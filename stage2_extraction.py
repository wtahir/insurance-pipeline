# ingested_data.json (89 documents)
#         ↓
# For each document:
#     → Classify: what type is this? (claim communication, policy, invoice, other)
#     → Extract: pull structured fields based on the type
#     → Validate: does the output have the minimum required fields?
#     → Save: structured record ready for Stage 3

# stage2_extraction.py
# This stage classifies each document and extracts structured fields.
# Input: data/output/ingested_data.json (from Stage 1)
# Output: data/output/extracted_data.json (structured records)
#         data/output/extraction_summary.json (pipeline health report)

import os
import json
import logging
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ValidationError
from openai import AzureOpenAI
from dotenv import load_dotenv
from config import INGESTED_DATA, OUTPUT_FOLDER

load_dotenv()

os.makedirs("logs", exist_ok=True)
os.makedirs("data/output", exist_ok=True)

logging.basicConfig(
    filename="logs/extraction.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Azure OpenAI client ---
# Reads credentials from your .env file, never hardcoded
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-08-01-preview"
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

# --- Pydantic models ---
# These define exactly what a valid extraction result looks like.
# If the LLM returns something missing or with wrong types, Pydantic catches it here
# rather than letting bad data silently flow into Stage 3.

class ClaimCommunication(BaseModel):
    document_type: str                        # always "claim_communication"
    language: str                             # "de", "en", etc.
    claim_number: Optional[str]               # Optional because it might be missing
    date: Optional[str]                       # ISO format preferred
    sender: Optional[str]
    recipient: Optional[str]
    subject: Optional[str]
    summary_en: str                           # English summary — always required
    attachments_mentioned: list[str]          # Empty list if none
    action_required: Optional[str]            # What needs to happen next
    urgency: str                              # "low", "normal", "high"
    confidence: float                         # 0.0 to 1.0 — how confident is the LLM


class PolicyDocument(BaseModel):
    # This schema is ready for when you add policy documents later.
    # Stage 2 will route to this automatically based on classification.
    document_type: str                        # always "policy_document"
    language: str
    policy_number: Optional[str]
    policyholder_name: Optional[str]
    coverage_type: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    premium_amount: Optional[str]
    summary_en: str
    confidence: float


class UnknownDocument(BaseModel):
    # Fallback for anything that doesn't fit known types
    document_type: str                        # always "unknown"
    language: str
    summary_en: str
    confidence: float


# --- Prompt ---
# The prompt is the most important part of this stage.
# It tells the LLM exactly what to do and what format to return.
# Small changes here have large effects on output quality.

EXTRACTION_PROMPT = """You are an insurance document analyst. You will receive text from an insurance document.

Your tasks:
1. Classify the document type. Choose from: claim_communication, policy_document, invoice, unknown
2. Detect the language (use ISO 639-1 codes: "de" for German, "en" for English, etc.)
3. Extract the relevant structured fields based on document type
4. Write a concise English summary (2-3 sentences) regardless of the document's original language
5. Estimate your confidence in the extraction from 0.0 to 1.0

IMPORTANT: Respond ONLY with a valid JSON object. No explanation, no markdown, no code fences.
If a field cannot be found, use null. Never omit a field entirely.

For claim_communication, return exactly this structure:
{
  "document_type": "claim_communication",
  "language": "<detected language>",
  "claim_number": "<claim number or null>",
  "date": "<date in YYYY-MM-DD format or null>",
  "sender": "<sender email or name or null>",
  "recipient": "<recipient or null>",
  "subject": "<subject or null>",
  "summary_en": "<english summary>",
  "attachments_mentioned": ["<attachment1>", "<attachment2>"],
  "action_required": "<what needs to happen next or null>",
  "urgency": "<low|normal|high>",
  "confidence": <0.0 to 1.0>
}

For policy_document, return exactly this structure:
{
  "document_type": "policy_document",
  "language": "<detected language>",
  "policy_number": "<policy number or null>",
  "policyholder_name": "<name or null>",
  "coverage_type": "<type of coverage or null>",
  "start_date": "<YYYY-MM-DD or null>",
  "end_date": "<YYYY-MM-DD or null>",
  "premium_amount": "<amount with currency or null>",
  "summary_en": "<english summary>",
  "confidence": <0.0 to 1.0>
}

For unknown, return:
{
  "document_type": "unknown",
  "language": "<detected language>",
  "summary_en": "<english summary>",
  "confidence": <0.0 to 1.0>
}

Document text:
"""


def truncate_text(text: str, max_chars: int = 1500) -> str:
    """
    Takes only the first max_chars characters for classification.
    Why 1500? Enough to identify document type and extract header fields.
    Sending full documents wastes tokens — the claim number and sender
    are always in the first few lines of an email.
    """
    return text[:max_chars] if len(text) > max_chars else text


def validate_extraction(raw: dict) -> tuple[BaseModel, str]:
    """
    Routes the raw LLM output to the correct Pydantic model based on document_type.
    Returns a validated model instance and the document type string.
    Raises ValidationError if fields are missing or wrong type.
    
    Why this matters: without validation, a missing 'claim_number' field
    would only cause a crash in Stage 5 when you try to display it.
    Better to catch it here, immediately, with a clear error message.
    """
    doc_type = raw.get("document_type", "unknown")

    if doc_type == "claim_communication":
        return ClaimCommunication(**raw), doc_type
    elif doc_type == "policy_document":
        return PolicyDocument(**raw), doc_type
    else:
        return UnknownDocument(
            document_type="unknown",
            language=raw.get("language", "unknown"),
            summary_en=raw.get("summary_en", "Could not summarize."),
            confidence=raw.get("confidence", 0.0)
        ), "unknown"


def extract_document(document: dict) -> dict:
    """
    Processes a single document through the LLM.
    Returns a result dict with status, extracted fields, and metadata.
    Never crashes — failures are captured and returned as failed records.
    """
    file_name = document.get("file_name", "unknown")
    content = document.get("content", "")

    if not content.strip():
        logging.warning(f"Empty content for {file_name}, skipping LLM call.")
        return {
            "file_name": file_name,
            "status": "skipped",
            "reason": "empty content",
            "extracted_at": datetime.now().isoformat()
        }

    truncated = truncate_text(content, max_chars=1500)
    prompt = EXTRACTION_PROMPT + "\n" + truncated

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=1000
        )

        raw_text = response.choices[0].message.content.strip()

        # Parse JSON — if LLM ignored instructions and added markdown fences, strip them
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        
        raw_dict = json.loads(raw_text)

        validated, doc_type = validate_extraction(raw_dict)

        logging.info(f"OK: {file_name} → {doc_type} (confidence: {validated.confidence})")

        return {
            "file_name": file_name,
            "file_path": document.get("file_path"),
            "original_content": content,      # Keep full original for Stage 3 chunking
            "total_pages": document.get("total_pages"),
            "failed_pages": document.get("failed_pages", []),
            "status": "success",
            "extracted_at": datetime.now().isoformat(),
            **validated.model_dump()          # Unpack all validated fields into this dict
        }

    except json.JSONDecodeError as e:
        logging.error(f"JSON parse failed for {file_name}: {e} | Raw: {raw_text[:200]}")
        return {"file_name": file_name, "status": "failed", "reason": f"json_parse_error: {e}"}

    except ValidationError as e:
        logging.error(f"Validation failed for {file_name}: {e}")
        return {"file_name": file_name, "status": "failed", "reason": f"validation_error: {str(e)}"}

    except Exception as e:
        logging.error(f"Unexpected error for {file_name}: {e}")
        return {"file_name": file_name, "status": "failed", "reason": str(e)}


def extract_all():
    input_path = INGESTED_DATA

    if not os.path.exists(input_path):
        raise FileNotFoundError("ingested_data.json not found. Run Stage 1 first.")

    with open(input_path, "r") as f:
        documents = json.load(f)

    logging.info(f"Starting extraction for {len(documents)} documents.")
    print(f"Processing {len(documents)} documents...")

    results = []
    successful, failed, skipped = 0, 0, 0

    # Load already successful results if they exist, to avoid reprocessing
    existing_results = {}
    output_path = "data/output/extracted_data.json"
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            for r in json.load(f):
                if r.get("status") == "success":
                    existing_results[r["file_name"]] = r

    for i, doc in enumerate(documents):
        file_name = doc.get("file_name")
        
        # Skip if already successfully processed
        if file_name in existing_results:
            results.append(existing_results[file_name])
            successful += 1
            print(f"  [{i+1}/{len(documents)}] {file_name} — already done, skipping")
            continue

        print(f"  [{i+1}/{len(documents)}] {file_name}", end=" ")
        result = extract_document(doc)
        results.append(result)

        status = result.get("status")
        if status == "success":
            successful += 1
            print(f"✓ {result.get('document_type')} (conf: {result.get('confidence')})")
        elif status == "skipped":
            skipped += 1
            print("— skipped (empty)")
        else:
            failed += 1
            print(f"✗ failed: {result.get('reason', '')[:60]}")

    # Save full results for Stage 3
    with open("data/output/extracted_data.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)  # ensure_ascii=False preserves German characters

    # Save summary
    doc_type_counts = {}
    for r in results:
        if r.get("status") == "success":
            t = r.get("document_type", "unknown")
            doc_type_counts[t] = doc_type_counts.get(t, 0) + 1

    summary = {
        "run_at": datetime.now().isoformat(),
        "total_documents": len(documents),
        "successful": successful,
        "failed": failed,
        "skipped": skipped,
        "document_types_found": doc_type_counts
    }

    with open("data/output/extraction_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logging.info(f"Extraction complete. {successful} success, {failed} failed, {skipped} skipped.")
    print(f"\nDone. {successful} succeeded, {failed} failed, {skipped} skipped.")
    print(f"Document types found: {doc_type_counts}")


if __name__ == "__main__":
    extract_all()

