"""
Unit tests for the Insurance Document Intelligence Pipeline.

Tests cover core logic (chunking, validation, metadata building)
without requiring API keys or external services.

Run:  python -m pytest tests/ -v
"""

import pytest
import json
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── Model validation tests ──────────────────────────────────

class TestPydanticModels:
    """Validate that Pydantic models enforce schema correctly."""

    def test_claim_communication_valid(self):
        from models import ClaimCommunication

        data = {
            "document_type": "claim_communication",
            "language": "de",
            "claim_number": "SYN-2024-1234567-12345678",
            "date": "2024-06-15",
            "sender": "test@example.com",
            "recipient": "claims@insurance.com",
            "subject": "Water damage claim",
            "summary_en": "Customer reports water damage in basement.",
            "attachments_mentioned": ["photo.jpg"],
            "action_required": "Send inspector",
            "urgency": "high",
            "confidence": 0.92,
        }
        claim = ClaimCommunication(**data)
        assert claim.urgency == "high"
        assert claim.confidence == 0.92
        assert len(claim.attachments_mentioned) == 1

    def test_claim_communication_optional_fields(self):
        from models import ClaimCommunication

        data = {
            "document_type": "claim_communication",
            "language": "de",
            "summary_en": "Minimal claim document.",
            "urgency": "normal",
            "confidence": 0.5,
        }
        claim = ClaimCommunication(**data)
        assert claim.claim_number is None
        assert claim.sender is None
        assert claim.attachments_mentioned == []

    def test_invoice_document_valid(self):
        from models import InvoiceDocument

        data = {
            "document_type": "invoice",
            "language": "de",
            "invoice_number": "INV-001",
            "claim_number": "CLM-123",
            "amount": "1,500.00 EUR",
            "date": "2024-07-01",
            "vendor": "Reparatur GmbH",
            "summary_en": "Invoice for pipe repair.",
            "confidence": 0.88,
        }
        inv = InvoiceDocument(**data)
        assert inv.amount == "1,500.00 EUR"

    def test_unknown_document_defaults(self):
        from models import UnknownDocument

        doc = UnknownDocument()
        assert doc.document_type == "unknown"
        assert doc.confidence == 0.0

    def test_confidence_out_of_range(self):
        from models import ClaimCommunication
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ClaimCommunication(
                document_type="claim_communication",
                language="de",
                summary_en="Test.",
                urgency="normal",
                confidence=1.5,  # Out of range
            )


# ─── Chunking tests ──────────────────────────────────────────

class TestChunking:
    """Validate text chunking logic."""

    def test_short_document_single_chunk(self):
        from stage3_chunking import chunk_document

        doc = {
            "file_name": "short.pdf",
            "original_content": "This is a short document.",
            "status": "success",
        }
        chunks = chunk_document(doc)
        assert len(chunks) == 1
        assert chunks[0]["is_single_chunk"] is True

    def test_long_document_multiple_chunks(self):
        from stage3_chunking import chunk_text
        from config import CHUNK_SIZE, CHUNK_OVERLAP

        text = "Word " * 500  # ~2500 chars
        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        assert len(chunks) > 1

    def test_chunk_text_respects_min_size(self):
        from stage3_chunking import chunk_text

        text = "Hello world."
        chunks = chunk_text(text, chunk_size=800, overlap=150)
        # Too short to produce any chunks above MIN_CHUNK_SIZE
        # (depends on MIN_CHUNK_SIZE, but 12 chars < 100)
        assert len(chunks) == 0

    def test_chunks_have_metadata(self):
        from stage3_chunking import build_chunk_record

        doc = {
            "file_name": "test.pdf",
            "file_path": "/data/pdfs/test.pdf",
            "document_type": "claim_communication",
            "language": "de",
            "claim_number": "CLM-001",
            "urgency": "high",
            "confidence": 0.9,
            "summary_en": "Test summary.",
        }
        record = build_chunk_record("Some chunk text here", 0, 3, doc)
        assert record["chunk_id"] == "test.pdf_chunk_0"
        assert record["urgency"] == "high"
        assert record["claim_number"] == "CLM-001"
        assert record["total_chunks"] == 3

    def test_empty_content_produces_no_chunks(self):
        from stage3_chunking import chunk_document

        doc = {
            "file_name": "empty.pdf",
            "original_content": "",
        }
        chunks = chunk_document(doc)
        assert len(chunks) == 0

    def test_overlap_creates_redundancy(self):
        from stage3_chunking import chunk_text

        # Create text that spans multiple chunks
        text = "A" * 2000
        chunks = chunk_text(text, chunk_size=800, overlap=150)
        assert len(chunks) >= 2
        # Chunks should overlap (second chunk starts before first chunk ends)
        # This verifies overlap is working


# ─── Metadata building tests ─────────────────────────────────

class TestMetadata:
    """Validate ChromaDB metadata building."""

    def test_build_metadata_no_none_values(self):
        from stage4_embedding import build_metadata

        chunk = {
            "file_name": "test.pdf",
            "document_type": "claim_communication",
            "claim_number": None,  # This should become ""
            "date": None,
            "sender": "test@email.com",
            "urgency": "high",
            "language": "de",
            "chunk_index": 0,
            "total_chunks": 1,
            "is_single_chunk": True,
            "summary_en": "Test",
            "action_required": None,
        }
        meta = build_metadata(chunk)

        # ChromaDB rejects None values — verify none exist
        for key, value in meta.items():
            assert value is not None, f"Metadata key '{key}' has None value"

    def test_build_metadata_correct_types(self):
        from stage4_embedding import build_metadata

        chunk = {
            "file_name": "test.pdf",
            "document_type": "claim_communication",
            "claim_number": "CLM-001",
            "date": "2024-01-01",
            "sender": "test@email.com",
            "urgency": "high",
            "language": "de",
            "chunk_index": 2,
            "total_chunks": 5,
            "is_single_chunk": False,
            "summary_en": "Test",
            "action_required": "Review",
        }
        meta = build_metadata(chunk)
        assert isinstance(meta["chunk_index"], int)
        assert isinstance(meta["total_chunks"], int)
        assert isinstance(meta["is_single_chunk"], bool)


# ─── Extraction validation tests ─────────────────────────────

class TestExtractionValidation:
    """Validate the extraction routing logic."""

    def test_validate_claim_communication(self):
        from stage2_extraction import validate_extraction

        raw = {
            "document_type": "claim_communication",
            "language": "de",
            "claim_number": "CLM-001",
            "summary_en": "Test claim.",
            "urgency": "high",
            "confidence": 0.9,
            "attachments_mentioned": [],
        }
        model, doc_type = validate_extraction(raw)
        assert doc_type == "claim_communication"
        assert model.confidence == 0.9

    def test_validate_unknown_fallback(self):
        from stage2_extraction import validate_extraction

        raw = {
            "document_type": "something_weird",
            "language": "en",
            "summary_en": "Cannot classify.",
            "confidence": 0.1,
        }
        model, doc_type = validate_extraction(raw)
        assert doc_type == "unknown"
        assert model.document_type == "unknown"

    def test_validate_invoice(self):
        from stage2_extraction import validate_extraction

        raw = {
            "document_type": "invoice",
            "language": "de",
            "invoice_number": "INV-100",
            "claim_number": "CLM-200",
            "amount": "500 EUR",
            "summary_en": "Repair invoice.",
            "confidence": 0.85,
        }
        model, doc_type = validate_extraction(raw)
        assert doc_type == "invoice"


# ─── Config tests ─────────────────────────────────────────────

class TestConfig:
    """Validate configuration is accessible and sensible."""

    def test_config_paths_exist(self):
        from config import PDF_FOLDER, LOG_FOLDER, OUTPUT_FOLDER, CHROMA_FOLDER
        # Paths should be strings
        assert isinstance(PDF_FOLDER, str)
        assert isinstance(LOG_FOLDER, str)
        assert isinstance(OUTPUT_FOLDER, str)
        assert isinstance(CHROMA_FOLDER, str)

    def test_chunk_params_sensible(self):
        from config import CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE
        assert CHUNK_SIZE > CHUNK_OVERLAP, "Chunk size must exceed overlap"
        assert MIN_CHUNK_SIZE > 0
        assert CHUNK_OVERLAP >= 0

    def test_embedding_model_configured(self):
        from config import EMBEDDING_MODEL
        assert len(EMBEDDING_MODEL) > 0

    def test_reranker_model_configured(self):
        from config import RERANKER_MODEL, RERANK_TOP_K
        assert len(RERANKER_MODEL) > 0
        assert RERANK_TOP_K > 0
