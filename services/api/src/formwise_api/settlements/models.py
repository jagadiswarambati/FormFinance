from datetime import datetime, date
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


SettlementStatus = Literal[
    "uploaded",      # Just ingested
    "processing",    # Extraction/verification running
    "verified",      # All deductions verified
    "flagged",       # Some deductions need review
    "escalated"      # High-risk, requires escalation
]

SettlementSource = Literal["razorpay", "stripe", "paypal", "other"]


class SettlementDeduction(BaseModel):
    """Individual deduction from a settlement (charge, fee, hold, refund, etc.)"""
    
    id: str = Field(default_factory=lambda: uuid4().hex)
    settlement_id: str = Field(alias="settlementId")
    type: Literal["chargeback", "fee", "hold", "refund", "other"]
    description: str
    amount: float  # In settlement currency
    reference_id: str | None = Field(default=None, alias="referenceId")
    reference_date: date | None = Field(default=None, alias="referenceDate")
    extracted_with_confidence: float = Field(default=0.9, ge=0, le=1, alias="extractedWithConfidence")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    
    model_config = ConfigDict(populate_by_name=True)


class Settlement(BaseModel):
    """A payment settlement statement (from Razorpay, Stripe, etc.)"""
    
    id: str = Field(default_factory=lambda: uuid4().hex)
    owner_uid: str = Field(alias="ownerUid")  # Firebase UID
    source: SettlementSource
    status: SettlementStatus = "uploaded"
    settlement_date: date = Field(alias="settlementDate")
    gross_amount: float = Field(alias="grossAmount")  # Total collected
    net_amount: float = Field(alias="netAmount")      # After deductions
    currency: str = "INR"
    
    # References to related documents
    deduction_ids: list[str] = Field(default_factory=list, alias="deductionIds")
    document_ids: list[str] = Field(default_factory=list, alias="documentIds")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    
    model_config = ConfigDict(populate_by_name=True)


class SettlementCreateRequest(BaseModel):
    """Request to create a settlement"""
    
    source: SettlementSource
    settlement_date: date = Field(alias="settlementDate")
    gross_amount: float = Field(alias="grossAmount")
    net_amount: float = Field(alias="netAmount")
    currency: str = "INR"
    
    model_config = ConfigDict(populate_by_name=True)


class SettlementResponse(BaseModel):
    """Response containing settlement data"""
    
    id: str
    owner_uid: str = Field(alias="ownerUid")
    source: SettlementSource
    status: SettlementStatus
    settlement_date: date = Field(alias="settlementDate")
    gross_amount: float = Field(alias="grossAmount")
    net_amount: float = Field(alias="netAmount")
    currency: str
    deduction_ids: list[str] = Field(alias="deductionIds")
    document_ids: list[str] = Field(alias="documentIds")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    
    model_config = ConfigDict(populate_by_name=True)
