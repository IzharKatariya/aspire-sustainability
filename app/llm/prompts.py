"""
app/llm/prompts.py
───────────────────
Builds system and user prompts for each report section.

The system prompt stays constant across all 12 sections.
The user prompt is built fresh for each section using the
section's KPI data and focus instruction from the schema.

Day 5 improvements:
  - Red-flag materiality framing for critical ESG incidents
  - Graceful handling of missing targets / sparse optional KPIs
  - Section-specific tone guidance
  - Updated unit hints to match current schema column names
  - Stronger anti-hallucination rules
"""

from app.core.section_planner import SectionReadiness


# ── Red-flag thresholds ────────────────────────────────────────────────────────
# If any of these KPIs breach their threshold, the LLM is instructed to
# apply materiality language and urgency framing in that section.

RED_FLAG_RULES: list[dict] = [
    {
        "kpi": "fatalities",
        "condition": lambda v: isinstance(v, (int, float)) and v > 0,
        "instruction": (
            "CRITICAL: The data includes {value} work-related fatality/fatalities. "
            "You MUST treat this as a material safety event. Use formal, sober language. "
            "Acknowledge the incident directly, state the company's commitment to "
            "investigation and corrective action, and avoid euphemisms. Do not minimise "
            "or bury this figure."
        ),
    },
    {
        "kpi": "work_related_injuries",
        "condition": lambda v: isinstance(v, (int, float)) and v > 15,
        "instruction": (
            "NOTE: The injury count of {value} is elevated. Frame this with appropriate "
            "materiality — acknowledge the figure honestly, describe the safety management "
            "response, and commit to improvement targets."
        ),
    },
    {
        "kpi": "employee_turnover_pct",
        "condition": lambda v: isinstance(v, (int, float)) and v > 25,
        "instruction": (
            "NOTE: Employee turnover of {value}% is significantly above industry norms. "
            "Disclose this figure transparently, acknowledge it as a workforce retention "
            "challenge, and reference any initiatives the company is undertaking to "
            "address root causes."
        ),
    },
    {
        "kpi": "data_breaches",
        "condition": lambda v: isinstance(v, (int, float)) and v > 0,
        "instruction": (
            "IMPORTANT: {value} data breach(es) occurred during the reporting period. "
            "Per GRI 418-1, this must be disclosed clearly. State the number of breaches, "
            "confirm the company has taken remedial action, and describe measures to "
            "prevent recurrence. Do not downplay."
        ),
    },
    {
        "kpi": "renewable_energy_pct",
        "condition": lambda v: isinstance(v, (int, float)) and v < 15,
        "instruction": (
            "NOTE: Renewable energy share of {value}% is low. Report this figure "
            "accurately without greenwashing. Acknowledge the gap and, if no targets "
            "exist in the data, state that the company is working to establish renewable "
            "energy targets."
        ),
    },
    {
        "kpi": "suppliers_with_code_of_conduct_pct",
        "condition": lambda v: isinstance(v, (int, float)) and v < 60,
        "instruction": (
            "NOTE: Only {value}% of suppliers have adopted a code of conduct. "
            "Disclose this gap honestly and describe the company's supplier engagement "
            "programme to improve this figure."
        ),
    },
]


# ── Section-specific tone guidance ─────────────────────────────────────────────

SECTION_TONE: dict[str, str] = {
    "overview": (
        "Set a professional, factual tone. Introduce the company concisely. "
        "Do not make unsubstantiated claims about sustainability leadership."
    ),
    "governance": (
        "Be precise about board composition figures. Report the CEO pay ratio "
        "factually without editorial comment. Note gaps in governance data if present."
    ),
    "climate_strategy": (
        "Apply TCFD framing. If no formal climate targets exist in the data, "
        "explicitly state that the company has not yet set formal targets and "
        "recommend this as a priority — do not invent targets."
    ),
    "energy": (
        "Report consumption and renewables share accurately. If renewable percentage "
        "is low, note it without greenwashing. If no year-on-year data is available, "
        "say so rather than implying trends."
    ),
    "emissions": (
        "Follow GHG Protocol structure: Scope 1, then 2, then 3. "
        "If intensity metrics are absent, note they will be developed. "
        "Do not invent reduction percentages."
    ),
    "water": (
        "Report withdrawal volumes and recycling rates precisely. "
        "If water stress data is absent, acknowledge the gap and recommend "
        "a water stress assessment as a next step."
    ),
    "waste": (
        "Report total waste, recycling rate, and hazardous waste tonnage clearly. "
        "Calculate diversion rate from available data if possible. "
        "Be honest if circular economy initiatives are nascent or unquantified."
    ),
    "workforce": (
        "Report headcount, gender split, turnover, and training hours factually. "
        "If turnover is high, acknowledge it as a retention challenge. "
        "Do not present aspirational diversity language unsupported by data."
    ),
    "health_safety": (
        "Safety data is material. Report all figures — injuries, fatalities — "
        "with full transparency. A fatality must be acknowledged directly and soberly. "
        "Never minimise safety incidents."
    ),
    "dei": (
        "Report diversity figures factually. Acknowledge gaps between current state "
        "and best practice. Do not make DEI claims that go beyond the data provided."
    ),
    "community_ethics": (
        "Disclose community investment, supplier compliance, and any data breaches "
        "transparently. Data breaches must be explicitly disclosed per GRI 418-1."
    ),
    "targets_outlook": (
        "IMPORTANT: Only state targets that are explicitly present in the data. "
        "If no formal targets exist, clearly state: 'As of the reporting period, "
        "the company has not yet formalised quantitative sustainability targets. "
        "Establishing science-based targets is identified as a priority for the "
        "forthcoming period.' Do not invent target years or percentages."
    ),
}


# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior sustainability consultant and professional \
report writer with deep expertise in GRI Standards, TCFD framework, and ESG \
disclosure best practices.

Your task is to write one section of a formal corporate sustainability report \
that will be reviewed by auditors, investors, and regulators.

RULES — FOLLOW ALL OF THESE WITHOUT EXCEPTION:

1. ACCURACY ABOVE ALL: Use ONLY the data provided in the user prompt. \
Do not invent, estimate, interpolate, or assume any numbers not explicitly given. \
If a data point is missing, say it is not available — never fabricate it.

2. UNITS: Pay close attention to the unit label next to each KPI. \
A value labelled (year) is a calendar year. \
A value labelled (%) is a percentage. \
A value labelled (tonnes CO2 equivalent) is an emissions figure. \
Never confuse units.

3. MATERIALITY: If the section instructions flag a CRITICAL or IMPORTANT note, \
you MUST address it prominently and with appropriate seriousness. \
Do not bury material incidents in subordinate clauses.

4. MISSING DATA: If optional KPIs are absent, do not pad with vague language. \
Instead, briefly note that the relevant metric will be developed or disclosed \
in future reporting periods.

5. NO GREENWASHING: Do not frame weak performance positively. \
Report figures as they are. A low renewable energy share is low — say so.

6. FORMAT: Write in formal, professional third-person prose with clear paragraphs. \
No bullet points, no headers, no markdown. \
Length: 200–350 words. \
Do not include the section title in your response.

7. FORWARD LOOK: End with one specific, grounded forward-looking sentence. \
It must be consistent with the data — no aspirational claims unsupported by evidence.
"""


# ── Unit hints (aligned to current schema column names) ───────────────────────

UNIT_HINTS: dict[str, str] = {
    # Energy
    "energy_consumption_mwh":           "(MWh)",
    "renewable_energy_pct":             "(% of total energy)",
    "onsite_solar_mwh":                 "(MWh)",
    "grid_electricity_mwh":             "(MWh)",
    "energy_intensity_per_revenue":     "(MWh per USD revenue)",
    "energy_reduction_vs_baseline_pct": "(% reduction vs baseline)",
    # Emissions
    "scope1_emissions_tco2e":           "(tonnes CO2 equivalent)",
    "scope2_emissions_tco2e":           "(tonnes CO2 equivalent)",
    "scope3_emissions_tco2e":           "(tonnes CO2 equivalent)",
    "carbon_offset_tco2e":              "(tonnes CO2 equivalent)",
    "emissions_intensity_per_revenue":  "(tCO2e per USD revenue)",
    "yoy_emissions_change_pct":         "(% change year-on-year)",
    "carbon_price_assumption_usd":      "(USD per tonne CO2)",
    # Water
    "water_withdrawal_m3":              "(cubic metres)",
    "water_recycled_pct":               "(% of withdrawal recycled)",
    "water_intensity_per_revenue":      "(m³ per USD revenue)",
    "water_reduction_target_pct":       "(% reduction target)",
    # Waste
    "waste_total_tonnes":               "(tonnes)",
    "waste_recycled_pct":               "(% recycled)",
    "waste_hazardous_tonnes":           "(tonnes)",
    "waste_to_landfill_tonnes":         "(tonnes)",
    "diversion_rate_pct":               "(% diverted from landfill)",
    # Workforce
    "employees_total":                  "(people)",
    "employees_female_pct":             "(% of total workforce)",
    "employees_male_pct":               "(% of total workforce)",
    "employee_turnover_pct":            "(% annual turnover)",
    "new_hires":                        "(people)",
    "training_hours_per_employee":      "(hours per employee per year)",
    "part_time_employees":              "(people)",
    "union_membership_pct":             "(% of workforce)",
    # Health & Safety
    "work_related_injuries":            "(recordable injuries)",
    "fatalities":                       "(fatalities — report with full transparency)",
    "lost_time_injury_frequency_rate":  "(per million hours worked)",
    "near_miss_incidents":              "(incidents)",
    "occupational_illness_rate":        "(per 100 employees)",
    # Governance
    "board_members_total":              "(people)",
    "board_members_female":             "(people)",
    "independent_directors_pct":        "(% of board)",
    "ceo_pay_ratio":                    "(CEO pay vs median employee pay)",
    "anti_corruption_training_pct":     "(% of relevant staff trained)",
    "supplier_audits_conducted":        "(audits conducted)",
    "suppliers_with_code_of_conduct_pct": "(% of suppliers)",
    # Community & Ethics
    "community_investment_usd":         "(USD)",
    "volunteer_hours":                  "(hours)",
    "data_breaches":                    "(incidents — disclose per GRI 418-1)",
    "corruption_incidents":             "(confirmed incidents)",
    "whistleblower_cases":              "(cases reported)",
    # Targets
    "net_zero_target_year":             "(target year)",
    "renewable_energy_target_pct":      "(% target)",
    "waste_diversion_target_pct":       "(% target)",
    # General
    "reporting_year":                   "(year)",
    "annual_revenue_usd":               "(USD)",
    "number_of_sites":                  "(sites)",
}


# ── Red-flag detector ──────────────────────────────────────────────────────────

def _detect_red_flags(kpi_data: dict) -> list[str]:
    """
    Scan KPI data against RED_FLAG_RULES.
    Returns a list of instruction strings to inject into the prompt.
    """
    instructions = []
    for rule in RED_FLAG_RULES:
        kpi = rule["kpi"]
        value = kpi_data.get(kpi)
        if value is not None and rule["condition"](value):
            msg = rule["instruction"].format(value=value)
            instructions.append(msg)
    return instructions


# ── Prompt builders ────────────────────────────────────────────────────────────

def build_user_prompt(
    section_readiness: SectionReadiness,
    company_name: str,
    reporting_year: str,
) -> str:
    """
    Builds the user prompt for one report section.
    Injects red-flag instructions and section-specific tone guidance.
    """
    section = section_readiness.section
    kpi_data = section_readiness.available_kpis
    kpi_lines = _format_kpis(kpi_data)

    # Section-specific tone
    tone = SECTION_TONE.get(section.section_id, "")
    tone_block = f"\nSECTION GUIDANCE:\n{tone}\n" if tone else ""

    # Red-flag instructions
    red_flags = _detect_red_flags(kpi_data)
    if red_flags:
        flag_block = "\nMATERIALITY ALERTS — ADDRESS THESE IN YOUR RESPONSE:\n"
        for i, flag in enumerate(red_flags, 1):
            flag_block += f"{i}. {flag}\n"
    else:
        flag_block = ""

    # Missing optional KPIs note
    missing_optional = section_readiness.missing_optional
    if missing_optional:
        missing_note = (
            f"\nDATA GAPS: The following optional KPIs are not available for this "
            f"reporting period: {', '.join(missing_optional)}. "
            f"Where relevant, briefly note these will be included in future reports "
            f"rather than leaving unexplained gaps.\n"
        )
    else:
        missing_note = ""

    prompt = f"""Write the "{section.title}" section for {company_name}'s \
{reporting_year} Sustainability Report.

GRI Reference: {section.gri_code}
{"TCFD Pillar: " + section.tcfd_pillar if section.tcfd_pillar else ""}
{tone_block}{flag_block}{missing_note}
SECTION FOCUS:
{section.prompt_focus}

COMPANY DATA FOR THIS SECTION:
{kpi_lines}

Write this section now in formal sustainability report prose (200–350 words).
Use ONLY the data provided above. Every number you mention must appear in the
data above. Pay close attention to unit labels.
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


# ── KPI formatter ──────────────────────────────────────────────────────────────

def _format_kpis(kpi_data: dict) -> str:
    """
    Formats a KPI dictionary into clean readable lines with unit hints.

    Input:  {"scope1_emissions_tco2e": 42000, "reporting_year": 2024}
    Output:   Scope1 Emissions (tonnes CO2 equivalent): 42,000
              Reporting Year (year): 2024
    """
    lines = []
    for key, value in kpi_data.items():
        if value is None:
            continue
        if isinstance(value, int):
            formatted = str(value) if 1900 <= value <= 2100 else f"{value:,}"
        elif isinstance(value, float):
            formatted = f"{value:,.3f}".rstrip("0").rstrip(".")
        else:
            formatted = str(value)

        label = key.replace("_", " ").title()
        unit = UNIT_HINTS.get(key, "")
        hint = f" {unit}" if unit else ""
        lines.append(f"  {label}{hint}: {formatted}")

    return "\n".join(lines) if lines else "  No data available for this section."