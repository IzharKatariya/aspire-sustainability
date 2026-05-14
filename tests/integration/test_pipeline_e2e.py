"""
tests/integration/test_pipeline_e2e.py
────────────────────────────────────────
End-to-end integration tests for the full report generation pipeline.

Uses mocked LLM calls for speed and cost efficiency.
Run with: pytest tests/integration/test_pipeline_e2e.py -v

To run the live API test (slow, uses Groq credits):
  pytest tests/integration/test_pipeline_e2e.py -v -m live
"""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.section_planner import SectionPlanner
from app.llm.pipeline import LLMPipeline, GeneratedReport
from app.validation.validator import validate_report
from app.document.assembler import assemble_report


# ── Fixtures ───────────────────────────────────────────────────────────────────

CSV_DIR = Path("data/sample_csvs")

COMPANY_CSVS = [
    ("company_a.csv", "VerdantSteel Ltd",       "2023"),
    ("company_b.csv", "NovaMind Technologies",  "2023"),
    ("company_c.csv", "SolBridge Energy",       "2023"),
]

# Realistic mock text returned instead of real LLM output
MOCK_SECTION_TEXT = (
    "This section presents the company's performance data for the reporting year. "
    "The figures disclosed have been verified against source data and are presented "
    "in accordance with GRI Standards. The company remains committed to continuous "
    "improvement across all sustainability dimensions."
)


def _make_mock_generated_report(plan, section_ids: list[str]) -> GeneratedReport:
    """Build a GeneratedReport with mock text for all ready sections."""
    report = GeneratedReport(
        company_name=plan.company_name,
        reporting_year=plan.reporting_year,
    )
    report.skipped = plan.skipped_sections.copy()
    for section_id in section_ids:
        report.sections[section_id] = MOCK_SECTION_TEXT
    return report


# ── Section Planner Tests ──────────────────────────────────────────────────────

class TestSectionPlanner:

    @pytest.mark.parametrize("csv_file,company_name,year", COMPANY_CSVS)
    def test_plan_loads_correctly(self, csv_file, company_name, year):
        """Each CSV should load and produce a valid SectionPlan."""
        planner = SectionPlanner(CSV_DIR / csv_file)
        plan = planner.build_plan()

        assert plan.company_name == company_name
        assert plan.reporting_year == year
        assert len(plan.sections) == 12

    @pytest.mark.parametrize("csv_file,company_name,year", COMPANY_CSVS)
    def test_all_sections_ready(self, csv_file, company_name, year):
        """All 12 sections should be ready for all 3 companies."""
        planner = SectionPlanner(CSV_DIR / csv_file)
        plan = planner.build_plan()

        assert len(plan.ready_sections) == 12, (
            f"{company_name}: expected 12 ready sections, "
            f"got {len(plan.ready_sections)}. "
            f"Skipped: {plan.skipped_sections}"
        )

    @pytest.mark.parametrize("csv_file,company_name,year", COMPANY_CSVS)
    def test_raw_data_has_required_keys(self, csv_file, company_name, year):
        """Each plan must contain the core identity KPIs."""
        planner = SectionPlanner(CSV_DIR / csv_file)
        plan = planner.build_plan()

        required_keys = [
            "company_name", "reporting_year",
            "industry_sector", "scope1_emissions_tco2e",
        ]
        for key in required_keys:
            assert key in plan.raw_data, (
                f"{company_name}: missing required key '{key}'"
            )


# ── Generated Report Tests ─────────────────────────────────────────────────────

class TestGeneratedReport:

    @pytest.mark.parametrize("csv_file,company_name,year", COMPANY_CSVS)
    def test_mock_report_has_all_sections(self, csv_file, company_name, year):
        """Mock pipeline should produce 12 non-empty sections."""
        planner = SectionPlanner(CSV_DIR / csv_file)
        plan = planner.build_plan()

        section_ids = [sr.section.section_id for sr in plan.ready_sections]
        report = _make_mock_generated_report(plan, section_ids)

        assert len(report.sections) == 12
        for sid, text in report.sections.items():
            assert text, f"Section '{sid}' is empty"
            assert len(text) > 50, f"Section '{sid}' is too short"

    @pytest.mark.parametrize("csv_file,company_name,year", COMPANY_CSVS)
    def test_mock_report_metadata(self, csv_file, company_name, year):
        """Generated report must carry correct company metadata."""
        planner = SectionPlanner(CSV_DIR / csv_file)
        plan = planner.build_plan()

        section_ids = [sr.section.section_id for sr in plan.ready_sections]
        report = _make_mock_generated_report(plan, section_ids)

        assert report.company_name == company_name
        assert report.reporting_year == year


# ── Validator Tests ────────────────────────────────────────────────────────────

class TestValidator:

    @pytest.mark.parametrize("csv_file,company_name,year", COMPANY_CSVS)
    def test_validation_runs_without_error(self, csv_file, company_name, year):
        """Validator should run cleanly on mock-generated text."""
        planner = SectionPlanner(CSV_DIR / csv_file)
        plan = planner.build_plan()

        section_ids = [sr.section.section_id for sr in plan.ready_sections]
        report = _make_mock_generated_report(plan, section_ids)

        val = validate_report(
            generated_report=report,
            section_plan=plan,
            company_name=plan.company_name,
            reporting_year=plan.reporting_year,
        )

        assert val.company_name == company_name
        assert len(val.section_results) == 12
        assert val.total_numbers_checked >= 0

    def test_validator_catches_hallucination(self):
        """Validator must flag a clearly wrong number."""
        from app.core.schema import SECTION_MAP
        from app.validation.validator import validate_section

        planner = SectionPlanner(CSV_DIR / "company_a.csv")
        plan = planner.build_plan()
        readiness = plan.get_section("emissions")
        section = SECTION_MAP["emissions"]

        bad_text = (
            "The company reported Scope 1 emissions of 999,999 tCO2e "
            "and Scope 2 emissions of 888,888 tCO2e."
        )
        result = validate_section(section, readiness, bad_text)
        assert result.flag_count >= 1, "Hallucinated numbers should be flagged"
        assert not result.passed

    def test_validator_passes_correct_numbers(self):
        """Validator must not flag numbers that match source data."""
        from app.core.schema import SECTION_MAP
        from app.validation.validator import validate_section

        planner = SectionPlanner(CSV_DIR / "company_a.csv")
        plan = planner.build_plan()
        readiness = plan.get_section("emissions")
        section = SECTION_MAP["emissions"]

        good_text = (
            "Scope 1 emissions totalled 187,000 tCO2e "
            "and Scope 2 emissions were 54,000 tCO2e."
        )
        result = validate_section(section, readiness, good_text)
        assert result.passed, f"Correct numbers flagged: {result.flagged}"


# ── Document Assembler Tests ───────────────────────────────────────────────────

class TestDocumentAssembler:

    @pytest.mark.parametrize("csv_file,company_name,year", COMPANY_CSVS)
    def test_docx_is_created(self, csv_file, company_name, year, tmp_path):
        """Assembler should create a non-empty .docx file."""
        planner = SectionPlanner(CSV_DIR / csv_file)
        plan = planner.build_plan()

        section_ids = [sr.section.section_id for sr in plan.ready_sections]
        report = _make_mock_generated_report(plan, section_ids)

        val = validate_report(
            generated_report=report,
            section_plan=plan,
            company_name=plan.company_name,
            reporting_year=plan.reporting_year,
        )

        output_path = tmp_path / f"{company_name}_test.docx"
        result = assemble_report(report, val, plan, output_path=output_path)

        assert result.exists(), "Output .docx file was not created"
        assert result.stat().st_size > 5000, "Output .docx is suspiciously small"

    @pytest.mark.parametrize("csv_file,company_name,year", COMPANY_CSVS)
    def test_docx_filename_contains_company(self, csv_file, company_name, year, tmp_path):
        """Default output filename should include company name."""
        planner = SectionPlanner(CSV_DIR / csv_file)
        plan = planner.build_plan()

        section_ids = [sr.section.section_id for sr in plan.ready_sections]
        report = _make_mock_generated_report(plan, section_ids)

        val = validate_report(
            generated_report=report,
            section_plan=plan,
            company_name=plan.company_name,
            reporting_year=plan.reporting_year,
        )

        output_path = tmp_path / f"test_{csv_file}.docx"
        result = assemble_report(report, val, plan, output_path=output_path)
        assert result.exists()


# ── Live API Test (manual only) ────────────────────────────────────────────────

@pytest.mark.live
def test_live_pipeline_company_a(tmp_path):
    """
    Full live pipeline test using real Groq API.
    Run manually with: pytest tests/integration/test_pipeline_e2e.py -m live -v
    Takes ~3 minutes.
    """
    planner = SectionPlanner(CSV_DIR / "company_a.csv")
    plan = planner.build_plan()

    assert len(plan.ready_sections) == 12

    pipeline = LLMPipeline()
    generated = pipeline.run(plan)

    assert len(generated.sections) == 12
    total_words = sum(
        len(text.split())
        for text in generated.sections.values()
    )
    assert total_words >= 2000, f"Total words too low: {total_words}"

    val = validate_report(
        generated_report=generated,
        section_plan=plan,
        company_name=plan.company_name,
        reporting_year=plan.reporting_year,
    )

    output = assemble_report(
        generated, val, plan,
        output_path=tmp_path / "live_test_output.docx"
    )
    assert output.exists()
    print(f"\nLive test passed. Output: {output}")
    print(val.summary())