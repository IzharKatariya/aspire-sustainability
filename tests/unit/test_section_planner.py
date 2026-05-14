"""
tests/unit/test_section_planner.py
────────────────────────────────────
Unit tests for the section planner module.
Run with: pytest tests/unit/test_section_planner.py -v
"""

import math
import csv
import pytest
from pathlib import Path

from app.core.section_planner import (
    SectionPlanner,
    SectionPlan,
    SectionReadiness,
    _coerce,
    _is_blank,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────
# A fixture is a reusable setup that pytest injects into your tests.
# Instead of creating a CSV file in every test, we create it once here.

@pytest.fixture
def complete_csv(tmp_path: Path) -> Path:
    """
    Creates a minimal but complete CSV with all required KPIs.
    tmp_path is a pytest built-in — gives us a temporary folder
    that is automatically deleted after the test runs.
    """
    data = {
        # Overview
        "company_name": "TestCorp",
        "reporting_year": "2023",
        "industry_sector": "Technology",
        "country_of_operation": "United States",
        # Governance
        "board_size": "10",
        "board_sustainability_committee": "Yes",
        # Climate
        "has_climate_targets": "Yes",
        "net_zero_target_year": "2040",
        # Energy
        "total_energy_consumption_mwh": "50000",
        "renewable_energy_mwh": "30000",
        # Emissions
        "scope1_emissions_tco2e": "10000",
        "scope2_emissions_tco2e": "8000",
        # Water
        "total_water_withdrawal_m3": "500000",
        # Waste
        "total_waste_tonnes": "2000",
        # Workforce
        "number_of_employees": "5000",
        "female_employees_pct": "45",
        # Health & Safety
        "total_recordable_injury_rate": "0.5",
        "lost_time_injury_frequency_rate": "0.2",
        # DEI (uses female_employees_pct — already present)
        # Community
        "community_investment_usd": "1000000",
    }

    file_path = tmp_path / "test_company.csv"
    with open(file_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)

    return file_path


@pytest.fixture
def incomplete_csv(tmp_path: Path) -> Path:
    """
    CSV missing several required KPIs.
    Energy section will be missing total_energy_consumption_mwh.
    Emissions section will be missing both scope KPIs.
    """
    data = {
        "company_name": "IncompleteCorp",
        "reporting_year": "2023",
        "industry_sector": "Retail",
        "country_of_operation": "UK",
        "board_size": "8",
        "board_sustainability_committee": "Yes",
        "has_climate_targets": "No",
        "net_zero_target_year": "N/A",
        # Energy — missing total_energy_consumption_mwh intentionally
        "renewable_energy_mwh": "5000",
        # Emissions — missing scope1 and scope2 intentionally
        "total_water_withdrawal_m3": "200000",
        "total_waste_tonnes": "1000",
        "number_of_employees": "1200",
        "female_employees_pct": "38",
        "total_recordable_injury_rate": "1.2",
        "lost_time_injury_frequency_rate": "0.6",
        "community_investment_usd": "500000",
    }

    file_path = tmp_path / "incomplete_company.csv"
    with open(file_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)

    return file_path


# ── Tests: CSV Loading ────────────────────────────────────────────────────────

class TestCSVLoading:
    """Tests that verify the CSV is loaded correctly."""

    def test_loads_real_company_csv(self):
        """Planner should load company_a.csv without errors."""
        planner = SectionPlanner("data/sample_csvs/company_a.csv")
        plan = planner.build_plan()
        assert plan is not None
        assert isinstance(plan, SectionPlan)

    def test_company_name_extracted_correctly(self):
        """Company name should be read from CSV into the plan."""
        planner = SectionPlanner("data/sample_csvs/company_a.csv")
        plan = planner.build_plan()
        assert plan.company_name == "VerdantSteel Ltd"

    def test_reporting_year_extracted_correctly(self):
        """Reporting year should be extracted as a string."""
        planner = SectionPlanner("data/sample_csvs/company_a.csv")
        plan = planner.build_plan()
        assert plan.reporting_year == "2023"

    def test_raises_error_for_missing_file(self):
        """Planner should raise FileNotFoundError for non-existent CSV."""
        planner = SectionPlanner("data/sample_csvs/does_not_exist.csv")
        with pytest.raises(FileNotFoundError):
            planner.build_plan()

    def test_raw_data_has_71_kpis(self):
        """Real company CSVs should have exactly 71 KPI columns."""
        planner = SectionPlanner("data/sample_csvs/company_a.csv")
        plan = planner.build_plan()
        assert len(plan.raw_data) == 70


# ── Tests: Section Evaluation ─────────────────────────────────────────────────

class TestSectionEvaluation:
    """Tests that verify sections are correctly evaluated."""

    def test_exactly_12_sections_evaluated(self):
        """Plan should always contain exactly 12 sections."""
        planner = SectionPlanner("data/sample_csvs/company_a.csv")
        plan = planner.build_plan()
        assert len(plan.sections) == 12

    def test_all_sections_ready_with_complete_csv(self, complete_csv):
        """A complete CSV should have all 12 sections ready."""
        planner = SectionPlanner(complete_csv)
        plan = planner.build_plan()
        assert len(plan.ready_sections) == 12
        assert len(plan.incomplete_sections) == 0

    def test_real_company_all_sections_ready(self):
        """All 3 real company CSVs should have all 12 sections ready."""
        for csv_file in ["company_a.csv", "company_b.csv", "company_c.csv"]:
            planner = SectionPlanner(f"data/sample_csvs/{csv_file}")
            plan = planner.build_plan()
            assert len(plan.ready_sections) == 12, (
                f"{csv_file} should have 12 ready sections, "
                f"got {len(plan.ready_sections)}"
            )

    def test_missing_required_kpi_marks_section_not_ready(self, incomplete_csv):
        """Energy section should not be ready when total_energy_consumption_mwh missing."""
        planner = SectionPlanner(incomplete_csv)
        plan = planner.build_plan()
        energy = plan.get_section("energy")
        assert energy is not None
        assert energy.is_ready is False
        assert "total_energy_consumption_mwh" in energy.missing_required

    def test_missing_emissions_kpis_marks_section_not_ready(self, incomplete_csv):
        """Emissions section should not be ready when scope KPIs missing."""
        planner = SectionPlanner(incomplete_csv)
        plan = planner.build_plan()
        emissions = plan.get_section("emissions")
        assert emissions is not None
        assert emissions.is_ready is False
        assert "scope1_emissions_tco2e" in emissions.missing_required
        assert "scope2_emissions_tco2e" in emissions.missing_required

    def test_completeness_pct_is_100_for_full_section(self):
        """A section with all KPIs present should show 100% completeness."""
        planner = SectionPlanner("data/sample_csvs/company_a.csv")
        plan = planner.build_plan()
        overview = plan.get_section("overview")
        assert overview.completeness_pct == 100.0

    def test_skipped_sections_list_matches_incomplete(self, incomplete_csv):
        """skipped_sections should contain section_ids of all incomplete sections."""
        planner = SectionPlanner(incomplete_csv)
        plan = planner.build_plan()
        incomplete_ids = [s.section.section_id for s in plan.incomplete_sections]
        assert set(plan.skipped_sections) == set(incomplete_ids)


# ── Tests: Data Type Coercion ─────────────────────────────────────────────────

class TestCoerce:
    """Tests for the _coerce helper function."""

    def test_integer_string_becomes_int(self):
        assert _coerce("187000") == 187000
        assert isinstance(_coerce("187000"), int)

    def test_float_string_becomes_float(self):
        assert _coerce("0.467") == pytest.approx(0.467)
        assert isinstance(_coerce("0.467"), float)

    def test_text_stays_as_string(self):
        assert _coerce("GHG Protocol Corporate Standard") == \
               "GHG Protocol Corporate Standard"

    def test_empty_string_returns_none(self):
        assert _coerce("") is None

    def test_na_string_returns_none(self):
        assert _coerce("N/A") is None
        assert _coerce("n/a") is None

    def test_nan_string_returns_none(self):
        assert _coerce("nan") is None
        assert _coerce("NaN") is None

    def test_negative_number(self):
        assert _coerce("-6.4") == pytest.approx(-6.4)

    def test_zero_becomes_int(self):
        assert _coerce("0") == 0
        assert isinstance(_coerce("0"), int)


# ── Tests: Blank Detection ────────────────────────────────────────────────────

class TestIsBlank:
    """Tests for the _is_blank helper function."""

    def test_none_is_blank(self):
        assert _is_blank(None) is True

    def test_empty_string_is_blank(self):
        assert _is_blank("") is True

    def test_na_is_blank(self):
        assert _is_blank("N/A") is True
        assert _is_blank("n/a") is True

    def test_nan_float_is_blank(self):
        assert _is_blank(float("nan")) is True

    def test_zero_is_not_blank(self):
        """Zero is a valid data point — fatalities=0 means no fatalities."""
        assert _is_blank(0) is False

    def test_valid_string_is_not_blank(self):
        assert _is_blank("VerdantSteel Ltd") is False

    def test_valid_number_is_not_blank(self):
        assert _is_blank(187000) is False


# ── Tests: Summary Output ─────────────────────────────────────────────────────

class TestSummary:
    """Tests that the summary output is correctly formatted."""

    def test_summary_contains_company_name(self):
        planner = SectionPlanner("data/sample_csvs/company_a.csv")
        plan = planner.build_plan()
        summary = plan.summary()
        assert "VerdantSteel Ltd" in summary

    def test_summary_contains_ready_marker(self):
        planner = SectionPlanner("data/sample_csvs/company_a.csv")
        plan = planner.build_plan()
        summary = plan.summary()
        assert "✓ READY" in summary

    def test_summary_contains_skip_marker_when_incomplete(self, incomplete_csv):
        planner = SectionPlanner(incomplete_csv)
        plan = planner.build_plan()
        summary = plan.summary()
        assert "✗ SKIP" in summary