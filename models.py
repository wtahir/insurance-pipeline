"""
Pydantic models for validated LLM extraction output.

Each model defines the exact schema expected from GPT-4o when classifying
and extracting insurance documents. Validation catches bad LLM output
immediately — before it silently corrupts downstream stages.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ClaimCommunication(BaseModel):
    """Schema for insurance claim communications (emails, letters)."""
    document_type: str = Field(default="claim_communication")
    language: str = Field(description="ISO 639-1 code, e.g. 'de', 'en'")
    claim_number: Optional[str] = None
    date: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    subject: Optional[str] = None
    summary_en: str = Field(description="English summary, 2-3 sentences")
    attachments_mentioned: list[str] = Field(default_factory=list)
    action_required: Optional[str] = None
    urgency: str = Field(default="normal", description="low | normal | high")
    confidence: float = Field(ge=0.0, le=1.0)


class PolicyDocument(BaseModel):
    """Schema for insurance policy documents."""
    document_type: str = Field(default="policy_document")
    language: str
    policy_number: Optional[str] = None
    policyholder_name: Optional[str] = None
    coverage_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    premium_amount: Optional[str] = None
    summary_en: str
    confidence: float = Field(ge=0.0, le=1.0)


class InvoiceDocument(BaseModel):
    """Schema for invoices related to claims."""
    document_type: str = Field(default="invoice")
    language: str
    invoice_number: Optional[str] = None
    claim_number: Optional[str] = None
    amount: Optional[str] = None
    date: Optional[str] = None
    vendor: Optional[str] = None
    summary_en: str
    confidence: float = Field(ge=0.0, le=1.0)


class UnknownDocument(BaseModel):
    """Fallback schema for unclassifiable documents."""
    document_type: str = Field(default="unknown")
    language: str = "unknown"
    summary_en: str = "Could not summarize."
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
