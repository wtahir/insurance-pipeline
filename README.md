This project is about creating an end to end pipeline to extract and process insurance information. I am building it to get to know the challenges while using latest state of the art tech.

## The pipeline consists of the following steps:
 
1. Ingestion: This takes the pdfs as input and performs processing to convert data in structured format for the next steps. It creates jsons with text stored as a dict and additional keys for useful information.

2. Extraction: Takes the jsons created in step 1 and extracts information such as claim number, document type etc.

3. Chunking: Now that the data has the useful information in json format, chunking step chunks it into a fixed chunk size of 800 with minimum chunk size of 100. There is also a document threshold of 600 so that any document having less text should have a single chunk. Meanwhile the chunk size of 100 to avoid short less meaningful chunks. Chunking is done based on sentences with overlapping of few words and making sure that words dont split between chunks. It also contains meta data which is required to retrieve relevant chunks

4. Embedding: Converts chunking results into vectors and stores those in ChromaDB along with its metadata for retrieval in the later stage. Since the language is non English but the query is in English. The model used for embedding is capable of handling multiple languages.

5. Retrieval: Retrieve relevant chunks from Chroma based on user querry. Then generates an answer using GPT-4o using the context of the retrieved chunks.

6. Evaluation: Evaluate the relevancy of the chunks retrieved and generated answer

## What I learned:

I hit some bugs while creating this pipeline. I found out that because of the overlap calculation used, the character positions could land mid-word, so I added a word boundary search using text.find(' ') after calculating the new start position. There was an issue in formating prompt using .format method. Its simpler and bug free to keep prompt as it is and use it later on by calling it directly in a method. I also experienced the token limitation error which can happen if the LLM call generates an answer needing more tokens than the defined limit.

## How to run the pipeline

### 1) Setup environment

From the project root:

```bash
cd ~/projects/insurance-pipeline
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you already have `venv` created, just activate and install requirements.

### 2) Configure environment variables

Create or update `.env` in the project root with your Azure OpenAI settings:

```env
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### 3) Add input files

Place insurance PDFs in:

```text
data/pdfs/
```

### 4) Run all stages (manual sequence)

Run these in order:

```bash
python stage1_ingestion.py
python stage2_extraction.py
python stage3_chunking.py
python stage4_embedding.py
python stage5_retrieval.py
python stage6_evaluation.py
```

This writes outputs to `data/output/` and logs to `logs/`.

### 5) Run with the UI dashboard (recommended for demos)

```bash
./run_dashboard.sh
```

or:

```bash
streamlit run ui/app.py
```

Then open:

```text
http://localhost:8501
```

### 6) Optional: run Celery-based asynchronous processing

If you want queued/background processing with workers:

1. Start Redis.
2. Start Celery worker.
3. Submit jobs from `tasks.py` functions.

Typical worker command:

```bash
celery -A celery_app.app worker --loglevel=info
```

## How to debug

### Quick health checks

Check expected outputs exist after each stage:

- Stage 1: `data/output/ingested_data.json`, `data/output/ingestion_summary.json`
- Stage 2: `data/output/extracted_data.json`, `data/output/extraction_summary.json`
- Stage 3: `data/output/chunks.json`, `data/output/chunking_summary.json`
- Stage 4: `data/output/embedding_summary.json` and `chroma_db/` populated
- Stage 5: `data/output/query_log.json`
- Stage 6: `data/output/evaluation_report.json`, `data/output/evaluation_summary.json`

### Log files to inspect

Each stage writes logs in `logs/`:

- `logs/ingestion.log`
- `logs/extraction.log`
- `logs/chunking.log`
- `logs/embedding.log`
- `logs/retrieval.log`
- `logs/evaluation.log`
- `logs/celery_pipeline.log`

Use:

```bash
tail -n 100 logs/extraction.log
tail -n 100 logs/embedding.log
```

### Common issues and fixes

1. **No chunks produced in Stage 3**
	- Confirm Stage 2 produced successful records in `extracted_data.json`.
	- Check that documents contain `original_content` and are not empty.
	- Inspect `logs/chunking.log` for skipped/empty content warnings.

2. **Embedding stores 0 vectors / batch failures**
	- Confirm `data/output/chunks.json` is not empty.
	- Verify sentence-transformers dependencies are installed.
	- Check `logs/embedding.log` for batch error messages.

3. **Retrieval returns no results**
	- Confirm Stage 4 completed and collection has vectors.
	- Verify Chroma path `chroma_db` exists and is readable.
	- Try broader queries first (without metadata filters).

4. **Azure OpenAI errors (Stage 2/5/6)**
	- Re-check `.env` keys and endpoint/deployment names.
	- Ensure deployment supports chat completions.
	- Check rate limits and retry after a short delay.

5. **Dashboard does not start**
	- Activate `venv` first.
	- Install UI dependencies: `pip install -r requirements.txt`.
	- Run: `python -m streamlit run ui/app.py`.

### Useful debug commands

From project root:

```bash
# Validate JSON outputs quickly
python -m json.tool data/output/extraction_summary.json > /dev/null && echo "extraction_summary.json OK"

# Check how many chunks were generated
python - << 'PY'
import json
with open('data/output/chunks.json', 'r', encoding='utf-8') as f:
	 chunks = json.load(f)
print('chunks:', len(chunks))
PY

# Check number of query records
python - << 'PY'
import json
with open('data/output/query_log.json', 'r', encoding='utf-8') as f:
	 q = json.load(f)
print('queries:', len(q))
PY
```

### Re-run strategy during debugging

- If Stage 2 fails for API reasons, fix `.env` and rerun Stage 2 only.
- If Stage 3 or 4 outputs look wrong, rerun Stage 3 then Stage 4.
- If retrieval quality is poor, rerun Stage 5 with different queries/filters, then Stage 6.
- Use the dashboard to inspect data quality before running full end-to-end again.
