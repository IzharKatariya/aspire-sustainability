# AI-Powered Sustainability Report Generator

> A GenAI application that transforms raw company ESG data into structured,
> GRI/TCFD-aligned sustainability report drafts using a multi-step LLM pipeline.

---

## What It Does

1. **Ingests** a company's ESG data as a CSV file
2. **Plans** which GRI/TCFD report sections can be written based on available data
3. **Generates** each section using an LLM with structured prompts
4. **Validates** all numeric claims against the source CSV to prevent hallucination
5. **Assembles** a professionally formatted Word (.docx) report for download

---

## Why This Matters

Sustainability reporting is a $1B+ consulting service. Companies like McKinsey,
Deloitte, and PwC charge millions to produce GRI/TCFD-aligned reports manually.
This project automates the first draft — reducing report generation time from
weeks to minutes while maintaining framework compliance.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend API | FastAPI + Python | Receives uploads, returns reports |
| LLM Pipeline | Groq (LLaMA 3) / OpenAI (GPT-4o-mini) | Generates report sections |
| Validation | pandas | Hallucination detection |
| Document Assembly | python-docx | Builds the .docx output |
| Frontend | Streamlit | Web interface |
| Deployment | Render + Streamlit Cloud | Production hosting |

---

## Sustainability Standards Covered

### GRI (Global Reporting Initiative)
- GRI 2 — General Disclosures (company overview, governance)
- GRI 302 — Energy
- GRI 303 — Water
- GRI 305 — Emissions (Scope 1, 2, 3)
- GRI 306 — Waste
- GRI 401 — Employment
- GRI 403 — Occupational Health & Safety
- GRI 405 — Diversity & Equal Opportunity

### TCFD (Task Force on Climate-related Financial Disclosures)
- Governance
- Strategy
- Risk Management
- Metrics & Targets

---

## Project Structure
app/
├── core/          → Configuration, GRI/TCFD schema, section planner
├── llm/           → LLM pipeline, prompt templates
├── validation/    → Hallucination detection, numeric cross-checks
├── document/      → Word document assembly
├── api/           → FastAPI endpoints
└── utils/         → Shared helper functions
data/
└── sample_csvs/   → Sample data for 3 fictitious companies
tests/
├── unit/          → Individual module tests
└── integration/   → End-to-end pipeline tests

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/izharkatariya/sustainability-report-generator.git
cd sustainability-report-generator
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Open .env and add your API keys
```

---

## Running Locally

### Start the backend
```bash
uvicorn app.api.main:app --reload
```

### Start the frontend (separate terminal)
```bash
streamlit run app/frontend/main.py
```

Then open `http://localhost:8501` in your browser.

---

## How It Works — Pipeline Architecture

CSV Upload
↓
Section Planner     → Reads CSV, maps KPIs to GRI sections, flags missing data
↓
LLM Pipeline        → One LLM call per section with structured system prompts
↓
Validation Layer    → Cross-checks all numbers in LLM output against CSV
↓
Document Assembly   → Builds formatted .docx with cover page, tables, headings
↓
Download Report
---

## Hallucination Prevention

A key feature of this project is the validation layer that prevents the LLM
from inventing numbers. After each section is generated, the validator:

1. Extracts all numeric values from the LLM output
2. Cross-references each number against the source CSV
3. Flags any value that differs by more than 5% from the source
4. Regenerates or warns before including flagged sections in the final report

---

## Build Log

| Day | What Was Built |
|-----|---------------|
| Day 1 | Project scaffold, folder structure, git setup, dependencies |
| Day 2 | GRI/TCFD schema design, report section template |
| Day 3 | Sample CSVs for 3 fictitious companies |
| Day 4 | Section planner module |
| Day 5 | Unit tests for section planner |
| ... | ... |

---

## Author

Built as a portfolio project targeting AI/ML Associate roles at top consulting
firms' Sustainability Centers of Excellence.