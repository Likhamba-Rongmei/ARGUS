# ARGUS — Adaptive Real-time Graph-based Underwriting Surveillance

> SuRaksha Cyber Hackathon 2.0 | Canara Bank | Team: Cyber Junkies

*ARGUS — See what others miss.*

---

## What is ARGUS?

ARGUS is a dual-pipeline intelligent document forensics system for real-time detection of tampering, forgery, and fabrication across financial statements, GST invoices, and legal documents in banking underwriting.

Most fraud detection systems run forensic checks OR external verification. ARGUS runs both in parallel on every document and merges the signals through a verdict matrix — producing a four-state decision that catches what either pipeline alone cannot.

Supported file formats: **PDF, PNG, JPG, TIFF**

---

## The Core Innovation

Document forgery has two attack strategies:

| Attack | Description | Caught By |
|---|---|---|
| Alteration | Existing document is modified | Pipeline 1 — Forensic Detection |
| Fabrication | Document created from scratch | Pipeline 2 — Ground Truth Reconciliation |

A fabricated document leaves no forensic trace. It looks completely clean. No existing system catches it. ARGUS does — because forensic cleanliness combined with a contradicted claim is itself the signal.

---

## Design Philosophy

**Pipeline 1 is intentionally aggressive.**

A false positive at the forensic layer is safer than a false negative, because Pipeline 2 acts as the confirmation layer. If Pipeline 1 flags a clean document but Pipeline 2 confirms the claims, the verdict resolves to LIKELY FALSE POSITIVE — not a hard block. The system self-corrects.

A false negative at Pipeline 1 is dangerous. If both pipelines miss a fraudulent document, it gets CLEARED. That is the worst outcome ARGUS is designed to prevent.

This means: **a fraudster must beat both pipelines simultaneously to get a CLEARED verdict.**

**Why not just Pipeline 2 alone?**

Pipeline 2 verifies claims against registries — but it can be fooled by three attacks it cannot detect on its own:

1. Tampered real documents — someone takes a legitimate company's document with a valid CIN and GSTIN, then edits the declared turnover from 5 Crore to 500 Crore. Pipeline 2 confirms the identifiers are real and passes it. Pipeline 1 catches the pixel-level edit.

2. Stolen identity — a fraudster copies a real company's valid CIN and GSTIN onto a fake document. Pipeline 2 confirms both numbers exist in the registry and passes it. Pipeline 1 detects the document was digitally constructed or that metadata was stripped.

3. Backdated documents — a document created today but claiming to be a 2019 financial statement. Pipeline 2 has no way to verify document age. Pipeline 1's temporal consistency check catches the creation date mismatch.

---

## The Four-State Verdict Matrix

| Forensic | Reconciliation | Verdict | Meaning |
|---|---|---|---|
| Clean | Confirmed | CLEARED | High confidence, approved |
| Anomaly | Confirmed | LIKELY FALSE POSITIVE | Auto-cleared with note |
| Clean | Contradicted | SOPHISTICATED FORGERY | Escalate immediately |
| Anomaly | Contradicted | CONFIRMED FRAUD | Hard block |

**Row 3 is the killer feature.** A forensically perfect but factually impossible document — a clean fake created from scratch with a fictional CIN or invalid GSTIN. No prior system catches this. ARGUS does.

**Row 2 is what makes ARGUS deployable.** False positives from scan compression or screenshot artifacts are structurally resolved by Pipeline 2, not just reduced.

---

## How It Works

```
Document Upload (PDF / PNG / JPG / TIFF)
      │
      ▼
OCR Extraction
(Tesseract + PyMuPDF)
      │
      ▼
Claim Extraction
(Groq LLaMA — extracts CIN, GSTIN, company name, revenue)
      │
 ┌────┴────┐
 ▼         ▼
Pipeline 1 Pipeline 2
Forensic Reconciliation
Analysis (MCA21 + GST)
 │         │
 └────┬────┘
      ▼
Verdict Matrix
(4-state decision)
      │
      ▼
Evidence Graph
(Force-directed visualization)
```

### Pipeline 1 — Forensic Analysis

| Check | What It Detects |
|---|---|
| Error Level Analysis (ELA) | Pixel-level re-save artifacts from image editing. Threshold calibrated to 5.0 to prioritize recall. |
| Metadata Forensics | Suspicious editing software in EXIF, stripped metadata on documents that should have it, timestamp mismatches |
| PDF Structure Inspection | Incremental saves, hidden layers, embedded files, font inconsistencies, object stream anomalies |
| Temporal Consistency | Creation vs modification date anomalies, backdated documents |

### Pipeline 2 — Ground Truth Reconciliation

| Check | What It Verifies |
|---|---|
| MCA21 Registry | CIN format validity and existence in company registry |
| GST Network | GSTIN format validity, active status, and revenue slab consistency |

---

## Tech Stack

| Layer | Tools |
|---|---|
| Document Parsing | PyMuPDF, pdfplumber, Tesseract OCR |
| Claim Extraction | Groq API (LLaMA), Pydantic |
| Visual Forensics | OpenCV (ELA), Pillow |
| Metadata Forensics | ExifRead, pikepdf |
| Reconciliation | MCA21 mock adapter, GST mock adapter (real API integration in Round 2) |
| Evidence Graph | NetworkX, React force-directed graph |
| Backend | FastAPI, Python, uvicorn |
| Frontend | React.js |

---

## Demo Scenarios

### Scenario 0 — Clean Baseline
Legitimate document, real CIN, clean scan.
Forensics: **Clean** | Reconciliation: **Confirmed** | Verdict: **CLEARED**

### Scenario 1 — Sophisticated Forgery (Killer Demo)
A fabricated financial statement with a fictional CIN. Forensically perfect.
Forensics: **Clean** | Reconciliation: **Contradicted** | Verdict: **SOPHISTICATED FORGERY**
*No prior system catches this. ARGUS does.*

### Scenario 2 — Likely False Positive (Deployability Argument)
A legitimate document with scan compression artifacts triggering ELA flags.
Forensics: **Anomaly** | Reconciliation: **Confirmed** | Verdict: **LIKELY FALSE POSITIVE**
*False positives are structurally resolved, not just reduced.*

### Scenario 3 — Confirmed Fraud
Visible tampering + fictional CIN. Both pipelines fire.
Forensics: **Anomaly** | Reconciliation: **Contradicted** | Verdict: **CONFIRMED FRAUD — Hard block**

---

## Current Status

- [x] Idea conceptualized and submitted
- [x] Architecture designed
- [x] Repository initialized
- [x] OCR + claim extraction pipeline (Groq LLaMA)
- [x] Forensic detection pipeline (ELA, metadata, PDF inspector, timestamp)
- [x] Mock API reconciliation (MCA21 + GST)
- [x] Verdict matrix engine
- [x] Evidence graph visualization
- [x] React dashboard
- [x] End-to-end pipeline tested across PDF, PNG, JPG, TIFF
- [ ] Demo documents finalized
- [ ] Real API integration (Round 2 — Cashfree/Surepass)
- [ ] Final submission ready

---

## Repository Structure

```
ARGUS/
├── .env.example
├── .gitignore
├── README.md
├── backend/
│ ├── main.py
│ ├── requirements.txt
│ ├── extraction/
│ │ ├── groq_extractor.py
│ │ ├── ocr.py
│ │ └── schemas.py
│ ├── forensics/
│ │ ├── ela.py
│ │ ├── metadata.py
│ │ ├── pdf_inspector.py
│ │ └── timestamp.py
│ ├── graph/
│ │ └── evidence_graph.py
│ ├── reconciliation/
│ │ ├── gst.py
│ │ └── mca21.py
│ ├── routers/
│ │ ├── upload.py
│ │ ├── claims.py
│ │ ├── forensics.py
│ │ ├── graph.py
│ │ ├── reconciliation.py
│ │ ├── status.py
│ │ └── verdict.py
│ └── verdict/
│ └── matrix.py
├── frontend/
│ └── src/
│ ├── App.jsx
│ ├── api/argus.js
│ ├── components/
│ │ ├── EvidenceGraph.jsx
│ │ ├── FileUpload.jsx
│ │ ├── ForensicsPanel.jsx
│ │ ├── ReconciliationPanel.jsx
│ │ ├── StatusPoller.jsx
│ │ └── VerdictBadge.jsx
│ └── pages/
│ └── Dashboard.jsx
├── mock_apis/
│ ├── gst_valid_match.json
│ ├── gst_valid_mismatch.json
│ ├── mca21_cin_found.json
│ └── mca21_cin_notfound.json
└── tests/
└── test_extraction.py
```

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Homebrew (Mac) or Git Bash (Windows)
- Groq API key (free at console.groq.com)
- Tesseract OCR (`brew install tesseract`)
- ExifTool (`brew install exiftool`)

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
```

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, demo-ready only |
| `dev` | Integration branch — all fixes go here first |

---

## Known Limitations

### The Stolen Identity + Clean Fabrication Attack

If an attacker creates a document from scratch (no tampering, beats Pipeline 1)
AND uses a stolen but real CIN and GSTIN (registry confirms, beats Pipeline 2),
ARGUS returns CLEARED. This is a known blind spot.

**Why it is still a hard attack in practice:**

- CIN + GSTIN + company name + state + turnover slab must all be internally
consistent. One mismatch contradicts the document and fires Pipeline 2.
- The declared revenue must fall within the actual GST turnover slab of the
stolen identity. Overclaiming revenue on a small company's credentials
gets caught by the revenue cross-check.
- This attack requires prior identity theft of another company's credentials —
a separate and harder crime that leaves its own trail.

**What closes this gap in production (Round 2 roadmap):**

- Liveness check — flag if the same CIN has been submitted multiple times
across different applications
- Cross-document consistency — balance sheet vs ITR vs bank statement
must agree on figures
- Behavioural signals — submission metadata, device fingerprint, velocity

No single-layer system catches everything. ARGUS is designed so that
each additional layer geometrically increases the attacker's cost.

---
## Hackathon Context

**Event:** SuRaksha Cyber Hackathon 2.0
**Organizer:** Canara Bank
**Theme:** Real-time Anomaly Detection
**Round 1 Deadline:** 24th May 2026
**Prototype Phase:** 1st June – 30th June 2026
**Final Onsite (Bangalore):** 20th July 2026
