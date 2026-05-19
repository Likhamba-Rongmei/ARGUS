# tests/test_extraction.py
# Run this to verify Groq + extraction is working before integrating

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from extraction.groq_extractor import extract_claims_dict

# Fake OCR text simulating a financial statement
SAMPLE_TEXT = """
HORIZON VENTURES PRIVATE LIMITED
Company Identification Number: U72900MH2019PTC999999
GSTIN: 27AABCH1234F1Z5
PAN: AABCH1234F
Registered Address: 401, Nariman Point, Mumbai, Maharashtra - 400021
Director: Rajesh Kumar

Annual Financial Statement — FY 2023-24
Total Revenue: Rs. 42,00,000
Net Profit: Rs. 8,50,000

Certified by: CA Priya Mehta | ICAI Reg No. 123456
"""

if __name__ == "__main__":
    print("Testing claim extraction via Groq...\n")
    result = extract_claims_dict(SAMPLE_TEXT)

    import json
    print(json.dumps(result, indent=2))
    print("\n✅ Extraction successful" if result else "\n❌ Extraction failed")

# Test OCR pipeline
from extraction.ocr import extract_text

def test_ocr(file_path: str):
    print(f"\nTesting OCR on: {file_path}")
    result = extract_text(file_path)
    print(f"Method: {result['method']}")
    print(f"OCR used: {result['ocr_used']}")
    print(f"Text preview: {result['text'][:300]}")
    print("✅ OCR working" if result['text'] else "❌ OCR returned empty")

# Uncomment and point to any PDF to test
# test_ocr("path/to/your/test.pdf")

# Test ELA pipeline
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from forensics.ela import run_ela

def test_ela(file_path: str):
    print(f"\nTesting ELA on: {file_path}")
    result = run_ela(file_path)
    print(f"Result:        {result['result']}")
    print(f"Anomaly score: {result['anomaly_score']}")
    print(f"Regions found: {len(result['flagged_regions'])}")
    print(f"Notes:         {result['notes']}")
    print(f"Heatmap saved: {result['heatmap_path']}")
    print("✅ ELA working")

# Uncomment to test
# test_ela("path/to/your/test.pdf")
# test_ela("path/to/your/test.jpg")

from forensics.metadata import analyze_metadata

def test_metadata(file_path: str):
    print(f"\nTesting metadata analysis on: {file_path}")
    result = analyze_metadata(file_path)
    print(f"Result:   {result['result']}")
    print(f"Flags:    {result['flags']}")
    print(f"Software: {result['software_detected']}")
    print(f"Notes:    {result['notes']}")
    print("✅ Metadata analysis working")

# Uncomment to test
# test_metadata("path/to/your/test.pdf")
# test_metadata("path/to/your/test.jpg")


from forensics.pdf_inspector import inspect_pdf

def test_pdf_inspector(pdf_path: str):
    print(f"\nTesting PDF inspection on: {pdf_path}")
    result = inspect_pdf(pdf_path)
    print(f"Result:              {result['result']}")
    print(f"Flags:               {result['flags']}")
    print(f"Incremental updates: {result['incremental_updates']}")
    print(f"Hidden layers:       {result['hidden_layers_found']}")
    print(f"Embedded files:      {result['embedded_files_found']}")
    print(f"JS detected:         {result['javascript_detected']}")
    print(f"Notes:               {result['notes']}")
    print("✅ PDF inspector working")

# Uncomment to test
# test_pdf_inspector("path/to/your/test.pdf")


from verdict.matrix import run_verdict_pipeline

def test_verdict_matrix():
    print("\nTesting verdict matrix...")

    # Simulate scenario 1 — Sophisticated Forgery
    # Forensics clean, reconciliation contradicted
    result = run_verdict_pipeline(
        ela_result           = {"result": "CLEAN", "anomaly_score": 0.03, "flags": [], "notes": "Clean", "heatmap_path": None},
        metadata_result      = {"result": "CLEAN", "flags": [], "notes": "Clean"},
        pdf_inspector_result = {"result": "CLEAN", "flags": [], "notes": "Clean"},
        mca21_result         = {"result": "CONTRADICTED", "notes": "CIN not found in MCA21 registry"},
        gst_result           = {"result": "UNVERIFIED",   "notes": "GSTIN not registered"},
        claims               = {
            "company_name": "Horizon Ventures Pvt Ltd",
            "cin": "U72900MH2019PTC999999",
            "gstin": "27AABCH1234F1Z5"
        },
        document_id="doc_test_001"
    )

    print(f"Verdict:    {result['verdict']}")
    print(f"Label:      {result['verdict_label']}")
    print(f"Action:     {result['action']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Summary:    {result['summary']}")

    assert result["verdict"] == "SOPHISTICATED_FORGERY", "❌ Wrong verdict"
    print("✅ Verdict matrix working correctly")


test_verdict_matrix()
