# stage4_embedding.py
# Input: data/output/chunks.json (from Stage 3)
# Output: ChromaDB collection stored in chroma_db/ folder
#         data/output/embedding_summary.json
#
# This stage converts text chunks into vector embeddings and stores them
# in ChromaDB with metadata. After this stage your documents are
# semantically searchable — similar meaning finds similar chunks
# even without exact keyword matches.

import os
import json
import logging
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
from config import CHUNKS_DATA, OUTPUT_FOLDER
from dotenv import load_dotenv

load_dotenv()

os.makedirs("logs", exist_ok=True)
os.makedirs("chroma_db", exist_ok=True)

logging.basicConfig(
    filename="logs/embedding.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Embedding model ---
# We use sentence-transformers running locally.
# "paraphrase-multilingual-MiniLM-L12-v2" is specifically designed for
# multilingual text — it understands German and English in the same
# vector space. This means a German chunk and an English query can
# still match if they mean the same thing.
# It runs on your CPU, no API cost, no internet needed after first download.
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# --- ChromaDB setup ---
# PersistentClient saves to disk — your vectors survive between runs.
# If you used Client() instead, everything would be lost on restart.
chroma_client = chromadb.PersistentClient(path="chroma_db")

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)

# Collection is like a table in ChromaDB.
# get_or_create means: use existing collection if it exists, create if not.
# This makes the stage safely rerunnable.
collection = chroma_client.get_or_create_collection(
    name="insurance_claims",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}  # cosine similarity — standard for text
)

# Batch size for ChromaDB upserts.
# Why batch? Sending 549 individual inserts is slow.
# Sending one batch of 549 is fast.
# 100 is a safe batch size that works well for ChromaDB.
BATCH_SIZE = 100


def build_metadata(chunk: dict) -> dict:
    """
    Extracts only the filterable/useful metadata fields for ChromaDB.
    ChromaDB metadata values must be str, int, float, or bool — not None.
    We convert None to empty string to avoid storage errors.

    Why not store everything? ChromaDB metadata is not compressed —
    storing large fields like original_content in metadata bloats the index.
    The full chunk text is stored separately as the document field.
    """
    def safe(value) -> str:
        # ChromaDB rejects None values in metadata — convert to empty string
        return str(value) if value is not None else ""

    return {
        "file_name": safe(chunk.get("file_name")),
        "document_type": safe(chunk.get("document_type")),
        "claim_number": safe(chunk.get("claim_number")),
        "date": safe(chunk.get("date")),
        "sender": safe(chunk.get("sender")),
        "urgency": safe(chunk.get("urgency")),
        "language": safe(chunk.get("language")),
        "chunk_index": int(chunk.get("chunk_index", 0)),
        "total_chunks": int(chunk.get("total_chunks", 1)),
        "is_single_chunk": bool(chunk.get("is_single_chunk", False)),
        "summary_en": safe(chunk.get("summary_en")),
        "action_required": safe(chunk.get("action_required")),
    }


def embed_and_store(chunks: list[dict]):
    """
    Embeds chunks in batches and upserts into ChromaDB.
    Uses upsert instead of add — if a chunk_id already exists
    it gets updated rather than causing a duplicate error.
    This makes the stage safely rerunnable without clearing the DB first.
    """
    total = len(chunks)
    stored = 0
    failed = 0

    for batch_start in range(0, total, BATCH_SIZE):
        batch = chunks[batch_start: batch_start + BATCH_SIZE]
        batch_num = (batch_start // BATCH_SIZE) + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} chunks)...", end=" ")

        try:
            ids = [chunk["chunk_id"] for chunk in batch]
            documents = [chunk["text"] for chunk in batch]
            metadatas = [build_metadata(chunk) for chunk in batch]

            # upsert embeds the documents using embedding_fn automatically
            # then stores vector + metadata + id together
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

            stored += len(batch)
            print(f"✓")
            logging.info(f"Batch {batch_num}/{total_batches} stored ({len(batch)} chunks)")

        except Exception as e:
            failed += len(batch)
            print(f"✗ failed: {e}")
            logging.error(f"Batch {batch_num} failed: {e}")

    return stored, failed


def embed_all():
    input_path = CHUNKS_DATA

    if not os.path.exists(input_path):
        raise FileNotFoundError("chunks.json not found. Run Stage 3 first.")

    with open(input_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Embedding {len(chunks)} chunks into ChromaDB...")
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Collection: insurance_claims\n")

    # Check how many chunks are already in the collection
    existing_count = collection.count()
    if existing_count > 0:
        print(f"Note: collection already contains {existing_count} vectors — upserting (existing chunks will be updated)\n")

    start_time = datetime.now()
    stored, failed = embed_and_store(chunks)
    duration = (datetime.now() - start_time).total_seconds()

    final_count = collection.count()

    summary = {
        "run_at": datetime.now().isoformat(),
        "embedding_model": EMBEDDING_MODEL,
        "chunks_processed": len(chunks),
        "chunks_stored": stored,
        "chunks_failed": failed,
        "total_vectors_in_collection": final_count,
        "duration_seconds": round(duration, 2),
        "chunks_per_second": round(len(chunks) / duration, 1) if duration > 0 else 0
    }

    with open("data/output/embedding_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logging.info(f"Embedding complete. {stored} stored, {failed} failed. Duration: {duration:.1f}s")
    print(f"\nDone. {stored} chunks stored, {failed} failed.")
    print(f"Total vectors in collection: {final_count}")
    print(f"Duration: {duration:.1f}s")


if __name__ == "__main__":
    embed_all()