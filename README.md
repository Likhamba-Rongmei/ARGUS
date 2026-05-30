# ARGUS — Adaptive Real-time Graph-based Underwriting Surveillance


*ARGUS — See what others miss.*

---

## What is ARGUS?

ARGUS is a dual-pipeline intelligent document forensics system for real-time detection of tampering, forgery, and fabrication across tax invoices, bank statements, and land records in banking underwriting.

Most fraud detection systems run forensic checks OR external verification. ARGUS runs both in parallel on every document and merges the signals through a verdict matrix — producing a four-state decision that catches what either pipeline alone cannot.

Supported file formats: **PDF, PNG, JPG, TIFF**

---

## The Core Innovation

Document forgery has two attack strategies:

| Attack | Description | Caught By |
|---|---|---|
| Alteration | Existing document is modified after creation | Pipeline 1 — Forensic Detection |
| Fabrication | Document created from scratch with false claims | Pipeline 2 — Ground Truth Reconciliation |

A fabricated document leaves no forensic trace. It looks completely clean. No existing system catches it. ARGUS does — because forensic cleanliness combined with a contradicted claim is itself the signal.

---

## Design Philosophy

**Pipeline 1 is intentionally aggressive.**

A false positive at the forensic layer is safer than a false negative, because Pipeline 2 acts as the confirmation layer. If Pipeline 1 flags a clean document but Pipeline 2 confirms the claims, the verdict resolves to LIKELY_FALSE_POSITIVE — not a hard block. The system self-corrects.

A false negative at Pipeline 1 is dangerous. If both pipelines miss a fraudulent document, it gets CLEARED. That is the worst outcome ARGUS is designed to prevent.

This means: **a fraudster must beat both pipelines simultaneously to get a CLEARED verdict.**

**Why not just Pipeline 2 alone?**

Pipeline 2 verifies claims against registries but cannot detect:

1. Tampered real documents — a legitimate document with a valid CIN/GSTIN where the declared turnover has been edited. Pipeline 2 confirms the identifiers. Pipeline 1 catches the pixel-level or structural edit.

2. Stolen identity on fabricated documents — a fraudster uses a real company's CIN and GSTIN on a fake document. Pipeline 2 confirms both numbers exist. Pipeline 1 detects the document was digitally constructed or that metadata was stripped.

3. Backdated documents — a document created today claiming to be from 2019. Pipeline 2 cannot verify document age. Pipeline 1's temporal consistency check catches the creation date anomaly.

**Why not just Pipeline 1 alone?**

Pipeline 1 cannot tell if the numbers inside are true — only if the file was tampered with. A clean fake created from scratch with realistic but false data passes Pipeline 1 every time.

---

## The Four-State Verdict Matrix

| Forensic | Reconciliation | Verdict | Meaning |
|---|---|---|---|
| Clean | Confirmed | CLEARED | High confidence, approved |
| Anomaly | Confirmed | LIKELY_FALSE_POSITIVE | Auto-cleared with note |
| Clean | Contradicted | SOPHISTICATED_FORGERY | Escalate immediately |
| Anomaly | Contradicted | CONFIRMED_FRAUD | Hard block |

**Row 3 is the killer feature.** A forensically perfect but factually impossible document — a clean fake created from scratch with a fictional CIN or GSTIN that does not exist in any registry. No prior system catches this. ARGUS does.

**Row 2 is what makes ARGUS deployable.** False positives from scan compression or PDF export artifacts are structurally resolved by Pipeline 2, not just reduced.

---

## How It Works

```
Document Upload (PDF / PNG / JPG / TIFF)
        │
        ▼
   OCR Extraction
   (Tesseract + PyMuPDF — fallback to OCR if native text insufficient)
        │
        ▼
   Unicode Sanitization
   (Strips invalid byte sequences from regional language OCR output
    before sending to Groq — prevents JSON parse errors)
        │
        ▼
   Claim Extraction
   (Groq LLaMA — extracts CIN, GSTIN, account number, property ID, owner name, revenue)
        │
   ┌────┴────┐
   ▼         ▼
Pipeline 1  Pipeline 2
Forensic    Reconciliation
Analysis    (MCA21 + GST + NACH + DILRMP)
   │         │
   └────┬────┘
        ▼
   Verdict Matrix
   (4-state decision engine)
        │
        ▼
   Evidence Graph
   (Force-directed visualization — nodes, edges, contradicts lines)
```

---

## Pipeline 1 — Forensic Analysis

| Check | Applies To | What It Detects |
|---|---|---|
| Error Level Analysis (ELA) | PNG, JPG, TIFF | Pixel-level re-save artifacts. Threshold 5.5. Skipped for PDFs — unreliable due to internal image compression layers in government portal PDFs. |
| JPEG Ghost Analysis | JPG only | Double compression detection — catches Photoshop, Snapseed, Canva edits regardless of editing software. |
| Noise Inconsistency Analysis | PNG, TIFF | Sensor noise pattern breaks at edit boundaries — catches region erasure, text overlay, cloning. |
| Metadata Forensics | All | Suspicious editing software in EXIF, timestamp mismatches, stripped metadata on documents that should have it. |
| PDF Structure Inspection | PDF only | Incremental saves, hidden layers, embedded files, font inconsistencies. Object ratio check removed — unreliable for modern PDF generators (ClearTax, Canva produce 999 objects/page legitimately). |
| Temporal Consistency | All | Creation vs modification date anomalies, backdated documents. |

**Key calibration decisions made during testing:**
- ELA skipped for PDFs — government portal PDFs (Bhulekh 7/12, SBI statements) have embedded scanned image layers that produce ELA scores of 8-10 on unmodified documents, making the signal useless
- ELA threshold raised to 5.5 — Canva and ClearTax PDF exports produce false positives at 5.0
- `stripped_metadata` removed as anomaly trigger — Mac screenshots legitimately have no EXIF
- SKIPPED checks hidden from frontend panel and evidence graph

---

## Pipeline 2 — Ground Truth Reconciliation

| Adapter | Document Type | What It Verifies |
|---|---|---|
| MCA21 | Tax invoice, financial statement | CIN format and company name match against corporate registry |
| GST Network | Tax invoice | GSTIN format, active status, revenue slab consistency |
| NACH | Bank statement | Account number, account holder name (prefix-normalized), bank name (alias-mapped — SBIN → State Bank of India), KYC status |
| DILRMP | Land record | Property ID, survey number, owner name (case-insensitive partial match) against land registry |

**Reconciliation logic:**
- UNVERIFIED — document has no relevant identifiers for that adapter. Treated as neutral, hidden from UI and graph.
- CONTRADICTED — identifier found but does not match registry data.
- CONFIRMED — identifier matches registry data.

---

## Demo Documents

Three document types tested end-to-end:

**Tax Invoice** — created using Referns (web invoice generator). Full field control. Clean version, sophisticated forgery (fictional GSTIN), and tampered version (amount edited in Preview) all produced correct verdicts.

**Bank Statement** — SBI specimen statement sourced from Scribd (publicly available). Clean scenario uses original. Tampered version edited in Preview — PDF Structure Inspector caught the incremental update. NACH verifies account number, holder name, and bank name.

**Land Record (7/12 Extract)** — Maharashtra Bhulekh record sourced from Scribd (public government portal document). Contains Marathi text requiring Unicode sanitization to prevent malformed JSON breaking Groq's extraction. Tampered version created in Acrobat by changing the survey number — DILRMP contradicted the modified value.

---

## Known Limitations

### The Stolen Identity + Clean Fabrication Attack

If an attacker creates a document from scratch (no tampering, beats Pipeline 1) AND uses a stolen but real CIN and GSTIN (registry confirms, beats Pipeline 2), ARGUS returns CLEARED. This is a known blind spot.

Why it is still a hard attack in practice:
- CIN + GSTIN + company name + state + turnover slab must all be internally consistent. One mismatch fires Pipeline 2.
- Declared revenue must fall within the actual GST turnover slab of the stolen identity. Overclaiming on a small company's credentials gets caught.
- This attack requires prior identity theft — a separate and harder crime.

What closes this gap in production (future scope):
- Liveness check — flag if the same CIN appears across multiple submissions
- Cross-document consistency — balance sheet vs ITR vs bank statement must agree
- Behavioural signals — submission metadata, device fingerprint, velocity

### Regional Language OCR

Tesseract does not reliably extract Devanagari (Marathi) text without the language pack. Owner name extraction fails on Marathi land records. Only numeric fields extract reliably. Pipeline 1 compensates by catching edits forensically.

### Professional Editor PNG Detection

ELA and noise analysis do not reliably catch edits made by Photoshop or Snapseed on PNG files — these tools re-export with uniform compression, flattening the signal. JPEG Ghost catches Photoshop on JPG. PNG edits by professional tools remain a gap — DCT coefficient analysis is on the future scope roadmap.

---

## Tech Stack

| Layer | Tools |
|---|---|
| Document Parsing | PyMuPDF, pdfplumber, Tesseract OCR |
| Claim Extraction | Groq API (LLaMA), Pydantic |
| Visual Forensics | OpenCV (ELA, JPEG Ghost, Noise Analysis), Pillow |
| Metadata Forensics | ExifRead, pikepdf |
| Reconciliation | MCA21, GST, NACH, DILRMP mock adapters (real API integration Round 2) |
| Evidence Graph | NetworkX, React force-directed graph |
| Backend | FastAPI, Python, uvicorn |
| Frontend | React.js |

---


## Repository Structure

```
ARGUS/
├── .env.example
├── .gitignore
├── README.md
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── extraction/
│   │   ├── groq_extractor.py
│   │   ├── ocr.py
│   │   └── schemas.py
│   ├── forensics/
│   │   ├── ela.py
│   │   ├── jpeg_ghost.py
│   │   ├── noise_analysis.py
│   │   ├── metadata.py
│   │   ├── pdf_inspector.py
│   │   └── timestamp.py
│   ├── graph/
│   │   └── evidence_graph.py
│   ├── reconciliation/
│   │   ├── gst.py
│   │   ├── mca21.py
│   │   ├── nach.py
│   │   ├── utr.py
│   │   └── dilrmp.py
│   ├── routers/
│   │   ├── upload.py
│   │   ├── claims.py
│   │   ├── forensics.py
│   │   ├── graph.py
│   │   ├── reconciliation.py
│   │   ├── status.py
│   │   └── verdict.py
│   └── verdict/
│       └── matrix.py
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api/argus.js
│       ├── components/
│       │   ├── EvidenceGraph.jsx
│       │   ├── FileUpload.jsx
│       │   ├── ForensicsPanel.jsx
│       │   ├── ReconciliationPanel.jsx
│       │   ├── StatusPoller.jsx
│       │   └── VerdictBadge.jsx
│       └── pages/
│           └── Dashboard.jsx
├── mock_apis/
│   ├── gst_valid_match.json
│   ├── gst_valid_mismatch.json
│   ├── mca21_cin_found.json
│   ├── mca21_cin_notfound.json
│   ├── nach_account_found.json
│   ├── nach_account_notfound.json
│   ├── dilrmp_property_found.json
│   ├── dilrmp_property_notfound.json
│   ├── utr_valid.json
│   └── utr_invalid.json
└── tests/
    └── test_extraction.py
```

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key (free at console.groq.com)
- Tesseract OCR — `brew install tesseract` (Mac) or UB-Mannheim installer (Windows)
- ExifTool — `brew install exiftool` (Mac) or exiftool.org (Windows)

### Backend
```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env
# Add your GROQ_API_KEY to .env
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### Environment Variables
```
GROQ_API_KEY=your_key_here
MCA21_MOCK=true
GST_MOCK=true
NACH_MOCK=true
DILRMP_MOCK=true
```

---

## Mock Data Matching Rules

| Adapter | Confirms | Contradicts |
|---|---|---|
| MCA21 | CIN: `U74999MH2019PTC123456` | Any other CIN |
| GST | GSTIN: `27AABCT1234F1Z5` | Any other GSTIN |
| NACH | Account: `00000010111171171`, Bank: SBI | Any other account |
| DILRMP | Property: `161A1A1/9A/1`, Survey: `15684598638` | Any other property |

To demo with different values, update both the mock JSON in `mock_apis/` and the demo document to use that exact value.

---


