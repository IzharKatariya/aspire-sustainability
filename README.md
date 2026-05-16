# ASPIRE
### Automated Sustainability Pipeline for Integrated Reporting & Evaluation

ASPIRE transforms raw corporate ESG data into audit-ready sustainability report drafts in under 60 seconds. Upload a CSV of company KPIs and receive a professionally formatted GRI/TCFD-aligned Word document — with every number automatically validated against source data.

**Live:**
- UI → https://aspire-sustainability.streamlit.app
- API → https://aspire-sustainability.onrender.com

---

## What It Does

1. **Parses** a company ESG CSV (wide or vertical format)
2. **Plans** which of 12 GRI sections can be generated from available data
3. **Generates** each section via LLaMA 3 on Groq, with section-specific prompts
4. **Validates** every number in the output against the source CSV (±5% tolerance)
5. **Assembles** a styled `.docx` with title page, 12 sections, and a validation appendix

---

## Performance

| Metric | Value |
|---|---|
| Average generation time | ~30 seconds |
| Sections generated | 12 / 12 (all GRI sections) |
| Validation accuracy | 0 flags on clean data |
| Output size | ~45KB .docx |
| API uptime | Render (free tier — cold start ~30s) |

Benchmarked across Manufacturing, Financial Services, and Retail & FMCG profiles.

---

## Framework Coverage

| Framework | Coverage |
|---|---|
| GRI 2 | Overview, Governance, Targets & Outlook |
| GRI 201-2 | Climate Strategy & Risk Management |
| GRI 302 | Energy Consumption & Efficiency |
| GRI 303 | Water Stewardship |
| GRI 305 | Greenhouse Gas Emissions (Scope 1, 2, 3) |
| GRI 306 | Waste Management & Circular Economy |
| GRI 401 / 403 / 405 | Workforce, Health & Safety, DEI |
| GRI 413 / 205 | Community Investment & Business Ethics |
| TCFD | Governance · Strategy · Risk Management · Metrics & Targets |

---

## Red-Flag Detection

ASPIRE automatically detects material ESG incidents and applies urgency framing:

| Trigger | Threshold | Action |
|---|---|---|
| Fatalities | > 0 | Mandatory disclosure with corrective action language |
| Work injuries | > 15 | Elevated count framing + improvement commitment |
| Employee turnover | > 25% | Retention challenge acknowledgment |
| Data breaches | > 0 | GRI 418-1 explicit disclosure |
| Renewable energy | < 15% | Gap acknowledgment, no greenwashing |
| Supplier code adoption | < 60% | Supply chain gap disclosure |

---

## API Reference

**Base URL:** `https://aspire-sustainability.onrender.com`

### Health Check
```
GET /api/v1/health
```
```json
{"status": "ok", "service": "ASPIRE"}
```

### Generate Report
```
POST /api/v1/generate
Content-Type: multipart/form-data
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `file` | CSV file | Yes | Company ESG data (wide format) |

**Minimum required columns:**
```
company_name, reporting_year, scope1_emissions_tco2e, scope2_emissions_tco2e
```

**Response:** `.docx` file download

**Example (curl):**
```bash
curl -X POST https://aspire-sustainability.onrender.com/api/v1/generate \
  -F "file=@your_company_esg.csv" \
  -o sustainability_report.docx
```

**Response codes:**

| Code | Meaning |
|---|---|
| 200 | Report generated successfully |
| 422 | CSV missing required columns |
| 500 | Internal pipeline error — check Render logs |

### Interactive Docs
```
GET /docs
```
Full Swagger UI with request/response schemas.

---

## CSV Format

Wide format — one row of data, column headers are KPI names.

**Required columns:**
```
company_name, reporting_year, scope1_emissions_tco2e, scope2_emissions_tco2e
```

**Full schema (30 columns):**
```
company_name, reporting_year, industry, country,
employees_total, employees_female_pct, employees_male_pct,
new_hires, employee_turnover_pct, work_related_injuries, fatalities,
training_hours_per_employee, energy_consumption_mwh, renewable_energy_pct,
scope1_emissions_tco2e, scope2_emissions_tco2e, scope3_emissions_tco2e,
water_withdrawal_m3, water_recycled_pct, waste_total_tonnes,
waste_recycled_pct, waste_hazardous_tonnes, community_investment_usd,
board_members_total, board_members_female, independent_directors_pct,
ceo_pay_ratio, supplier_audits_conducted,
suppliers_with_code_of_conduct_pct, data_breaches,
anti_corruption_training_pct
```

Sample CSVs available in `data/sample_csvs/`.

---

## Architecture

```
CSV Upload
    │
    ▼
SectionPlanner          Maps CSV columns → 12 GRI sections
    │                   Skips sections with missing required KPIs
    ▼
LLMPipeline             Builds section-specific prompts
    │                   Injects red-flag materiality alerts
    │                   Calls Groq LLaMA 3 per section (~2.5s each)
    ▼
Validator               Extracts all numbers from LLM output
    │                   Cross-checks against source CSV (±5% tolerance)
    │                   Section-aware matching prevents false positives
    ▼
Assembler               Builds styled .docx
                        Title page · 12 sections · Validation appendix
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq · LLaMA 3.3-70b |
| Backend | FastAPI · Python 3.11 |
| Frontend | Streamlit |
| Document generation | python-docx |
| Data processing | Pandas |
| Deployment | Render (API) · Streamlit Cloud (UI) |

---

## Local Development

### 1. Clone
```bash
git clone https://github.com/IzharKatariya/aspire-sustainability.git
cd aspire-sustainability
```

### 2. Environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### 3. Config
Create `.env` in the root:
```
GROQ_API_KEY=your_key_here
```

### 4. Run
```bash
# Terminal 1 — Backend
uvicorn app.main:app --port 8000 --reload

# Terminal 2 — Frontend
streamlit run streamlit_app.py
```

Frontend will connect to `http://localhost:8000` by default.

For production deployment, set `BACKEND_URL` in Streamlit secrets:
```toml
BACKEND_URL = "https://aspire-sustainability.onrender.com"
```

---

## Project Structure

```
aspire-sustainability/
├── app/
│   ├── core/
│   │   ├── schema.py          # 12 GRI/TCFD section definitions + KPI mappings
│   │   ├── section_planner.py # CSV parser + section readiness logic
│   │   ├── report_template.py # Document style config
│   │   └── config.py          # App settings
│   ├── llm/
│   │   ├── prompts.py         # System + user prompt builder, red-flag detection
│   │   ├── pipeline.py        # LLM orchestration (sequential, rate-limit safe)
│   │   └── groq_client.py     # Groq API client
│   ├── validation/
│   │   └── validator.py       # Numeric cross-check engine
│   ├── document/
│   │   └── assembler.py       # .docx assembly
│   └── api/
│       └── routes.py          # FastAPI endpoints
├── data/
│   └── sample_csvs/           # Sample ESG data (manufacturing, financial, retail)
├── tests/
│   ├── unit/                  # Section planner unit tests
│   └── integration/           # End-to-end pipeline tests
├── streamlit_app.py
└── requirements.txt
```

---

## Disclaimer

ASPIRE generates AI-assisted first drafts. All figures must be independently verified against source data before external publication. The validation appendix in each report identifies any numbers requiring human review.

---

## About

Built by **Izhar Katariya** — Data Scientist and AI/ML Engineer specialising in production-grade AI systems for the sustainability sector.

[GitHub](https://github.com/IzharKatariya) · [LinkedIn](https://linkedin.com/in/izharkatariya)