# backend/extraction/schemas.py

from pydantic import BaseModel, Field
from typing import Optional


class DocumentClaims(BaseModel):
    document_type: str = Field(
        description="Type: financial_statement | land_record | bank_statement | legal_doc | unknown"
    )
    company_name: Optional[str] = None
    cin: Optional[str] = Field(None, description="Company Identification Number")
    gstin: Optional[str] = Field(None, description="GST Identification Number")
    pan: Optional[str] = Field(None, description="PAN number")
    director_name: Optional[str] = None
    registered_address: Optional[str] = None
    declared_revenue: Optional[float] = Field(None, description="In INR")
    declared_revenue_period: Optional[str] = Field(None, description="e.g. FY 2023-24")
    property_id: Optional[str] = None
    owner_name: Optional[str] = None
    survey_number: Optional[str] = None
    registered_property_value: Optional[float] = None
    account_number: Optional[str] = None
    utr: Optional[str] = None
    account_holder: Optional[str] = None
    bank_name: Optional[str] = None
    opening_balance: Optional[float] = None
    extraction_confidence: float = Field(default=0.0,
        description="0.0 to 1.0 — how confident the extraction is overall"
    )
    low_confidence_fields: list[str] = Field(
        default=[],
        description="Fields where extraction was uncertain"
    )
    notes: Optional[str] = Field(
        None,
        description="Any anomalies or ambiguities noticed during extraction"
    )
