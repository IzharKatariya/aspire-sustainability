# ASPIRE: Automated Sustainability Pipeline for Integrated Reporting & Evaluation

## Strategic Overview

ASPIRE is a production-grade AI orchestration pipeline designed to automate the transition from raw corporate ESG data to audit-ready sustainability disclosures. By integrating Generative AI with structured validation logic, the system generates reports aligned with GRI (Global Reporting Initiative) and TCFD (Task Force on Climate-related Financial Disclosures) frameworks — transforming a weeks-long manual consulting process into a multi-minute automated workflow.

---

## Core Functionality

- **Intelligent Section Planning:** Maps quantitative KPIs from CSV inputs to specific disclosure requirements (e.g., GRI 305 for Emissions).
- **Multi-Step LLM Pipeline:** Orchestrates parallel calls to GPT-4o-mini or LLaMA-3 with section-specific system prompts and response constraints.
- **Hallucination Prevention Layer:** Employs a numeric validation engine that cross-references LLM outputs against source data to ensure 100% factual integrity.
- **Automated Assembly:** Generates professionally formatted `.docx` reports with structured headings, tables, and cover pages.

---

## Framework Coverage

| Framework     | Standards / Pillars Covered                                              |
|---------------|--------------------------------------------------------------------------|
| GRI Standards | GRI 2 (General), 302 (Energy), 303 (Water), 305 (Emissions), 306 (Waste), 401/403/405 (Social/Diversity) |
| TCFD          | Governance, Strategy, Risk Management, Metrics & Targets                 |

---

## Technical Architecture

```
CSV Input → Section Planner → LLM Orchestration → Validation Layer → .docx Assembly
  (Raw)        (Logic)            (GenAI)           (Fact-Check)      (Formatting)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangChain, Python 3.11 |
| Models | Groq (LLaMA-3.3-70b), OpenAI (GPT-4o-mini) |
| Backend | FastAPI (Async API design) |
| Data / Validation | Pandas, NumPy, Regex |
| Frontend | Streamlit |

---

## Installation & Local Development

### 1. Clone the Repository
```bash
git clone https://github.com/IzharKatariya/aspire-sustainability.git
cd aspire-sustainability
```

### 2. Environment Setup
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

### 4. Launch Services
```bash
# Backend
uvicorn app.main:app --port 8000

# Frontend
streamlit run streamlit_app.py
```

---

## Project Structure

```
aspire-sustainability/
├── app/
│   ├── core/         # GRI/TCFD schemas and SectionPlanner logic
│   ├── llm/          # Prompt engineering and LLMPipeline
│   ├── validation/   # Numeric cross-check engine to eliminate hallucinations
│   └── document/     # Word document assembly logic (python-docx)
├── data/
│   └── sample_csvs/  # Sample ESG data for company_a, company_b, company_c
├── tests/            # 57/57 tests passing (unit + integration)
├── streamlit_app.py
└── requirements.txt
```

---

## Deployment

- **API:** Hosted on Render (FastAPI)
- **Interface:** Hosted on Streamlit Cloud

---

## About the Author

Izhar Katariya is an aspiring Data Scientist and AI/ML Engineer focused on building production-grade AI solutions for the sustainability sector. This project was developed as a flagship portfolio piece for Sustainability Centers of Excellence (CoE) at top-tier consulting firms.
