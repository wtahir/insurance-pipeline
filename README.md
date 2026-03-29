# 🏛️ Insurance Document Intelligence Pipeline

An end-to-end AI system that **reads insurance claim PDFs**, **extracts structured data**, and lets you **ask questions in plain English** — even when the source documents are in German.

Built to demonstrate real-world challenges in document AI: multilingual processing, structured extraction with validation, semantic search, and automated quality evaluation.

---

## What It Does

```
  📄 PDF Claims        →   🔍 Read & Parse   →   🤖 Classify & Extract
  (German emails,           (text from every       (claim number, sender,
   invoices, letters)        page)                  urgency, date, type)

         ↓                       ↓                        ↓

  ✂️ Smart Chunking     →   📐 Vectorise      →   💬 Ask Questions
  (overlapping pieces        (multilingual          (English questions,
   that respect word          embeddings into         answers grounded
   boundaries)                ChromaDB)               in real documents)

         ↓

  📊 Auto-Evaluate
  (GPT-4o scores both
   retrieval & answer quality)
```

---

## Pipeline Stages

| # | Stage | What happens | Key tech |
|---|-------|-------------|----------|
| 1 | **Ingestion** | Reads PDFs, extracts text page-by-page, logs failures per page | pdfplumber |
| 2 | **Extraction** | Classifies document type, pulls structured fields, validates with schemas | GPT-4o + Pydantic |
| 3 | **Chunking** | Splits text into overlapping pieces (800 chars, 150 overlap) respecting sentences & word boundaries | Custom logic |
| 4 | **Embedding** | Converts chunks into vectors, stores with metadata for filtered search | Sentence Transformers + ChromaDB |
| 5 | **Retrieval** | Finds relevant chunks by meaning, generates a grounded English answer | ChromaDB + GPT-4o (RAG) |
| 6 | **Evaluation** | Scores retrieval quality and answer quality, identifies failure types | GPT-4o-as-Judge |

Each stage reads the previous stage's output and writes its own — you can rerun any single stage without starting over.

---

## Quick Start — Docker (recommended)

> **Prerequisites:** [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.
>
> **Note:** This project uses `docker-compose` (standalone). If you have the newer Docker Compose plugin, replace `docker-compose` with `docker compose` (no hyphen) in the commands below.

### 1. Clone & configure

```bash
git clone <your-repo-url>
cd insurance-pipeline
```

Create a `.env` file in the project root with your Azure OpenAI credentials:

```env
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### 2. Add your documents

Place PDF files in:

```
data/pdfs/
```

### 3. Build the image

```bash
docker-compose build
```

This creates a single `insurance-pipeline:latest` image used by every stage.

### 4. Run the full pipeline

```bash
docker-compose up
```

This runs **all 6 stages in order, automatically.** Each stage waits for the previous one to finish before starting. Results appear in `data/output/` and logs in `logs/` — both are shared with your machine through Docker volumes, so you can inspect them directly on your file system.

### 5. Run a single stage (optional)

To rerun just one stage (for example, extraction after fixing your `.env`):

```bash
docker-compose run --rm stage2
```

Replace `stage2` with any of `stage1` through `stage6`.

### 6. Stop & clean up

```bash
docker-compose down
```

---

## Run with Celery Workers (parallel processing)

For large batches, the Celery setup processes multiple documents **in parallel** using Redis as a message queue:

```bash
docker-compose -f docker-compose-celery.yaml up
```

This starts three containers:

| Container | Role |
|-----------|------|
| **redis** | Message queue between pipeline and workers |
| **worker** | Picks up documents and runs stages 1→4 per document (4 concurrent) |
| **pipeline** | Submits all PDFs from `data/pdfs/` to the queue |

---

## Run the Dashboard (demo UI)

A visual dashboard designed for live demos and non-technical stakeholders:

```bash
# Option A — locally (recommended for demos)
source venv/bin/activate
./run_dashboard.sh

# Option B — via Docker
docker-compose run --rm -p 8501:8501 stage1 \
  streamlit run ui/app.py --server.headless true
```

Then open **http://localhost:8501** in your browser.

**Dashboard pages:**

| Page | What you see |
|------|-------------|
| **Overview** | KPIs, architecture diagram, evaluation scores at a glance |
| **Pipeline Runner** | Execute stages with real-time progress bars |
| **Document Explorer** | Browse, search, and filter all documents with charts |
| **Query Interface** | Ask questions in English, see retrieved chunks + AI answer |
| **Evaluation Dashboard** | Retrieval vs answer quality charts, improvement suggestions |

---

## Run Locally (without Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then run stages in order:

```bash
python stage1_ingestion.py
python stage2_extraction.py
python stage3_chunking.py
python stage4_embedding.py
python stage5_retrieval.py
python stage6_evaluation.py
```

Outputs go to `data/output/`, logs to `logs/`.

---

## Project Structure

```
insurance-pipeline/
│
├── stage1_ingestion.py         # PDF → structured text
├── stage2_extraction.py        # Text → classified + extracted fields
├── stage3_chunking.py          # Full text → overlapping chunks
├── stage4_embedding.py         # Chunks → vectors in ChromaDB
├── stage5_retrieval.py         # Query → relevant chunks → GPT-4o answer
├── stage6_evaluation.py        # Score retrieval + answer quality
│
├── tasks.py                    # Celery task wrappers for parallel runs
├── celery_app.py               # Celery + Redis configuration
├── config.py                   # Paths and constants
│
├── ui/                         # Streamlit dashboard
│   ├── app.py                  # Main entry point
│   ├── pages/                  # Overview, Explorer, Query, Evaluation
│   └── components/             # Theme, widgets, helpers
│
├── Dockerfile                  # Single image for all stages
├── docker-compose.yml          # Sequential pipeline (stage1 → stage6)
├── docker-compose-celery.yaml  # Parallel pipeline (Redis + workers)
│
├── data/
│   ├── pdfs/                   # ← Put your input PDFs here
│   └── output/                 # Stage outputs (JSON)
├── logs/                       # Per-stage log files
└── chroma_db/                  # Vector store (persisted)
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Document parsing | pdfplumber |
| LLM | Azure OpenAI GPT-4o |
| Validation | Pydantic |
| Embeddings | Sentence Transformers (multilingual MiniLM) |
| Vector store | ChromaDB |
| Orchestration | Docker Compose / Celery + Redis |
| Dashboard | Streamlit + Plotly |
| Containerisation | Docker |

---

## How to Debug

### Check stage outputs

Each stage writes a summary file you can inspect immediately:

| Stage | Check this file |
|-------|----------------|
| 1 — Ingestion | `data/output/ingestion_summary.json` |
| 2 — Extraction | `data/output/extraction_summary.json` |
| 3 — Chunking | `data/output/chunking_summary.json` |
| 4 — Embedding | `data/output/embedding_summary.json` |
| 5 — Retrieval | `data/output/query_log.json` |
| 6 — Evaluation | `data/output/evaluation_summary.json` |

### Check logs

```bash
# On your host (volumes are shared)
tail -n 100 logs/extraction.log
tail -n 100 logs/embedding.log

# Inside a running Docker container
docker-compose logs stage2
```

### Common issues

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| No chunks produced (Stage 3) | Empty `original_content` in extracted data | Check `extracted_data.json` — rerun Stage 2 |
| 0 vectors stored (Stage 4) | `chunks.json` is empty | Rerun Stage 3, then Stage 4 |
| Retrieval returns nothing | ChromaDB collection is empty | Confirm Stage 4 completed; check `embedding_summary.json` |
| Azure OpenAI errors | Wrong key / endpoint / deployment | Re-check `.env` values |
| Dashboard won't start | Missing dependencies | `pip install -r requirements.txt` and activate venv |
| Docker stage fails | Missing `.env` or empty `data/pdfs/` | Add `.env` file and at least one PDF |
| Docker build fails | Network or pip issue | Run `docker-compose build --no-cache` |

### Rerun strategy

- **API key issue** → fix `.env`, rerun only Stage 2
- **Bad chunks** → rerun Stage 3, then Stage 4
- **Poor answers** → rerun Stage 5 with different queries, then Stage 6
- **Full reset** → delete `data/output/*`, `chroma_db/*`, and rerun from Stage 1
- Use the **dashboard** to inspect data quality before doing a full re-run

---

## What I Learned

I hit some bugs while creating this pipeline. I found out that because of the overlap calculation used, the character positions could land mid-word, so I added a word boundary search using `text.find(' ')` after calculating the new start position. There was an issue in formatting prompt using `.format` method. It's simpler and bug-free to keep the prompt as-is and use it later on by calling it directly in a method. I also experienced the token limitation error which can happen if the LLM call generates an answer needing more tokens than the defined limit.
