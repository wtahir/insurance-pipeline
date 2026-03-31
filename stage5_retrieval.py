# stage5_retrieval.py
# Input: ChromaDB collection (from Stage 4) + user query
# Output: data/output/query_log.json (every query and answer logged)
#
# This stage has two responsibilities:
# 1. Retrieve relevant chunks from ChromaDB based on a query
# 2. Generate an answer using GPT-4o with retrieved chunks as context
# Every query and its result is logged — this feeds directly into Stage 6 evaluation.

import os
import json
import logging
from datetime import datetime
from openai import AzureOpenAI
import chromadb
from chromadb.utils import embedding_functions
from config import INGESTED_DATA, OUTPUT_FOLDER
from dotenv import load_dotenv

load_dotenv()

os.makedirs("logs", exist_ok=True)
os.makedirs("data/output", exist_ok=True)

logging.basicConfig(
    filename="logs/retrieval.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Clients ---
azure_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-08-01-preview"
)
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

chroma_client = chromadb.PersistentClient(path="chroma_db")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
collection = chroma_client.get_collection(
    name="insurance_claims",
    embedding_function=embedding_fn
)

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

QUERY_LOG_PATH = "data/output/query_log.json"


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
    n_results: int = 5
) -> list[dict]:
    """
    Retrieves semantically similar chunks from ChromaDB.

    metadata_filter uses ChromaDB's 'where' syntax.
    Examples:
        {"urgency": "high"}
        {"claim_number": "2025 1033831"}
        {"$and": [{"urgency": "high"}, {"date": "2025-02-17"}]}

    Why n_results=5 as default? Enough context for a focused answer
    without overloading the prompt with irrelevant chunks.
    More chunks = more tokens = higher cost and more noise.
    """
    query_params = {
        "query_texts": [search_text],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"]
        # distances tells us how similar each chunk is — lower = more similar
        # We use this in Stage 6 to understand retrieval quality
    }

    if metadata_filter:
        query_params["where"] = metadata_filter

    results = collection.query(**query_params)

    # Restructure ChromaDB's nested response into a flat list of chunk dicts
    # ChromaDB returns results[0] because it supports batch queries —
    # we always send one query at a time so we always take index [0]
    chunks = []
    for doc, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text": doc,
            "metadata": metadata,
            "distance": round(distance, 4)
            # distance is cosine distance — 0.0 = identical, 2.0 = opposite
            # typical good matches are between 0.1 and 0.5
        })

    return chunks


def build_context(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a context block for the GPT-4o prompt.
    Each chunk is labeled with its source so the model can reference it.
    """
    context_parts = []
    for i, chunk in enumerate(chunks):
        meta = chunk["metadata"]
        context_parts.append(
            f"[Chunk {i+1} | File: {meta.get('file_name')} | "
            f"Claim: {meta.get('claim_number')} | "
            f"Date: {meta.get('date')} | "
            f"Distance: {chunk['distance']}]\n"
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
            {"role": "user", "content": user_message}
        ],
        max_completion_tokens=1000
    )

    return response.choices[0].message.content.strip()


def query_pipeline(
    query: str,
    metadata_filter: dict | None = None,
    n_results: int = 5
) -> dict:
    """
    Full RAG pipeline for a single query:
    retrieve → build context → generate answer → log everything

    Returns a result dict containing the answer and all supporting data.
    Logging every query here is what makes Stage 6 possible —
    you can't evaluate what you haven't recorded.
    """
    logging.info(f"Query: {query} | Filter: {metadata_filter} | n_results: {n_results}")

    # Step 1: Retrieve
    chunks = retrieve_chunks(query, metadata_filter, n_results)

    if not chunks:
        answer = "No relevant documents found for this query."
        logging.warning(f"No chunks retrieved for query: {query}")
    else:
        # Step 2: Build context
        context = build_context(chunks)

        # Step 3: Generate
        answer = generate_answer(query, context)

    # Step 4: Build result record
    result = {
        "query_id": f"q_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "query": query,
        "metadata_filter": metadata_filter,
        "n_results_requested": n_results,
        "chunks_retrieved": len(chunks),
        "chunks": chunks,
        "answer": answer,
        "queried_at": datetime.now().isoformat(),
        "evaluated": False,      # Stage 6 will flip this to True after scoring
        "score": None,           # Stage 6 will populate this
        "evaluation_notes": None # Stage 6 will populate this
    }

    # Step 5: Append to log
    log = load_query_log()
    log.append(result)
    save_query_log(log)

    logging.info(f"Query answered. chunks_retrieved={len(chunks)}, query_id={result['query_id']}")

    return result


def run_test_queries():
    """
    Runs a set of test queries to verify the pipeline works end to end.
    These are the kinds of questions a real insurance analyst would ask.
    Modify these to match your actual data.
    """
    test_queries = [
        {
            "query": "What documents are missing from water damage claims?",
            "filter": None
        },
        {
            "query": "Which claims require urgent attention?",
            "filter": {"urgency": "high"}
        },
        {
            "query": "What actions are required by the policyholder?",
            "filter": None
        },
        {
            "query": "Show me claims where an invoice was mentioned",
            "filter": None
        },
        {
            "query": "What types of damage are most common?",
            "filter": None
        }
    ]

    print("Running test queries...\n")

    for i, test in enumerate(test_queries):
        print(f"Query {i+1}: {test['query']}")
        if test['filter']:
            print(f"Filter: {test['filter']}")

        result = query_pipeline(
            query=test['query'],
            metadata_filter=test['filter'],
            n_results=5
        )

        print(f"Answer: {result['answer'][:400]}...")
        print(f"Chunks retrieved: {result['chunks_retrieved']}")
        print(f"Avg distance: {round(sum(c['distance'] for c in result['chunks']) / len(result['chunks']), 3) if result['chunks'] else 'N/A'}")
        print(f"Query ID: {result['query_id']}")
        print("-" * 60 + "\n")

    print(f"Done. {len(test_queries)} queries logged to {QUERY_LOG_PATH}")


if __name__ == "__main__":
    run_test_queries()