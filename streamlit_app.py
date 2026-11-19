"""
streamlit_app.py
─────────────────
Streamlit frontend for the Sustainability Report Generator.

Talks to the FastAPI backend via HTTP.
Set API_URL in .env or environment for deployment.
Defaults to localhost for local development.
"""

import os
import io
import requests
import pandas as pd
import streamlit as st
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────
API_BASE          = os.getenv("API_URL", "http://localhost:8000")
HEALTH_ENDPOINT   = f"{API_BASE}/api/v1/health"
GENERATE_ENDPOINT = f"{API_BASE}/api/v1/generate"

REQUIRED_COLUMNS = [
    "company_name",
    "reporting_year",
    "scope1_emissions_tco2e",
    "scope2_emissions_tco2e",
]

# ── Page setup ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ASPIRE | Sustainability Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@300;400&display=swap');

/* ── Root variables ── */
:root {
    --forest-deep:   #0D1F17;
    --forest-mid:    #132B1E;
    --forest-light:  #1A3828;
    --sage:          #4CAF7D;
    --sage-dim:      #2D7A52;
    --gold:          #C9A96E;
    --cream:         #E8EDE9;
    --cream-dim:     #9FB5A4;
    --white:         #F5F9F6;
    --border:        rgba(76, 175, 125, 0.15);
    --border-bright: rgba(76, 175, 125, 0.35);
}

/* ── Base & fonts ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--cream);
}

.stApp {
    background-color: var(--forest-deep);
    background-image:
        radial-gradient(ellipse at 0% 0%, rgba(76,175,125,0.06) 0%, transparent 60%),
        radial-gradient(ellipse at 100% 100%, rgba(201,169,110,0.04) 0%, transparent 60%);
}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 900px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--forest-mid);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container { padding-top: 2.5rem; }

/* ── Wordmark ── */
.aspire-wordmark {
    font-family: 'Cormorant Garamond', serif;
    font-size: 3.2rem;
    font-weight: 300;
    letter-spacing: 0.18em;
    color: var(--white);
    line-height: 1;
    margin-bottom: 0;
}
.aspire-wordmark span { color: var(--sage); }

.aspire-tagline {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.22em;
    color: var(--cream-dim);
    text-transform: uppercase;
    margin-top: 0.4rem;
    margin-bottom: 2rem;
}

/* ── Section labels ── */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--sage);
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── Cards ── */
.aspire-card {
    background: var(--forest-mid);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
}
.aspire-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, var(--sage) 0%, transparent 100%);
}

/* ── Status pill ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.75rem;
    border-radius: 100px;
    font-size: 0.72rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.08em;
}
.status-online  { background: rgba(76,175,125,0.12); border: 1px solid rgba(76,175,125,0.3); color: var(--sage); }
.status-offline { background: rgba(220,80,80,0.12);  border: 1px solid rgba(220,80,80,0.3);  color: #E07070; }

.status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
}
.status-dot.online  { background: var(--sage);  box-shadow: 0 0 6px var(--sage); }
.status-dot.offline { background: #E07070; box-shadow: 0 0 6px #E07070; }

/* ── Divider ── */
.aspire-divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 2rem 0;
}

/* ── File upload zone ── */
[data-testid="stFileUploader"] {
    border: 1px dashed var(--border-bright) !important;
    border-radius: 2px !important;
    background: rgba(76,175,125,0.03) !important;
    transition: all 0.2s ease;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--sage) !important;
    background: rgba(76,175,125,0.06) !important;
}

/* ── DataFrame ── */
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 2px; }

/* ── Buttons ── */
.stButton > button {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    border-radius: 2px !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"] {
    background: var(--sage) !important;
    border: none !important;
    color: var(--forest-deep) !important;
    font-weight: 500 !important;
}
.stButton > button[kind="primary"]:hover {
    background: #5DC98E !important;
    box-shadow: 0 4px 20px rgba(76,175,125,0.3) !important;
    transform: translateY(-1px) !important;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    border-radius: 2px !important;
    background: transparent !important;
    border: 1px solid var(--sage) !important;
    color: var(--sage) !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: rgba(76,175,125,0.1) !important;
    box-shadow: 0 4px 20px rgba(76,175,125,0.15) !important;
}

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--sage-dim), var(--sage)) !important;
}

/* ── Alerts ── */
.stAlert { border-radius: 2px !important; border-left-width: 3px !important; }

/* ── Sidebar nav label ── */
.sidebar-section {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--cream-dim);
    margin: 1.5rem 0 0.6rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid var(--border);
}

/* ── Report preview card ── */
.report-meta {
    background: linear-gradient(135deg, rgba(76,175,125,0.08) 0%, rgba(201,169,110,0.04) 100%);
    border: 1px solid var(--border-bright);
    border-radius: 2px;
    padding: 1.25rem 1.5rem;
    margin: 1rem 0;
}
.report-meta-company {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.6rem;
    font-weight: 400;
    color: var(--white);
    margin-bottom: 0.2rem;
}
.report-meta-year {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.15em;
    color: var(--gold);
    text-transform: uppercase;
}

/* ── Step indicator ── */
.step-row {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
    padding: 1rem 1.25rem;
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border);
    border-radius: 2px;
}
.step-number {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.8rem;
    font-weight: 300;
    color: var(--sage);
    line-height: 1;
    min-width: 2rem;
}
.step-content h4 {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--white);
    margin: 0 0 0.2rem 0;
}
.step-content p {
    font-size: 0.78rem;
    color: var(--cream-dim);
    margin: 0;
    line-height: 1.5;
}

/* ── Pipeline stages ── */
.pipeline-stage {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: var(--cream-dim);
    padding: 0.3rem 0;
    letter-spacing: 0.05em;
}
.pipeline-stage.active { color: var(--sage); }
.pipeline-stage.done   { color: var(--sage-dim); }
</style>
""", unsafe_allow_html=True)

# ── Session state init ──────────────────────────────────────────────────────────
if "report_ready"    not in st.session_state: st.session_state.report_ready    = False
if "report_bytes"    not in st.session_state: st.session_state.report_bytes    = None
if "report_filename" not in st.session_state: st.session_state.report_filename = None
if "company_name"    not in st.session_state: st.session_state.company_name    = None
if "report_year"     not in st.session_state: st.session_state.report_year     = None
if "last_file"       not in st.session_state: st.session_state.last_file       = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Wordmark
    st.markdown("""
    <div style="padding: 0 0 1.5rem 0; border-bottom: 1px solid rgba(76,175,125,0.15);">
        <div style="font-family:'Cormorant Garamond',serif; font-size:1.8rem; font-weight:300;
                    letter-spacing:0.15em; color:#F5F9F6;">
            A<span style="color:#4CAF7D;">S</span>PIRE
        </div>
        <div style="font-family:'DM Mono',monospace; font-size:0.58rem; letter-spacing:0.2em;
                    color:#9FB5A4; text-transform:uppercase; margin-top:0.3rem;">
            Sustainability Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Backend status
    st.markdown('<div class="sidebar-section">System</div>', unsafe_allow_html=True)
    try:
        resp = requests.get(HEALTH_ENDPOINT, timeout=5)
        if resp.status_code == 200:
            st.markdown("""
            <div class="status-pill status-online">
                <div class="status-dot online"></div> API Online
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-pill status-offline">
                <div class="status-dot offline"></div> API Error
            </div>""", unsafe_allow_html=True)
    except Exception:
        st.markdown("""
        <div class="status-pill status-offline">
            <div class="status-dot offline"></div> API Offline
        </div>""", unsafe_allow_html=True)

    # How it works
    st.markdown('<div class="sidebar-section">Pipeline</div>', unsafe_allow_html=True)
    stages = [
        ("01", "CSV Ingestion",        "Parse and validate ESG data"),
        ("02", "Section Planning",     "Map 12 GRI disclosure areas"),
        ("03", "LLaMA 3 Generation",   "Draft each section via Groq"),
        ("04", "Numeric Validation",   "Cross-check all figures ±5%"),
        ("05", "Document Assembly",    "Compile GRI/TCFD Word report"),
    ]
    for num, title, desc in stages:
        st.markdown(f"""
        <div class="step-row">
            <div class="step-number">{num}</div>
            <div class="step-content">
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>
        </div>""", unsafe_allow_html=True)

    # Sample CSVs
    sample_dir = Path("data/sample_csvs")
    if sample_dir.exists():
        csv_files = sorted(sample_dir.glob("*.csv"))
        if csv_files:
            st.markdown('<div class="sidebar-section">Sample Data</div>', unsafe_allow_html=True)
            for csv_file in csv_files:
                with open(csv_file, "rb") as f:
                    st.download_button(
                        label=f"↓  {csv_file.stem}",
                        data=f,
                        file_name=csv_file.name,
                        mime="text/csv",
                        key=csv_file.name,
                        use_container_width=True,
                    )

# ── Main content ───────────────────────────────────────────────────────────────
# Header
st.markdown("""
<div style="margin-bottom: 2.5rem;">
    <div class="aspire-wordmark">A<span>S</span>PIRE</div>
    <div class="aspire-tagline">Automated Sustainability Pipeline for Integrated Reporting &amp; Evaluation</div>
    <div style="font-size: 0.9rem; color: #9FB5A4; max-width: 580px; line-height: 1.7;">
        Upload your company ESG data and receive a <strong style="color:#E8EDE9;">GRI/TCFD-aligned
        sustainability report</strong> drafted by LLaMA 3 — ready for analyst review in under a minute.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Step 1: Upload ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">01 — Data Input</div>', unsafe_allow_html=True)

st.markdown("""
<div class="aspire-card" style="margin-bottom:1.25rem;">
    <div style="font-size:0.78rem; color:#9FB5A4; line-height:1.7;">
        Required columns: &nbsp;
        <code style="background:rgba(76,175,125,0.1); padding:0.1rem 0.4rem;
                     border-radius:2px; font-size:0.72rem; color:#4CAF7D;">company_name</code> &nbsp;
        <code style="background:rgba(76,175,125,0.1); padding:0.1rem 0.4rem;
                     border-radius:2px; font-size:0.72rem; color:#4CAF7D;">reporting_year</code> &nbsp;
        <code style="background:rgba(76,175,125,0.1); padding:0.1rem 0.4rem;
                     border-radius:2px; font-size:0.72rem; color:#4CAF7D;">scope1_emissions_tco2e</code> &nbsp;
        <code style="background:rgba(76,175,125,0.1); padding:0.1rem 0.4rem;
                     border-radius:2px; font-size:0.72rem; color:#4CAF7D;">scope2_emissions_tco2e</code>
        <br>Download a sample from the sidebar to see the full schema.
    </div>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop your ESG CSV here or click to browse",
    type=["csv"],
    label_visibility="collapsed",
)

# Clear session state if a new file is uploaded
if uploaded_file is not None and uploaded_file.name != st.session_state.last_file:
    st.session_state.report_ready    = False
    st.session_state.report_bytes    = None
    st.session_state.report_filename = None
    st.session_state.company_name    = None
    st.session_state.report_year     = None
    st.session_state.last_file       = uploaded_file.name

# ── CSV validation & preview ───────────────────────────────────────────────────
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        uploaded_file.seek(0)  # reset for later API call

        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]

        if missing:
            st.markdown(f"""
            <div style="background:rgba(220,80,80,0.08); border:1px solid rgba(220,80,80,0.25);
                        border-radius:2px; padding:1rem 1.25rem; margin-top:1rem;">
                <div style="font-family:'DM Mono',monospace; font-size:0.7rem;
                            letter-spacing:0.1em; color:#E07070; margin-bottom:0.4rem;">
                    ✕ &nbsp; VALIDATION FAILED
                </div>
                <div style="font-size:0.8rem; color:#9FB5A4;">
                    Missing required columns:
                    <strong style="color:#E8EDE9;">{', '.join(missing)}</strong>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            # Extract meta
            company = str(df["company_name"].iloc[0]) if "company_name" in df.columns else "Unknown"
            year    = str(df["reporting_year"].iloc[0]) if "reporting_year" in df.columns else "—"
            st.session_state.company_name = company
            st.session_state.report_year  = year

            # Success badge
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:0.75rem; margin-top:1rem;
                        background:rgba(76,175,125,0.06); border:1px solid rgba(76,175,125,0.2);
                        border-radius:2px; padding:0.75rem 1.25rem;">
                <div style="color:#4CAF7D; font-size:1rem;">✓</div>
                <div>
                    <div style="font-size:0.82rem; color:#E8EDE9; font-weight:500;">
                        {uploaded_file.name}
                    </div>
                    <div style="font-family:'DM Mono',monospace; font-size:0.65rem;
                                color:#9FB5A4; letter-spacing:0.08em; margin-top:0.15rem;">
                        {len(df.columns)} columns · {len(df)} row(s) · validated
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            # Data preview
            with st.expander("Preview data", expanded=False):
                st.dataframe(df.head(5), use_container_width=True, hide_index=True)

            st.markdown("<hr class='aspire-divider'>", unsafe_allow_html=True)

            # ── Step 2: Generate ───────────────────────────────────────────────
            st.markdown('<div class="section-label">02 — Generate Report</div>', unsafe_allow_html=True)

            # Report preview card
            st.markdown(f"""
            <div class="report-meta">
                <div style="font-family:'DM Mono',monospace; font-size:0.6rem; letter-spacing:0.2em;
                            color:#9FB5A4; text-transform:uppercase; margin-bottom:0.5rem;">
                    Report Preview
                </div>
                <div class="report-meta-company">{company}</div>
                <div class="report-meta-year">GRI / TCFD Sustainability Report &nbsp;·&nbsp; FY {year}</div>
            </div>""", unsafe_allow_html=True)

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("""
                <div style="font-size:0.8rem; color:#9FB5A4; line-height:1.7; padding-top:0.5rem;">
                    The pipeline will draft <strong style="color:#E8EDE9;">12 GRI disclosure sections</strong>,
                    validate all numeric figures, and assemble a Word document ready for analyst review.
                    Estimated time: <strong style="color:#E8EDE9;">30–60 seconds</strong>.
                </div>""", unsafe_allow_html=True)
            with col2:
                generate_clicked = st.button(
                    "Generate →",
                    type="primary",
                    use_container_width=True,
                    disabled=st.session_state.report_ready,
                )

            # ── Pipeline execution ─────────────────────────────────────────────
            if generate_clicked:
                st.session_state.report_ready = False
                progress_bar = st.progress(0)
                status_box   = st.empty()

                pipeline_steps = [
                    (10,  "Uploading CSV to backend..."),
                    (25,  "Parsing ESG data..."),
                    (40,  "Planning GRI section structure..."),
                    (60,  "LLaMA 3 generating report sections..."),
                    (80,  "Validating figures against source data..."),
                    (92,  "Assembling Word document..."),
                    (100, "Complete."),
                ]

                try:
                    for pct, msg in pipeline_steps[:-2]:
                        progress_bar.progress(pct)
                        status_box.markdown(f"""
                        <div class="pipeline-stage active">▸ &nbsp;{msg}</div>
                        """, unsafe_allow_html=True)

                    response = requests.post(
                        GENERATE_ENDPOINT,
                        files={"file": (uploaded_file.name, uploaded_file, "text/csv")},
                        timeout=600,
                    )

                    progress_bar.progress(92)
                    status_box.markdown("""
                    <div class="pipeline-stage active">▸ &nbsp;Assembling Word document...</div>
                    """, unsafe_allow_html=True)

                    if response.status_code == 200:
                        progress_bar.progress(100)
                        status_box.empty()

                        content_disp = response.headers.get("content-disposition", "")
                        if "filename=" in content_disp:
                            filename = content_disp.split("filename=")[-1].strip('"')
                        else:
                            filename = f"{company.replace(' ', '_')}_{year}_sustainability_report.docx"

                        st.session_state.report_ready    = True
                        st.session_state.report_bytes    = response.content
                        st.session_state.report_filename = filename

                    else:
                        progress_bar.empty()
                        try:
                            detail = response.json().get("detail", response.text)
                        except Exception:
                            detail = response.text
                        status_box.markdown(f"""
                        <div style="background:rgba(220,80,80,0.08); border:1px solid rgba(220,80,80,0.25);
                                    border-radius:2px; padding:1rem 1.25rem;">
                            <div style="font-family:'DM Mono',monospace; font-size:0.7rem;
                                        color:#E07070; margin-bottom:0.3rem;">✕ &nbsp; GENERATION FAILED</div>
                            <div style="font-size:0.8rem; color:#9FB5A4;">{detail}</div>
                        </div>""", unsafe_allow_html=True)

                except requests.exceptions.Timeout:
                    progress_bar.empty()
                    status_box.markdown("""
                    <div style="background:rgba(220,80,80,0.08); border:1px solid rgba(220,80,80,0.25);
                                border-radius:2px; padding:1rem 1.25rem;">
                        <div style="font-family:'DM Mono',monospace; font-size:0.7rem;
                                    color:#E07070; margin-bottom:0.3rem;">✕ &nbsp; REQUEST TIMED OUT</div>
                        <div style="font-size:0.8rem; color:#9FB5A4;">
                            The pipeline exceeded 10 minutes. This may indicate high LLM load.
                            Please retry in a few moments.
                        </div>
                    </div>""", unsafe_allow_html=True)

                except requests.exceptions.ConnectionError:
                    progress_bar.empty()
                    status_box.markdown("""
                    <div style="background:rgba(220,80,80,0.08); border:1px solid rgba(220,80,80,0.25);
                                border-radius:2px; padding:1rem 1.25rem;">
                        <div style="font-family:'DM Mono',monospace; font-size:0.7rem;
                                    color:#E07070; margin-bottom:0.3rem;">✕ &nbsp; BACKEND UNREACHABLE</div>
                        <div style="font-size:0.8rem; color:#9FB5A4;">
                            The API server is not responding on port 8000.
                            Verify the backend container is running.
                        </div>
                    </div>""", unsafe_allow_html=True)

            # ── Step 3: Download ───────────────────────────────────────────────
            if st.session_state.report_ready and st.session_state.report_bytes:
                st.markdown("<hr class='aspire-divider'>", unsafe_allow_html=True)
                st.markdown('<div class="section-label">03 — Download</div>', unsafe_allow_html=True)

                st.markdown(f"""
                <div style="background:linear-gradient(135deg, rgba(76,175,125,0.08) 0%,
                            rgba(201,169,110,0.04) 100%); border:1px solid rgba(76,175,125,0.25);
                            border-radius:2px; padding:1.25rem 1.5rem; margin-bottom:1rem;">
                    <div style="font-family:'DM Mono',monospace; font-size:0.6rem; letter-spacing:0.2em;
                                color:#4CAF7D; text-transform:uppercase; margin-bottom:0.5rem;">
                        ✓ &nbsp; Report Ready
                    </div>
                    <div style="font-family:'Cormorant Garamond',serif; font-size:1.4rem;
                                color:#F5F9F6; margin-bottom:0.2rem;">
                        {st.session_state.company_name}
                    </div>
                    <div style="font-family:'DM Mono',monospace; font-size:0.65rem;
                                color:#C9A96E; letter-spacing:0.1em;">
                        GRI / TCFD Sustainability Report &nbsp;·&nbsp; FY {st.session_state.report_year}
                    </div>
                </div>""", unsafe_allow_html=True)

                st.download_button(
                    label="↓  Download Sustainability Report  (.docx)",
                    data=st.session_state.report_bytes,
                    file_name=st.session_state.report_filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )

                st.markdown("""
                <div style="margin-top:0.75rem; font-size:0.75rem; color:#9FB5A4; line-height:1.6;">
                    The document includes an <strong style="color:#E8EDE9;">Appendix: Validation Summary</strong>
                    flagging any figures that deviate from source data by more than 5%.
                    All content is AI-assisted and must be reviewed before external publication.
                </div>""", unsafe_allow_html=True)

    except Exception as e:
        st.markdown(f"""
        <div style="background:rgba(220,80,80,0.08); border:1px solid rgba(220,80,80,0.25);
                    border-radius:2px; padding:1rem 1.25rem; margin-top:1rem;">
            <div style="font-family:'DM Mono',monospace; font-size:0.7rem;
                        color:#E07070; margin-bottom:0.3rem;">✕ &nbsp; COULD NOT READ FILE</div>
            <div style="font-size:0.8rem; color:#9FB5A4;">
                Ensure the file is a valid CSV. Error: {str(e)}
            </div>
        </div>""", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:4rem; padding-top:1.5rem; border-top:1px solid rgba(76,175,125,0.1);
            display:flex; justify-content:space-between; align-items:center;
            flex-wrap:wrap; gap:0.5rem;">
    <div style="font-family:'DM Mono',monospace; font-size:0.6rem; letter-spacing:0.15em;
                color:rgba(159,181,164,0.5); text-transform:uppercase;">
        ASPIRE &nbsp;·&nbsp; Sustainability Intelligence Platform
    </div>
    <div style="font-family:'DM Mono',monospace; font-size:0.6rem; letter-spacing:0.08em;
                color:rgba(159,181,164,0.4);">
        FastAPI &nbsp;·&nbsp; Streamlit &nbsp;·&nbsp; LangChain &nbsp;·&nbsp; Groq LLaMA 3
    </div>
</div>
""", unsafe_allow_html=True)