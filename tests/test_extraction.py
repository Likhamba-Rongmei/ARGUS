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
    print("\n Extraction successful" if result else "\n Extraction failed")
