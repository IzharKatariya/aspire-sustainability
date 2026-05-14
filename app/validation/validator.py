"""
app/validation/validator.py
────────────────────────────
Cross-checks LLM-generated section text against source CSV values.
Flags any number that cannot be matched to a source value within tolerance.
"""

import re
import math
from dataclasses import dataclass
from typing import Optional
from app.core.schema import ReportSection

# Numbers differing by less than this fraction are considered matching
VALIDATION_TOLERANCE = 0.05   # 5 %


# ── Result dataclasses ─────────────────────────────────────────────────────────

@dataclass
class FlaggedNumber:
    """One number in the LLM text that could not be matched to source data."""
    value: float
    raw_text: str
    context: str
    closest_source_value: Optional[float] = None
    closest_source_kpi: Optional[str] = None
    deviation_pct: Optional[float] = None


@dataclass
class SectionValidation:
    """Validation result for one report section."""
    section_id: str
    section_title: str
    source_values: dict[str, float]
    extracted_numbers: list[float]
    flagged: list[FlaggedNumber]
    passed: bool

    @property
    def flag_count(self) -> int:
        return len(self.flagged)


@dataclass
class ValidationReport:
    """Full validation result across all generated sections."""
    company_name: str
    reporting_year: str
    section_results: list[SectionValidation]
    total_numbers_checked: int
    total_flags: int
    overall_passed: bool

    def summary(self) -> str:
        lines = [
            f"Validation Report — {self.company_name} ({self.reporting_year})",
            f"Sections checked : {len(self.section_results)}",
            f"Numbers checked  : {self.total_numbers_checked}",
            f"Flags raised     : {self.total_flags}",
            f"Overall status   : {'PASS ✓' if self.overall_passed else 'REVIEW REQUIRED ⚠'}",
            "",
        ]
        for sr in self.section_results:
            if sr.flagged:
                lines.append(f"  [{sr.section_id}] {sr.flag_count} flag(s):")
                for f in sr.flagged:
                    lines.append(
                        f"    • '{f.raw_text}' not matched "
                        f"(closest: {f.closest_source_kpi}="
                        f"{f.closest_source_value}, "
                        f"Δ{f.deviation_pct:.1f}%)"
                    )
        return "\n".join(lines)


# ── Core helpers ───────────────────────────────────────────────────────────────

def _extract_numbers(text: str) -> list[tuple[float, str, str]]:
    """
    Return list of (float_value, raw_string, context_snippet) for every
    number found in text. Handles commas (1,200,000) and decimals.
    Skips single digits, small numbers, and 4-digit years.
    """
    pattern = re.compile(r'\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\b')
    results = []
    for match in pattern.finditer(text):
        raw = match.group()
        try:
            value = float(raw.replace(',', ''))
        except ValueError:
            continue
        # Skip trivially small numbers
        if value < 10:
            continue
        # Skip 4-digit years (1900–2100)
        if 1900 <= value <= 2100:
            continue
        # Skip GRI standard numbers (100–999 range that appear in GRI codes)
        if 100 <= value <= 999:
            continue
        # Context: 30 chars before and after
        start = max(0, match.start() - 30)
        end = min(len(text), match.end() + 30)
        context = text[start:end].replace('\n', ' ')
        results.append((value, raw, context))
    return results


def _build_source_pool(
    readiness,  # SectionReadiness object
) -> dict[str, float]:
    """
    Extract numeric values from SectionReadiness.available_kpis.
    Only includes KPIs whose names suggest a numeric measurement,
    to avoid string fields with accidentally numeric-looking values.
    """
    NUMERIC_HINTS = (
        "_mwh", "_tco2e", "_m3", "_usd", "_pct", "_rate",
        "_ratio", "_tonnes", "_hours", "_size",
        "_employees", "_hires", "_incidents", "_cases",
        "_intensity", "_offset", "_price",
        "number_of", "total_", "avg_", "yoy_",
    )
    pool: dict[str, float] = {}
    for kpi, raw in readiness.available_kpis.items():
        if raw is None:
            continue
        if not any(hint in kpi for hint in NUMERIC_HINTS):
            continue
        try:
            val = float(str(raw).replace(',', ''))
            if not math.isnan(val):
                pool[kpi] = val
        except (ValueError, TypeError):
            continue
    return pool


def _find_closest(
    value: float,
    pool: dict[str, float],
) -> tuple[Optional[str], Optional[float], Optional[float]]:
    """
    Find the closest source value to `value` in the pool.
    Returns (kpi_name, source_value, deviation_pct).
    Returns (None, None, None) if pool is empty.
    """
    if not pool:
        return None, None, None

    best_kpi = None
    best_val = None
    best_dev = float('inf')

    for kpi, src in pool.items():
        if src == 0:
            continue
        dev = abs(value - src) / abs(src)
        if dev < best_dev:
            best_dev = dev
            best_kpi = kpi
            best_val = src

    return best_kpi, best_val, best_dev * 100


def _is_matched(value: float, pool: dict[str, float]) -> bool:
    """True if value is within VALIDATION_TOLERANCE of any pool entry."""
    for src in pool.values():
        if src == 0:
            continue
        if abs(value - src) / abs(src) <= VALIDATION_TOLERANCE:
            return True
    return False


# ── Main validator ─────────────────────────────────────────────────────────────

def validate_section(
    section: ReportSection,
    readiness,  # SectionReadiness object
    generated_text: str,
) -> SectionValidation:
    """Validate one section's generated text against its source data."""

    source_pool = _build_source_pool(readiness)
    extracted = _extract_numbers(generated_text)
    flagged: list[FlaggedNumber] = []

    for value, raw, context in extracted:
        if not _is_matched(value, source_pool):
            closest_kpi, closest_val, dev_pct = _find_closest(value, source_pool)
            flagged.append(FlaggedNumber(
                value=value,
                raw_text=raw,
                context=context,
                closest_source_value=closest_val,
                closest_source_kpi=closest_kpi,
                deviation_pct=dev_pct,
            ))

    return SectionValidation(
        section_id=section.section_id,
        section_title=section.title,
        source_values=source_pool,
        extracted_numbers=[v for v, _, _ in extracted],
        flagged=flagged,
        passed=len(flagged) == 0,
    )


def validate_report(
    generated_report,
    section_plan,       # SectionPlan object from SectionPlanner
    company_name: str,
    reporting_year: str,
) -> ValidationReport:
    """
    Run validation across all generated sections.

    Args:
        generated_report : GeneratedReport object from pipeline.py
        section_plan     : SectionPlan from SectionPlanner.build_plan()
        company_name     : from CSV
        reporting_year   : from CSV
    """
    from app.core.schema import SECTION_MAP

    # Build lookup: section_id -> SectionReadiness
    readiness_map = {
        sr.section.section_id: sr
        for sr in section_plan.sections
    }

    section_results: list[SectionValidation] = []
    total_numbers = 0
    total_flags = 0

    for section_id, text in generated_report.sections.items():
        if not text or section_id not in SECTION_MAP:
            continue
        section = SECTION_MAP[section_id]
        readiness = readiness_map.get(section_id)
        if readiness is None:
            continue

        result = validate_section(section, readiness, text)
        section_results.append(result)
        total_numbers += len(result.extracted_numbers)
        total_flags += result.flag_count

    return ValidationReport(
        company_name=company_name,
        reporting_year=str(reporting_year),
        section_results=section_results,
        total_numbers_checked=total_numbers,
        total_flags=total_flags,
        overall_passed=total_flags == 0,
    )