"""
app/core/section_planner.py
────────────────────────────
Reads a company CSV, maps available KPIs to GRI sections,
and returns a SectionPlan that all downstream modules consume.

Usage:
    from app.core.section_planner import SectionPlanner
    planner = SectionPlanner("data/sample_csvs/company_a.csv")
    plan = planner.build_plan()
    print(plan.summary())
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from app.core.schema import REPORT_SECTIONS, ReportSection



@dataclass
class SectionReadiness:
    """Readiness state for one report section."""
    section: ReportSection
    available_kpis: dict[str, Any]      # kpi_name → value from CSV
    missing_required: list[str]         # required KPIs absent from CSV
    missing_optional: list[str]         # optional KPIs absent from CSV
    is_ready: bool                      # True if all required KPIs present
    completeness_pct: float             # (present / total) × 100


@dataclass
class SectionPlan:
    """Full plan built from one company CSV."""
    company_name: str
    reporting_year: str
    raw_data: dict[str, Any]            # all CSV key-value pairs
    sections: list[SectionReadiness]
    skipped_sections: list[str]         # section_ids skipped


    @property
    def ready_sections(self) -> list[SectionReadiness]:
        return [s for s in self.sections if s.is_ready]

    @property
    def incomplete_sections(self) -> list[SectionReadiness]:
        return [s for s in self.sections if not s.is_ready]

    def get_section(self, section_id: str) -> Optional[SectionReadiness]:
        for sr in self.sections:
            if sr.section.section_id == section_id:
                return sr
        return None

    def summary(self) -> str:
        lines = [
            f"{'='*60}",
            f"  Section Plan: {self.company_name} ({self.reporting_year})",
            f"{'='*60}",
            f"  Total sections : {len(self.sections)}",
            f"  Ready          : {len(self.ready_sections)}",
            f"  Incomplete     : {len(self.incomplete_sections)}",
            f"  CSV KPIs found : {len(self.raw_data)}",
            f"{'─'*60}",
        ]
        for sr in self.sections:
            status = "✓ READY" if sr.is_ready else "✗ SKIP "
            lines.append(
                f"  [{status}] {sr.section.title} "
                f"({sr.completeness_pct:.0f}% complete)"
            )
            if sr.missing_required:
                lines.append(
                    f"           Missing required: "
                    f"{', '.join(sr.missing_required)}"
                )
        lines.append(f"{'='*60}")
        return "\n".join(lines)



class SectionPlanner:
    """
    Parses a company CSV and maps columns to GRI section readiness.

    Accepts two CSV layouts:
    1. Wide format  — column headers are KPI names, one data row
    2. Vertical format — two columns: kpi_name, value
    """

    def __init__(self, csv_path: str | Path) -> None:
        self.csv_path = Path(csv_path)
        self._raw: dict[str, Any] = {}

    def build_plan(self) -> SectionPlan:
        """Main entry point. Returns a complete SectionPlan."""
        self._raw = self._load_csv()

        readiness_list: list[SectionReadiness] = []
        skipped: list[str] = []

        for section in REPORT_SECTIONS:
            sr = self._evaluate_section(section)
            readiness_list.append(sr)
            if not sr.is_ready:
                skipped.append(section.section_id)

        company_name = str(self._raw.get("company_name", "Unknown Company"))
        reporting_year = str(self._raw.get("reporting_year", "N/A"))

        return SectionPlan(
            company_name=company_name,
            reporting_year=reporting_year,
            raw_data=self._raw,
            sections=readiness_list,
            skipped_sections=skipped,
        )


    def _load_csv(self) -> dict[str, Any]:
        """Load CSV and return flat key-value dictionary."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")

        df = pd.read_csv(self.csv_path, dtype=str)

        # Normalise column names
        df.columns = [
            c.strip().lower().replace(" ", "_")
            for c in df.columns
        ]

        # Detect layout
        if "kpi_name" in df.columns and "value" in df.columns:
            return self._parse_vertical(df)
        else:
            return self._parse_wide(df)

    @staticmethod
    def _parse_wide(df: pd.DataFrame) -> dict[str, Any]:
        """Wide format — headers are KPI names, first row is values."""
        if df.empty:
            return {}
        row = df.iloc[0]
        return {col: _coerce(str(row[col]).strip()) for col in df.columns}

    @staticmethod
    def _parse_vertical(df: pd.DataFrame) -> dict[str, Any]:
        """Vertical format — two columns: kpi_name, value."""
        result: dict[str, Any] = {}
        for _, row in df.iterrows():
            key = str(row["kpi_name"]).strip().lower().replace(" ", "_")
            result[key] = _coerce(str(row["value"]).strip())
        return result

    def _evaluate_section(self, section: ReportSection) -> SectionReadiness:
        """Check which KPIs are present/missing for one section."""
        available: dict[str, Any] = {}
        missing_required: list[str] = []
        missing_optional: list[str] = []

        for kpi in section.required_kpis:
            if kpi in self._raw and not _is_blank(self._raw[kpi]):
                available[kpi] = self._raw[kpi]
            else:
                missing_required.append(kpi)

        for kpi in section.optional_kpis:
            if kpi in self._raw and not _is_blank(self._raw[kpi]):
                available[kpi] = self._raw[kpi]
            else:
                missing_optional.append(kpi)

        total = len(section.required_kpis) + len(section.optional_kpis) or 1
        completeness = (len(available) / total) * 100
        is_ready = len(missing_required) == 0

        return SectionReadiness(
            section=section,
            available_kpis=available,
            missing_required=missing_required,
            missing_optional=missing_optional,
            is_ready=is_ready,
            completeness_pct=completeness,
        )



def _coerce(value: str) -> Any:
    """Try to cast string to int, then float, else keep as string."""
    if value in ("", "nan", "NaN", "None", "N/A", "n/a", "none"):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        f = float(value)
        return None if math.isnan(f) else f
    except ValueError:
        pass
    return value


def _is_blank(value: Any) -> bool:
    """Return True if value is empty, None, or NaN."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() in (
        "", "nan", "None", "N/A", "n/a", "none"
    ):
        return True
    return False