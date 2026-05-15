"""
streamlit_app.py
─────────────────
Streamlit frontend for the Sustainability Report Generator.

Talks to the FastAPI backend via HTTP.
Set BACKEND_URL in .env or Streamlit secrets for deployment.
Defaults to localhost for local development.
"""

import os
import requests
import streamlit as st
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
GENERATE_ENDPOINT = f"{BACKEND_URL}/api/v1/generate"
HEALTH_ENDPOINT   = f"{BACKEND_URL}/api/v1/health"

# ── Page setup ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ASPIRE | Sustainability Report Generator",
    page_icon="🌱",
    layout="centered",
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🌱 ASPIRE")
st.subheader("Automated Sustainability Pipeline for Integrated Reporting & Evaluation")
st.markdown(
    "Upload your company ESG data as a CSV file and receive a "
    "**GRI/TCFD-aligned sustainability report draft** as a Word document. "
    "Powered by LLaMA 3 via Groq."
)

st.divider()

# ── Backend status ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("System Status")
    try:
        resp = requests.get(HEALTH_ENDPOINT, timeout=30)
        if resp.status_code == 200:
            st.success("API: Online ✓")
        else:
            st.error("API: Error")
    except requests.exceptions.ConnectionError:
        st.error("API: Offline ✗")
        st.info("Start the backend:\n```\nuvicorn app.main:app --port 8000\n```")

    st.divider()
    st.header("How It Works")
    st.markdown("""
1. Upload your ESG CSV
2. Pipeline plans 12 GRI sections
3. LLaMA 3 generates each section
4. Validator checks all numbers
5. Word document assembled
6. Download your report
    """)

    st.divider()
    st.header("Sample CSVs")
    sample_dir = Path("data/sample_csvs")
    if sample_dir.exists():
        for csv_file in sorted(sample_dir.glob("*.csv")):
            with open(csv_file, "rb") as f:
                st.download_button(
                    label=f"⬇ {csv_file.name}",
                    data=f,
                    file_name=csv_file.name,
                    mime="text/csv",
                    key=csv_file.name,
                )

# ── Main upload area ───────────────────────────────────────────────────────────
st.subheader("Step 1 — Upload ESG Data CSV")
st.markdown(
    "Your CSV must contain at least: `company_name`, `reporting_year`, "
    "`scope1_emissions_tco2e`, `scope2_emissions_tco2e`. "
    "Download a sample CSV from the sidebar to see the full format."
)

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"],
    help="Wide format: one row of data, column headers are KPI names.",
)

if uploaded_file is not None:
    st.success(f"File uploaded: **{uploaded_file.name}**")

    st.divider()
    st.subheader("Step 2 — Generate Report")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            "Click **Generate** to run the full AI pipeline. "
            "This takes approximately **3–4 minutes**."
        )
    with col2:
        generate_clicked = st.button(
            "Generate Report",
            type="primary",
            use_container_width=True,
        )

    if generate_clicked:
        # ── Call the API ───────────────────────────────────────────
        progress = st.progress(0, text="Starting pipeline...")
        status   = st.empty()

        try:
            status.info("Sending CSV to backend...")
            progress.progress(10, text="Uploading CSV...")

            response = requests.post(
                GENERATE_ENDPOINT,
                files={"file": (uploaded_file.name, uploaded_file, "text/csv")},
                timeout=600,   # 10 min timeout — LLM pipeline is slow
            )

            progress.progress(90, text="Assembling document...")

            if response.status_code == 200:
                progress.progress(100, text="Done!")
                status.success("Report generated successfully!")

                st.divider()
                st.subheader("Step 3 — Download Report")

                # Extract filename from response headers if available
                content_disp = response.headers.get(
                    "content-disposition", ""
                )
                if "filename=" in content_disp:
                    filename = content_disp.split("filename=")[-1].strip('"')
                else:
                    filename = f"{uploaded_file.name.replace('.csv', '')}_sustainability_report.docx"

                st.download_button(
                    label="⬇ Download Sustainability Report (.docx)",
                    data=response.content,
                    file_name=filename,
                    mime=(
                        "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document"
                    ),
                    type="primary",
                    use_container_width=True,
                )

                # ── Validation summary ─────────────────────────────
                st.divider()
                st.subheader("Validation Summary")
                st.markdown(
                    "The report includes an automated validation appendix. "
                    "Numbers flagged below differ from source data by more than 5% "
                    "and should be reviewed before publication."
                )
                st.info(
                    "Open the downloaded .docx and check the "
                    "**Appendix: Validation Summary** on the final page."
                )

            else:
                progress.empty()
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text
                status.error(f"Generation failed: {detail}")

        except requests.exceptions.Timeout:
            progress.empty()
            status.error(
                "Request timed out after 10 minutes. "
                "The LLM pipeline may be overloaded. Please try again."
            )
        except requests.exceptions.ConnectionError:
            progress.empty()
            status.error(
                "Cannot connect to the backend API. "
                "Make sure the FastAPI server is running on port 8000."
            )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "AI-Assisted Draft — All figures must be verified against source data "
    "before external publication. "
    "Built with FastAPI · Streamlit · LangChain · Groq LLaMA 3."
)