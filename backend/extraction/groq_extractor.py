# backend/extraction/groq_extractor.py

import json
from .llm_client import call_llm_json
from .schemas import DocumentClaims


SYSTEM_PROMPT = """You are a document forensics assistant for a banking underwriting system.
Your job is to extract structured claims from financial and legal documents.
Be precise. Extract only what is explicitly stated in the document.
Do not infer or guess values that are not present.
If a field is not present in the document, set it to null.
Always respond with valid JSON only."""


def build_extraction_prompt(text: str) -> str:
    return f"""Extract all verifiable claims from the following document text.

Return a JSON object with exactly these fields:
{{
  "document_type": "financial_statement | land_record | bank_statement | legal_doc | unknown",
  "company_name": "string or null",
  "cin": "string or null — Company Identification Number",
  "gstin": "string or null — GST Identification Number",
  "pan": "string or null",
  "director_name": "string or null",
  "registered_address": "string or null — the SELLER or ISSUER company's own registered address only, NOT the buyer or client address",
  "declared_revenue": "number or null — in INR",
  "declared_revenue_period": "string or null — e.g. FY 2023-24",
  "property_id": "string or null",
  "owner_name": "string or null",
  "survey_number": "string or null",
  "registered_property_value": "number or null — in INR",
  "account_number": "string or null — bank account number",
  "account_holder": "string or null — full name of the account holder as printed on the statement",
  "utr": "string or null — UTR/transaction reference number (NEFT/RTGS/IMPS/UPI)",
  "bank_name": "string or null — short bank name or abbreviation e.g. SBIN, HDFC, ICICI",
  "opening_balance": "number or null — opening or closing balance in INR as printed on the statement",
  "extraction_confidence": "float between 0.0 and 1.0",
  "low_confidence_fields": ["list of field names where extraction was uncertain"],
  "notes": "string or null — note any anomalies, ambiguities, or suspicious patterns you noticed"
}}

DOCUMENT TEXT:
{text}"""


def extract_claims(ocr_text: str) -> DocumentClaims:
    """
    Takes raw OCR text, returns validated DocumentClaims object.
    """
    prompt = build_extraction_prompt(ocr_text)

    raw_dict = call_llm_json(prompt, system=SYSTEM_PROMPT)

    # Validate against Pydantic schema
    claims = DocumentClaims(**raw_dict)
    return claims


def extract_claims_dict(ocr_text: str) -> dict:
    """
    Same as extract_claims but returns dict for API response.
    """
    claims = extract_claims(ocr_text)
    return claims.model_dump()
