"""
app/core/schema.py
───────────────────
GRI Standards + TCFD section schema.

Each ReportSection defines:
  - section_id      : short unique identifier
  - gri_code        : GRI Standard reference (e.g. "GRI 302-1")
  - tcfd_pillar     : TCFD pillar if applicable, else None
  - title           : human-readable section title
  - required_kpis   : CSV column names that MUST be present
  - optional_kpis   : CSV column names that enrich the section
  - prompt_focus    : one-line instruction to the LLM for this section
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ReportSection:
    section_id: str
    gri_code: str
    tcfd_pillar: Optional[str]
    title: str
    required_kpis: list[str]
    optional_kpis: list[str]
    prompt_focus: str



REPORT_SECTIONS: list[ReportSection] = [

    ReportSection(
        section_id="overview",
        gri_code="GRI 2-1",
        tcfd_pillar="Governance",
        title="Company Overview & Reporting Scope",
        required_kpis=[
            "company_name",
            "reporting_year",
            "industry_sector",
            "country_of_operation",
        ],
        optional_kpis=[
            "number_of_employees",
            "annual_revenue_usd",
            "number_of_sites",
        ],
        prompt_focus="Introduce the company, its industry, geographic presence, "
                     "and the scope and boundaries of this sustainability report.",
    ),

    ReportSection(
        section_id="governance",
        gri_code="GRI 2-9 / GRI 2-12",
        tcfd_pillar="Governance",
        title="Governance & Sustainability Leadership",
        required_kpis=[
            "board_size",
            "board_sustainability_committee",
        ],
        optional_kpis=[
            "female_board_members_pct",
            "independent_directors_pct",
            "ceo_pay_ratio",
            "sustainability_linked_exec_compensation",
        ],
        prompt_focus="Describe the board structure, oversight mechanisms for "
                     "sustainability, and how executive accountability for ESG "
                     "performance is embedded.",
    ),

    ReportSection(
        section_id="climate_strategy",
        gri_code="GRI 201-2",
        tcfd_pillar="Strategy",
        title="Climate Strategy & Risk Management",
        required_kpis=[
            "has_climate_targets",
            "net_zero_target_year",
        ],
        optional_kpis=[
            "physical_risk_exposure",
            "transition_risk_exposure",
            "climate_scenario_analysis",
            "carbon_price_assumption_usd",
        ],
        prompt_focus="Articulate the company's climate strategy, short/medium/long-term "
                     "targets, and how it identifies and manages physical and transition "
                     "climate risks per TCFD recommendations.",
    ),

    ReportSection(
        section_id="energy",
        gri_code="GRI 302-1 / GRI 302-4",
        tcfd_pillar="Metrics & Targets",
        title="Energy Consumption & Efficiency",
        required_kpis=[
            "total_energy_consumption_mwh",
            "renewable_energy_mwh",
            "reporting_year",
        ],
        optional_kpis=[
            "energy_intensity_per_revenue",
            "energy_reduction_vs_baseline_pct",
            "onsite_solar_mwh",
            "grid_electricity_mwh",
        ],
        prompt_focus="Report total energy consumption, renewable energy share, "
                     "year-on-year trends, and efficiency initiatives with "
                     "quantified impact.",
    ),

    ReportSection(
        section_id="emissions",
        gri_code="GRI 305-1 / GRI 305-2 / GRI 305-3",
        tcfd_pillar="Metrics & Targets",
        title="Greenhouse Gas Emissions",
        required_kpis=[
            "scope1_emissions_tco2e",
            "scope2_emissions_tco2e",
            "reporting_year",
        ],
        optional_kpis=[
            "scope3_emissions_tco2e",
            "emissions_intensity_per_revenue",
            "yoy_emissions_change_pct",
            "carbon_offset_tco2e",
            "ghg_protocol_methodology",
        ],
        prompt_focus="Disclose Scope 1, 2, and 3 GHG emissions, methodology, "
                     "intensity metrics, and progress against reduction targets "
                     "in line with GHG Protocol.",
    ),

    ReportSection(
        section_id="water",
        gri_code="GRI 303-1 / GRI 303-3",
        tcfd_pillar=None,
        title="Water Stewardship",
        required_kpis=[
            "total_water_withdrawal_m3",
        ],
        optional_kpis=[
            "water_recycled_m3",
            "water_intensity_per_revenue",
            "sites_in_water_stressed_areas",
            "water_reduction_target_pct",
        ],
        prompt_focus="Describe water withdrawal, consumption, recycling rates, "
                     "and stewardship programmes especially in water-stressed areas.",
    ),

    ReportSection(
        section_id="waste",
        gri_code="GRI 306-2 / GRI 306-3",
        tcfd_pillar=None,
        title="Waste Management & Circular Economy",
        required_kpis=[
            "total_waste_tonnes",
        ],
        optional_kpis=[
            "waste_recycled_tonnes",
            "waste_to_landfill_tonnes",
            "hazardous_waste_tonnes",
            "diversion_rate_pct",
            "circular_economy_initiatives",
        ],
        prompt_focus="Report total waste generation, diversion rates, hazardous "
                     "waste handling, and circular economy initiatives.",
    ),

    ReportSection(
        section_id="workforce",
        gri_code="GRI 2-7 / GRI 401-1 / GRI 405-1",
        tcfd_pillar=None,
        title="Workforce & Human Capital",
        required_kpis=[
            "number_of_employees",
            "female_employees_pct",
        ],
        optional_kpis=[
            "employee_turnover_rate_pct",
            "new_hires",
            "part_time_employees",
            "union_membership_pct",
            "avg_training_hours_per_employee",
        ],
        prompt_focus="Disclose workforce composition, diversity metrics, turnover, "
                     "hiring trends, and human capital development investments.",
    ),

    ReportSection(
        section_id="health_safety",
        gri_code="GRI 403-2 / GRI 403-9",
        tcfd_pillar=None,
        title="Occupational Health & Safety",
        required_kpis=[
            "total_recordable_injury_rate",
            "lost_time_injury_frequency_rate",
        ],
        optional_kpis=[
            "fatalities",
            "near_miss_incidents",
            "safety_training_hours",
            "occupational_illness_rate",
        ],
        prompt_focus="Present safety performance data including TRIR and LTIFR, "
                     "describe the safety management system, and highlight "
                     "improvement trends.",
    ),

    ReportSection(
        section_id="dei",
        gri_code="GRI 405-1 / GRI 406-1",
        tcfd_pillar=None,
        title="Diversity, Equity & Inclusion",
        required_kpis=[
            "female_employees_pct",
        ],
        optional_kpis=[
            "female_senior_managers_pct",
            "ethnically_diverse_employees_pct",
            "pay_gap_pct",
            "discrimination_incidents",
            "dei_programmes",
        ],
        prompt_focus="Report workforce diversity across gender and ethnicity, "
                     "pay equity status, anti-discrimination measures, and "
                     "DEI programme outcomes.",
    ),

    ReportSection(
        section_id="community_ethics",
        gri_code="GRI 205-1 / GRI 413-1",
        tcfd_pillar=None,
        title="Community Investment & Business Ethics",
        required_kpis=[
            "community_investment_usd",
        ],
        optional_kpis=[
            "volunteer_hours",
            "supplier_esg_assessments_pct",
            "corruption_incidents",
            "whistleblower_cases",
            "human_rights_assessments",
        ],
        prompt_focus="Detail community investment programmes, supplier ESG due "
                     "diligence, anti-corruption controls, and human rights "
                     "assessments.",
    ),

    ReportSection(
        section_id="targets_outlook",
        gri_code="GRI 2-29 / TCFD Metrics & Targets",
        tcfd_pillar="Metrics & Targets",
        title="Sustainability Targets & Forward Outlook",
        required_kpis=[
            "reporting_year",
        ],
        optional_kpis=[
            "net_zero_target_year",
            "renewable_energy_target_pct",
            "water_reduction_target_pct",
            "waste_diversion_target_pct",
            "science_based_targets",
        ],
        prompt_focus="Summarise all quantitative sustainability targets, progress "
                     "to date, science-based target commitments, and the company's "
                     "sustainability outlook.",
    ),
]



SECTION_MAP: dict[str, ReportSection] = {
    s.section_id: s for s in REPORT_SECTIONS
}

ALL_KNOWN_KPIS: set[str] = set()
for _s in REPORT_SECTIONS:
    ALL_KNOWN_KPIS.update(_s.required_kpis)
    ALL_KNOWN_KPIS.update(_s.optional_kpis)