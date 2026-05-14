"""
app/llm/prompts.py
───────────────────
Builds system and user prompts for each report section.

The system prompt stays constant across all 12 sections.
The user prompt is built fresh for each section using the
section's KPI data and focus instruction from the schema.
"""

from app.core.section_planner import SectionReadiness


# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior sustainability consultant and professional \
report writer with deep expertise in GRI Standards, TCFD framework, and ESG \
disclosure best practices.

Your task is to write one section of a formal corporate sustainability report.

RULES YOU MUST FOLLOW:
1. Write in formal, professional third-person language suitable for a \
published sustainability report.
2. Use ONLY the data provided in the user prompt. Do not invent, estimate, \
or assume any numbers not explicitly given.
3. Every numeric claim must come directly from the provided KPI data.
4. Pay close attention to the units provided next to each data point. \
A value labelled (year) is a year, not a quantity. \
A value labelled (USD per tonne CO2) is a price, not a total amount.
5. Structure your response with clear paragraphs. Do not use bullet points \
or headers — write in flowing prose.
6. Length: 200-350 words. Concise but substantive.
7. End with one forward-looking sentence about the company's commitment or \
next steps.
8. Do not include the section title in your response — it will be added \
separately.
"""


# ── Unit Hints ────────────────────────────────────────────────────────────────
# Adds context to each KPI so the LLM understands what the number means.

UNIT_HINTS: dict[str, str] = {
    "carbon_price_assumption_usd": "(USD per tonne CO2)",
    "total_energy_consumption_mwh": "(MWh)",
    "renewable_energy_mwh": "(MWh)",
    "onsite_solar_mwh": "(MWh)",
    "grid_electricity_mwh": "(MWh)",
    "scope1_emissions_tco2e": "(tonnes CO2 equivalent)",
    "scope2_emissions_tco2e": "(tonnes CO2 equivalent)",
    "scope3_emissions_tco2e": "(tonnes CO2 equivalent)",
    "carbon_offset_tco2e": "(tonnes CO2 equivalent)",
    "total_water_withdrawal_m3": "(cubic metres)",
    "water_recycled_m3": "(cubic metres)",
    "total_waste_tonnes": "(tonnes)",
    "waste_recycled_tonnes": "(tonnes)",
    "waste_to_landfill_tonnes": "(tonnes)",
    "hazardous_waste_tonnes": "(tonnes)",
    "community_investment_usd": "(USD)",
    "annual_revenue_usd": "(USD)",
    "net_zero_target_year": "(year)",
    "reporting_year": "(year)",
    "safety_training_hours": "(hours)",
    "avg_training_hours_per_employee": "(hours per employee)",
    "number_of_employees": "(people)",
    "new_hires": "(people)",
    "part_time_employees": "(people)",
    "board_size": "(people)",
    "volunteer_hours": "(hours)",
    "near_miss_incidents": "(incidents)",
    "discrimination_incidents": "(incidents)",
    "whistleblower_cases": "(cases)",
    "number_of_sites": "(sites)",
    "fatalities": "(fatalities)",
}


# ── User Prompt Builder ───────────────────────────────────────────────────────

def build_user_prompt(
    section_readiness: SectionReadiness,
    company_name: str,
    reporting_year: str,
) -> str:
    """
    Builds the user prompt for one report section.
    """
    section = section_readiness.section
    kpi_data = section_readiness.available_kpis
    kpi_lines = _format_kpis(kpi_data)

    prompt = f"""Write the "{section.title}" section for {company_name}'s \
{reporting_year} Sustainability Report.

GRI Reference: {section.gri_code}
{"TCFD Pillar: " + section.tcfd_pillar if section.tcfd_pillar else ""}

SECTION FOCUS:
{section.prompt_focus}

COMPANY DATA FOR THIS SECTION:
{kpi_lines}

Write this section now in formal sustainability report prose (200-350 words).
Use only the data provided above. Every number you mention must appear
in the data above. Pay close attention to the unit labels — they tell you
exactly what each number represents.
"""
    return prompt.strip()


def build_messages(
    section_readiness: SectionReadiness,
    company_name: str,
    reporting_year: str,
) -> list[dict]:
    """
    Returns the messages list in OpenAI/Groq chat format.
    """
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(
                section_readiness, company_name, reporting_year
            ),
        },
    ]


# ── Helper ────────────────────────────────────────────────────────────────────

def _format_kpis(kpi_data: dict) -> str:
    """
    Formats a KPI dictionary into clean readable lines with unit hints.

    Input:  {"scope1_emissions_tco2e": 187000, "net_zero_target_year": 2045}
    Output:   Scope1 Emissions Tco2E (tonnes CO2 equivalent): 187,000
              Net Zero Target Year (year): 2045
    """
    lines = []
    for key, value in kpi_data.items():
        if isinstance(value, int):
            if 1900 <= value <= 2100:
                formatted = str(value)
            else:
                formatted = f"{value:,}"
        elif isinstance(value, float):
            formatted = f"{value:,.3f}".rstrip("0").rstrip(".")
        else:
            formatted = str(value)

        label = key.replace("_", " ").title()
        unit = UNIT_HINTS.get(key, "")
        hint = f" {unit}" if unit else ""
        lines.append(f"  {label}{hint}: {formatted}")

    return "\n".join(lines)