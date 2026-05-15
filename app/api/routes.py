"""
app/api/routes.py
──────────────────
FastAPI route definitions for the report generation API.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.section_planner import SectionPlanner
from app.llm.pipeline import LLMPipeline
from app.validation.validator import validate_report
from app.document.assembler import assemble_report

router = APIRouter()


@router.get("/health")
def health_check():
    """Simple liveness check — confirms the API is running."""
    return {"status": "ok", "service": "ASPIRE"}


@router.post("/generate")
async def generate_report(file: UploadFile = File(...)):
    """
    Accept a CSV file upload and return a generated .docx report.

    Flow:
      1. Save uploaded CSV to temp/
      2. Run SectionPlanner
      3. Run LLMPipeline
      4. Run Validator
      5. Assemble .docx
      6. Return file download
      7. Clean up temp file
    """
    # ── Validate file type ─────────────────────────────────────────
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only .csv files are accepted.",
        )

    # ── Save upload to temp directory ──────────────────────────────
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    temp_csv = settings.temp_dir / f"{uuid.uuid4().hex}.csv"

    try:
        with temp_csv.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        # ── Run pipeline ───────────────────────────────────────────
        try:
            planner = SectionPlanner(temp_csv)
            plan = planner.build_plan()
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"CSV parsing failed: {str(e)}",
            )

        if len(plan.ready_sections) == 0:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No sections could be generated — "
                    "CSV is missing too many required KPIs. "
                    f"Skipped: {plan.skipped_sections}"
                ),
            )

        try:
            pipeline = LLMPipeline()
            generated = pipeline.run(plan)
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"LLM pipeline failed: {str(e)}",
            )

        val_report = validate_report(
            generated_report=generated,
            section_plan=plan,
            company_name=plan.company_name,
            reporting_year=plan.reporting_year,
        )

        # ── Assemble document ──────────────────────────────────────
        output_path = assemble_report(generated, val_report, plan)

        # ── Return file ────────────────────────────────────────────
        return FileResponse(
            path=str(output_path),
            media_type=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
            filename=output_path.name,
        )

    finally:
        # Always clean up the temp CSV
        if temp_csv.exists():
            temp_csv.unlink()