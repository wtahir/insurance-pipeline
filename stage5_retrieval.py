# stage5_retrieval.py
# Input: ChromaDB collection (from Stage 4) + user query
# Output: data/output/query_log.json (every query and answer logged)
#
# This stage has three responsibilities:
# 1. Retrieve relevant chunks from ChromaDB based on a query
# 2. Rerank results with a cross-encoder for precision (if enabled)
# 3. Generate an answer using GPT-4o with retrieved chunks as context
# Every query and its result is logged — this feeds directly into Stage 6 evaluation.

import os
import json
import logging
from datetime import datetime
from openai import AzureOpenAI
import chromadb
from chromadb.utils import embedding_functions
from config import (
    QUERY_LOG, OUTPUT_FOLDER, CHROMA_FOLDER, CHROMA_COLLECTION,
    EMBEDDING_MODEL, RERANKER_MODEL, RERANK_ENABLED, RERANK_TOP_K,
    DEFAULT_N_RESULTS, RETRIEVAL_OVER_FETCH,
    AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT, AZURE_API_VERSION,
    LOG_FOLDER, LOG_FORMAT,
)
from dotenv import load_dotenv

load_dotenv()

os.makedirs(LOG_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_FOLDER, "retrieval.log"),
    level=logging.INFO,
    format=LOG_FORMAT,
)

# --- Clients ---
azure_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_API_VERSION,
)
DEPLOYMENT_NAME = AZURE_OPENAI_DEPLOYMENT

# --- Lazy-loaded resources ---
_chroma_collection = None
_reranker = None


def _get_collection():
    """Lazy-load ChromaDB collection to avoid import-time side effects."""
    global _chroma_collection
    if _chroma_collection is None:
        client = chromadb.PersistentClient(path=CHROMA_FOLDER)
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        _chroma_collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            embedding_function=embedding_fn,
        )
    return _chroma_collection


def _get_reranker():
    """Lazy-load cross-encoder reranker model."""
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(RERANKER_MODEL)
        logging.info(f"Loaded reranker model: {RERANKER_MODEL}")
    return _reranker


# --- Prompt ---
# The system prompt tells GPT-4o its role and constraints.
# "Only use the provided context" is critical — without this instruction
# the model will hallucinate answers from its training data when
# it doesn't find relevant information in the chunks.
SYSTEM_PROMPT = """You are an insurance claims analyst assistant.
You answer questions based strictly on the provided context chunks from insurance claim documents.
The documents are in German but you must always answer in English.
If the context does not contain enough information to answer the question, say so clearly.
Never make up information that is not present in the context.
When referencing specific claims, always mention the claim number."""

QUERY_LOG_PATH = QUERY_LOG


def load_query_log() -> list:
    """
    Loads existing query log or returns empty list.
    Every query is appended to this log — Stage 6 reads it for evaluation.
    """
    if os.path.exists(QUERY_LOG_PATH):
        with open(QUERY_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_query_log(log: list):
    with open(QUERY_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def retrieve_chunks(
    search_text: str,
    metadata_filter: dict | None = None,
    n_results: int = DEFAULT_N_RESULTS,
) -> list[dict]:
    """
    Retrieves semantically similar chunks from ChromaDB.

    metadata_filter uses ChromaDB's 'where' syntax.
    Examples:
        {"urgency": "high"}
        {"claim_number": "2025 1033831"}
        {"$and": [{"urgency": "high"}, {"date": "2025-02-17"}]}

    When reranking is enabled, we over-fetch (RETRIEVAL_OVER_FETCH) candidates
    from the bi-encoder and then rerank with a cross-encoder for precision.
    """
    collection = _get_collection()

    # Over-fetch if reranking is enabled — the cross-encoder will select the best
    fetch_count = RETRIEVAL_OVER_FETCH if RERANK_ENABLED else n_results

    query_params = {
        "query_texts": [search_text],
        "n_results": fetch_count,
        "include": ["documents", "metadatas", "distances"],
    }

    if metadata_filter:
        query_params["where"] = metadata_filter

    results = collection.query(**query_params)

    # Restructure ChromaDB's nested response into a flat list of chunk dicts
    chunks = []
    for doc, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "metadata": metadata,
            "distance": round(distance, 4),
        })

    return chunks


def rerank_chunks(query: str, chunks: list[dict], top_k: int = RERANK_TOP_K) -> list[dict]:
    """
    Re-scores chunks using a cross-encoder model for higher precision.

    Bi-encoders (sentence-transformers) are fast but approximate —
    they encode query and document independently. Cross-encoders
    process (query, document) pairs together, producing more accurate
    relevance scores at the cost of speed.

    This two-stage retrieve-then-rerank pattern is standard in
    production RAG systems.
    """
    if not chunks:
        return chunks

    reranker = _get_reranker()

    # Build (query, chunk_text) pairs for the cross-encoder
    pairs = [(query, chunk["text"]) for chunk in chunks]
    scores = reranker.predict(pairs)

    # Attach cross-encoder score to each chunk
    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = round(float(score), 4)

    # Sort by cross-encoder score (higher = more relevant) and take top_k
    reranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)[:top_k]

    logging.info(
        f"Reranked {len(chunks)} → {len(reranked)} chunks. "
        f"Score range: {reranked[-1]['rerank_score']:.3f} – {reranked[0]['rerank_score']:.3f}"
    )

    return reranked


def build_context(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a context block for the GPT-4o prompt.
    Each chunk is labeled with its source so the model can reference it.
    """
    context_parts = []
    for i, chunk in enumerate(chunks):
        meta = chunk["metadata"]
        rerank_info = f" | Relevance: {chunk['rerank_score']:.3f}" if "rerank_score" in chunk else ""
        context_parts.append(
            f"[Chunk {i+1} | File: {meta.get('file_name')} | "
            f"Claim: {meta.get('claim_number')} | "
            f"Date: {meta.get('date')} | "
            f"Distance: {chunk['distance']}{rerank_info}]\n"
            f"{chunk['text']}"
        )
    return "\n\n---\n\n".join(context_parts)


def generate_answer(query: str, context: str) -> str:
    """
    Sends query + context to GPT-4o and returns the answer.
    Temperature=0 for consistent, deterministic answers.
    """
    user_message = f"""Context from insurance claim documents:

{context}

Question: {query}

Answer based only on the context above:"""

    response = azure_client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        max_completion_tokens=1000,
    )

    return response.choices[0].message.content.strip()


def query_pipeline(
    query: str,
    metadata_filter: dict | None = None,
    n_results: int = DEFAULT_N_RESULTS,
) -> dict:
    """
    Full RAG pipeline for a single query:
    retrieve → rerank (optional) → build context → generate answer → log everything

    Returns a result dict containing the answer and all supporting data.
    Logging every query here is what makes Stage 6 possible —
    you can't evaluate what you haven't recorded.
    """
    logging.info(f"Query: {query} | Filter: {metadata_filter} | n_results: {n_results}")

    # Step 1: Retrieve (bi-encoder)
    chunks = retrieve_chunks(query, metadata_filter, n_results)

    # Step 2: Rerank (cross-encoder) — if enabled
    if RERANK_ENABLED and chunks:
        chunks = rerank_chunks(query, chunks, top_k=n_results)

    if not chunks:
        answer = "No relevant documents found for this query."
        logging.warning(f"No chunks retrieved for query: {query}")
    else:
        # Step 3: Build context
        context = build_context(chunks)

        # Step 4: Generate
        answer = generate_answer(query, context)

    # Step 5: Build result record
    result = {
        "query_id": f"q_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "query": query,
        "metadata_filter": metadata_filter,
        "n_results_requested": n_results,
        "chunks_retrieved": len(chunks),
        "reranking_enabled": RERANK_ENABLED,
        "chunks": chunks,
        "answer": answer,
        "queried_at": datetime.now().isoformat(),
        "evaluated": False,
        "score": None,
        "evaluation_notes": None,
    }

    # Step 6: Append to log
    log = load_query_log()
    log.append(result)
    save_query_log(log)

    logging.info(f"Query answered. chunks_retrieved={len(chunks)}, query_id={result['query_id']}")

    return result


def run_test_queries():
    """
    Runs a set of test queries to verify the pipeline works end to end.
    These are the kinds of questions a real insurance analyst would ask.
    """
    test_queries = [
        {
            "query": "What documents are missing from water damage claims?",
            "filter": None,
        },
        {
            "query": "Which claims require urgent attention?",
            "filter": {"urgency": "high"},
        },
        {
            "query": "What actions are required by the policyholder?",
            "filter": None,
        },
        {
            "query": "Show me claims where an invoice was mentioned",
            "filter": None,
        },
        {
            "query": "What types of damage are most common?",
            "filter": None,
        },
    ]

    print(f"Running test queries (reranking: {'ON' if RERANK_ENABLED else 'OFF'})...\n")

    for i, test in enumerate(test_queries):
        print(f"Query {i+1}: {test['query']}")
        if test["filter"]:
            print(f"Filter: {test['filter']}")

        result = query_pipeline(
            query=test["query"],
            metadata_filter=test["filter"],
            n_results=DEFAULT_N_RESULTS,
        )

        print(f"Answer: {result['answer'][:400]}...")
        print(f"Chunks retrieved: {result['chunks_retrieved']}")
        avg_dist = (
            round(sum(c["distance"] for c in result["chunks"]) / len(result["chunks"]), 3)
            if result["chunks"] else "N/A"
        )
        print(f"Avg distance: {avg_dist}")
        if RERANK_ENABLED and result["chunks"] and "rerank_score" in result["chunks"][0]:
            avg_rerank = round(
                sum(c["rerank_score"] for c in result["chunks"]) / len(result["chunks"]), 3
            )
            print(f"Avg rerank score: {avg_rerank}")
        print(f"Query ID: {result['query_id']}")
        print("-" * 60 + "\n")

    print(f"Done. {len(test_queries)} queries logged to {QUERY_LOG_PATH}")


if __name__ == "__main__":
    run_test_queries()