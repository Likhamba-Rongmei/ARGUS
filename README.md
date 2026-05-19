# ARGUS — Adaptive Real-time Graph-based Underwriting Surveillance System

> SuRaksha Cyber Hackathon 2.0 | Canara Bank | Team: Cyber Junkies

---

## What is ARGUS?

ARGUS is a dual-pipeline intelligent document forensics system for real-time
detection of tampering, forgery, and fabrication across financial statements,
land records, and legal documents in banking underwriting.

Most fraud detection systems run forensic checks OR external verification.
ARGUS runs both in parallel on every document and merges the signals through
an agentic reasoning layer — producing a four-state verdict that catches what
either pipeline alone cannot.

---

## The Core Innovation

Document forgery has two attack strategies:

| Attack | Description | Caught By |
|---|---|---|
| Alteration | Existing document is modified | Pipeline 1 — Forensic Detection |
| Fabrication | Document created from scratch | Pipeline 2 — Ground Truth Reconciliation |

A fabricated document leaves no forensic trace. It looks completely clean.
No existing system catches it. ARGUS does.

---

## The Four-State Verdict Matrix

| Forensic | Reconciliation | Verdict | Meaning |
|---|---|---|---|
| Clean | Confirmed |  CLEARED | High confidence, approved |
| Anomaly | Confirmed |  LIKELY FALSE POSITIVE | Auto-cleared with note |
| Clean | Contradicted |  SOPHISTICATED FORGERY | Escalate immediately |
| Anomaly | Contradicted |  CONFIRMED FRAUD | Hard block |

**Row 3 is the killer feature.** A forensically perfect but factually
impossible document — no prior system catches this. ARGUS does.

**Row 2 is what makes ARGUS deployable.** False positives are structurally
eliminated, not just reduced.

---

## System Architecture

---

## Repository Structure
```text
ARGUS/
├── .env.example
├── .gitignore
├── README.md
├── backend/
│   ├── .env                          # gitignored — real keys here
│   ├── main.py
│   ├── requirements.txt
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── groq_extractor.py
│   │   ├── llm_client.py
│   │   ├── ocr.py
│   │   └── schemas.py
│   ├── forensics/
│   │   ├── __init__.py
│   │   ├── copy_move.py              # skipped for MVP
│   │   ├── ela.py
│   │   ├── metadata.py
│   │   ├── pdf_inspector.py
│   │   └── timestamp.py
│   ├── graph/
│   │   ├── __init__.py
│   │   └── evidence_graph.py
│   ├── reconciliation/
│   │   ├── __init__.py
│   │   ├── gst.py
│   │   └── mca21.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── claims.py
│   │   ├── forensics.py
│   │   ├── graph.py
│   │   ├── reconciliation.py
│   │   ├── status.py
│   │   ├── upload.py
│   │   └── verdict.py
│   └── verdict/
│       ├── __init__.py
│       └── matrix.py
├── demo_scenarios/
│   ├── scenario0_clean_baseline/
│   ├── scenario1_sophisticated_forgery/
│   ├── scenario2_false_positive/
│   └── scenario3_confirmed_fraud/
├── docs/
│   ├── api_contracts.md
│   ├── demo_script.md
│   └── qa_prep.md
├── frontend/
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.jsx
│       ├── index.jsx
│       ├── api/
│       │   └── argus.js
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
│   ├── dilrmp_property_found.json
│   ├── dilrmp_property_notfound.json
│   ├── gst_valid_match.json
│   ├── gst_valid_mismatch.json
│   ├── mca21_cin_found.json
│   └── mca21_cin_notfound.json
└── tests/
    └── test_extraction.py

---
```

## Tech Stack

| Layer | Tools |
|---|---|
| Document Parsing | PyMuPDF, pdfplumber, Tesseract, LayoutLM |
| Claim Extraction | Claude API, Pydantic |
| Visual Forensics | OpenCV (ELA, copy-move) |
| Metadata Forensics | ExifTool, pikepdf, Pillow |
| Reconciliation APIs | MCA21, GST Public API (mock adapters) |
| Knowledge Graph | NetworkX, Neo4j, D3.js |
| Agentic Layer | LangGraph, Claude API |
| Backend | FastAPI, Python |
| Frontend | React, D3.js |

---

## Demo Scenarios

### Scenario 1 — Sophisticated Forgery (Killer Demo)
A fabricated financial statement with a fictional CIN.
Forensics: **Clean**. Reconciliation: **Contradicted**.
Verdict:  **SOPHISTICATED FORGERY**
*No prior system catches this. ARGUS does.*

### Scenario 2 — Likely False Positive (Deployability Argument)
A legitimate document with scan compression artifacts triggering ELA flags.
Forensics: **Anomaly**. Reconciliation: **Confirmed**.
Verdict:  **LIKELY FALSE POSITIVE — Auto-cleared**
*False positives are structurally eliminated, not just reduced.*

### Scenario 3 — Confirmed Fraud (Full Fraud)
Visible tampering + fictional CIN.
Forensics: **Anomaly**. Reconciliation: **Contradicted**.
Verdict:  **CONFIRMED FRAUD — Hard block**

### Scenario 0 — Clean Baseline
Legitimate document, real CIN, clean scan.
Forensics: **Clean**. Reconciliation: **Confirmed**.
Verdict:  **CLEARED**

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- Tesseract OCR installed locally
- ExifTool installed locally
- Anthropic API key

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # add your API keys
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Environment Variables
ANTHROPIC_API_KEY=
MCA21_MOCK=true
GST_MOCK=true

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, demo-ready only |
| `dev` | Integration branch |
| `frontend` | UI development |
| `backend` | FastAPI development |
| `forensics` | Pipeline development |

**Nobody pushes directly to main.**
All work merges into `dev` first, then to `main` when stable.


---

## Current Status

- [x] Idea conceptualized and submitted
- [x] Architecture designed
- [x] Repository initialized
- [ ] Demo documents prepared
- [ ] OCR + claim extraction pipeline
- [ ] Forensic detection pipeline
- [ ] Mock API reconciliation
- [ ] Verdict matrix engine
- [ ] Dashboard
- [ ] End-to-end demo tested
- [ ] Final submission ready

---

## Hackathon Context

**Event:** SuRaksha Cyber Hackathon 2.0
**Organizer:** Canara Bank
**Theme:** Real-time Anomaly Detection
**Phase:** Prototype

---

*ARGUS — See what others miss.*
