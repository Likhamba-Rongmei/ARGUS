# ARGUS — Adaptive Real-time Graph-based Underwriting Surveillance System

> **SuRaksha Cyber Hackathon 2.0 | Canara Bank | Team: Cyber Junkies**

---

## What is ARGUS?

ARGUS is a dual-pipeline intelligent document forensics system for real-time detection of tampering, forgery, and fabrication across financial statements, land records, and legal documents in banking underwriting.

Most fraud detection systems run forensic checks **or** external verification. ARGUS runs **both in parallel** on every document and merges the signals through a four-state verdict matrix — catching what either pipeline alone cannot.

---

## The Core Innovation

Document forgery has two attack strategies:

| Attack | Description | Caught By |
|---|---|---|
| **Alteration** | Existing document is modified | Pipeline 1 — Forensic Detection |
| **Fabrication** | Document created from scratch | Pipeline 2 — Ground Truth Reconciliation |

A fabricated document leaves **no forensic trace**. It looks completely clean to every existing system. ARGUS catches it anyway through cross-pipeline contradiction.

---

## The Four-State Verdict Matrix

| Forensic | Reconciliation | Verdict | Action |
|---|---|---|---|
| Clean | Confirmed | **CLEARED** | Approve |
| Anomaly | Confirmed | **LIKELY FALSE POSITIVE** | Auto-clear with note |
| Clean | Contradicted | **SOPHISTICATED FORGERY** | Escalate immediately |
| Anomaly | Contradicted | **CONFIRMED FRAUD** | Hard block |

**Row 3 is the killer feature.** A forensically perfect but factually impossible document — no prior system catches this. ARGUS does.

**Row 2 is what makes ARGUS deployable.** False positives are structurally eliminated, not just reduced. A badly scanned but legitimate document gets cleared, not flagged.

---

## System Architecture

```
                        ┌─────────────────────────────────┐
                        │         UPLOADED DOCUMENT       │
                        └──────────────┬──────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │                                     │
          ┌─────────▼──────────┐               ┌──────────▼──────────┐
          │   PIPELINE 1       │               │   PIPELINE 2        │
          │ Forensic Detection │               │ Ground Truth Recon  │
          ├────────────────────┤               ├─────────────────────┤
          │ • ELA (OpenCV)     │               │ • OCR (Tesseract)   │
          │ • Metadata         │               │ • Claim Extraction  │
          │   (ExifTool/pikepdf│               │   (Groq LLM)        │
          │ • PDF Structure    │               │ • MCA21 lookup      │
          │ • Timestamp checks │               │ • GST Network check │
          └─────────┬──────────┘               │ • DILRMP lookup     │
                    │                          └──────────┬──────────┘
                    │                                     │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │        VERDICT MATRIX           │
                    │   Four-state logic engine       │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │       EVIDENCE GRAPH            │
                    │   NetworkX → D3.js visualisation│
                    └─────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **LLM / Claim Extraction** | Groq API — `llama-3.1-8b-instant` (free tier) |
| **OCR** | Tesseract (local) |
| **Visual Forensics** | OpenCV — Error Level Analysis |
| **Metadata Forensics** | ExifTool, pikepdf, exifread (local) |
| **Reconciliation** | Mock JSON adapters for MCA21, GST, DILRMP |
| **Evidence Graph** | NetworkX (build) + D3.js (visualise) |
| **Backend** | FastAPI + Python |
| **Frontend** | React + D3.js |
| **Verdict Engine** | Pure Python four-state logic |

> **Runtime:** Fully local. No cloud deployment required for demo.
> FastAPI on `localhost:8000`, React on `localhost:3000`.

---

## Repository Structure

```
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
│   │   ├── groq_extractor.py         # Groq LLM claim extraction
│   │   ├── llm_client.py             # Groq API client
│   │   ├── ocr.py                    # Tesseract OCR wrapper
│   │   └── schemas.py                # Pydantic claim schemas
│   ├── forensics/
│   │   ├── __init__.py
│   │   ├── ela.py                    # Error Level Analysis (OpenCV)
│   │   ├── metadata.py               # EXIF / metadata forensics
│   │   ├── pdf_inspector.py          # PDF structure inspection
│   │   ├── timestamp.py              # Temporal consistency checks
│   │   └── copy_move.py              # Copy-move detection (skipped MVP)
│   ├── graph/
│   │   ├── __init__.py
│   │   └── evidence_graph.py         # NetworkX graph builder
│   ├── reconciliation/
│   │   ├── __init__.py
│   │   ├── mca21.py                  # MCA21 company registry adapter
│   │   └── gst.py                    # GST Network adapter
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── upload.py                 # POST /api/upload
│   │   ├── status.py                 # GET  /api/status/{job_id}
│   │   ├── verdict.py                # GET  /api/verdict/{job_id}
│   │   ├── claims.py                 # GET  /api/claims/{job_id}
│   │   ├── forensics.py              # GET  /api/forensics/{job_id}
│   │   ├── reconciliation.py         # GET  /api/reconciliation/{job_id}
│   │   └── graph.py                  # GET  /api/graph/{job_id}
│   └── verdict/
│       ├── __init__.py
│       └── matrix.py                 # Four-state verdict engine
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
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.jsx
│       ├── index.jsx
│       ├── api/
│       │   └── argus.js              # All API calls
│       ├── components/
│       │   ├── EvidenceGraph.jsx     # D3.js force-directed graph
│       │   ├── FileUpload.jsx        # Drag-and-drop upload
│       │   ├── ForensicsPanel.jsx    # Pipeline 1 results accordion
│       │   ├── ReconciliationPanel.jsx # Pipeline 2 results
│       │   ├── StatusPoller.jsx      # Background job polling
│       │   └── VerdictBadge.jsx      # Four-state verdict display
│       └── pages/
│           └── Dashboard.jsx         # Main UI
├── mock_apis/
│   ├── mca21_cin_found.json
│   ├── mca21_cin_notfound.json
│   ├── gst_valid_match.json
│   ├── gst_valid_mismatch.json
│   ├── dilrmp_property_found.json
│   └── dilrmp_property_notfound.json
└── tests/
    └── test_extraction.py
```

---

## Setup Instructions

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ |
| Tesseract OCR | Any recent (must be in PATH) |
| ExifTool | Any recent (must be in PATH) |

Install Tesseract:
- **Ubuntu/Debian:** `sudo apt install tesseract-ocr`
- **macOS:** `brew install tesseract`
- **Windows:** [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)

Install ExifTool:
- **Ubuntu/Debian:** `sudo apt install libimage-exiftool-perl`
- **macOS:** `brew install exiftool`
- **Windows:** [Download from exiftool.org](https://exiftool.org)

---

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env         # then add your GROQ_API_KEY
uvicorn main:app --reload
```

Backend will be live at `http://localhost:8000`.
Swagger docs at `http://localhost:8000/docs`.

---

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend will open at `http://localhost:3000`.

---

### Environment Variables

Copy `.env.example` to `backend/.env` and fill in your values:

```env
GROQ_API_KEY=your_actual_key_here
LLM_PROVIDER=groq
MCA21_MOCK=true
GST_MOCK=true
DILRMP_MOCK=true
BACKEND_HOST=localhost
BACKEND_PORT=8000
```

> Get a free Groq API key at [console.groq.com](https://console.groq.com).
> All reconciliation APIs run in mock mode for the demo — no external API keys required.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload document, returns `job_id` |
| `GET` | `/api/status/{job_id}` | Poll analysis status |
| `GET` | `/api/verdict/{job_id}` | Get four-state verdict |
| `GET` | `/api/claims/{job_id}` | Get extracted claims |
| `GET` | `/api/forensics/{job_id}` | Get forensic analysis results |
| `GET` | `/api/reconciliation/{job_id}` | Get reconciliation results |
| `GET` | `/api/graph/{job_id}` | Get evidence graph (node-link JSON) |

All result endpoints return `HTTP 202` if the job is still running.

---

## Demo Scenarios

Four pre-built scenarios covering every cell of the verdict matrix:

### Scenario 0 — Clean Baseline
- Legitimate document, real CIN, clean scan
- Forensics: **Clean** | Reconciliation: **Confirmed**
- Expected verdict: `CLEARED`

### Scenario 1 — Sophisticated Forgery *(killer demo)*
- Fabricated financial statement with a fictional CIN (ending `999999`)
- Forensically perfect — no pixel or metadata anomalies
- Reconciliation fails: CIN does not exist in MCA21
- Forensics: **Clean** | Reconciliation: **Contradicted**
- Expected verdict: `SOPHISTICATED FORGERY`
- **No prior system catches this. ARGUS does.**

### Scenario 2 — Likely False Positive *(deployability argument)*
- Legitimate document with bad scan compression triggering ELA flags
- Real CIN confirmed by MCA21
- Forensics: **Anomaly** | Reconciliation: **Confirmed**
- Expected verdict: `LIKELY FALSE POSITIVE`
- **Demonstrates ARGUS does not over-block legitimate documents.**

### Scenario 3 — Confirmed Fraud
- Tampered document (visible pixel anomalies) + fictional CIN
- Both pipelines fail independently
- Forensics: **Anomaly** | Reconciliation: **Contradicted**
- Expected verdict: `CONFIRMED FRAUD`

---

## Mock API Logic

All reconciliation adapters run against local JSON files in `mock_apis/`. No external network calls are made during the demo.

| Trigger | Behaviour |
|---|---|
| CIN ending in `999999` | MCA21 returns `not_found` → CONTRADICTED |
| Any other CIN | MCA21 returns `found` + company details → CONFIRMED |
| GSTIN with matching turnover (±20%) | GST returns `match` → CONFIRMED |
| GSTIN with mismatched turnover | GST returns `mismatch` → CONTRADICTED |

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, demo-ready only |
| `dev` | Integration branch |
| `frontend` | UI development |
| `backend` | FastAPI development |
| `forensics` | Pipeline development |

Nobody pushes directly to `main`. All work merges into `dev` first, then to `main` when stable.

---

## Project Status

- [x] Architecture designed
- [x] Repository initialised
- [x] Extraction pipeline (OCR + Groq)
- [x] Forensic pipeline (ELA, metadata, PDF, timestamp)
- [x] Mock reconciliation adapters (MCA21, GST, DILRMP)
- [x] Verdict matrix engine
- [x] Evidence graph builder (NetworkX)
- [x] FastAPI backend (all 7 endpoints)
- [x] React frontend (Dashboard, all components)
- [ ] Demo scenario documents prepared
- [ ] End-to-end run tested
- [ ] Final submission ready

---

## Hackathon Context

| | |
|---|---|
| **Event** | SuRaksha Cyber Hackathon 2.0 |
| **Organiser** | Canara Bank |
| **Theme** | Real-time Anomaly Detection in Banking |
| **Team** | Cyber Junkies |
| **Phase** | Prototype |

---

*ARGUS — See what others miss.*
