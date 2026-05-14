"""
app/llm/pipeline.py
────────────────────
Orchestrates the full LLM generation pipeline.

For each ready section in the SectionPlan:
  1. Build the prompt (prompts.py)
  2. Send to Groq (groq_client.py)
  3. Collect the generated text
  4. Return all results as a GeneratedReport

Usage:
    from app.core.section_planner import SectionPlanner
    from app.llm.pipeline import LLMPipeline

    plan = SectionPlanner("data/sample_csvs/company_a.csv").build_plan()
    pipeline = LLMPipeline()
    report = pipeline.run(plan)
    print(report.sections["energy"])
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.core.section_planner import SectionPlan
from app.llm.prompts import build_messages
from app.llm.groq_client import generate_section


# ── Result Container ──────────────────────────────────────────────────────────

@dataclass
class GeneratedReport:
    """
    Holds all LLM-generated section texts for one company.

    sections        : section_id → generated text
    skipped         : section_ids that were skipped (missing data)
    failed          : section_ids where LLM call failed
    company_name    : name of the company
    reporting_year  : year of the report
    """
    company_name: str
    reporting_year: str
    sections: dict[str, str] = field(default_factory=dict)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"{'='*60}",
            f"  Generated Report: {self.company_name} ({self.reporting_year})",
            f"{'='*60}",
            f"  Sections generated : {len(self.sections)}",
            f"  Sections skipped   : {len(self.skipped)}",
            f"  Sections failed    : {len(self.failed)}",
            f"{'─'*60}",
        ]
        for section_id, text in self.sections.items():
            word_count = len(text.split())
            lines.append(f"  ✓ {section_id:<25} ({word_count} words)")
        for section_id in self.skipped:
            lines.append(f"  ○ {section_id:<25} (skipped — missing data)")
        for section_id in self.failed:
            lines.append(f"  ✗ {section_id:<25} (failed — API error)")
        lines.append(f"{'='*60}")
        return "\n".join(lines)


# ── LLM Pipeline ──────────────────────────────────────────────────────────────

class LLMPipeline:
    """
    Runs the full LLM generation pipeline for a SectionPlan.

    Processes each ready section sequentially.
    Skips sections marked as not ready by the planner.
    Handles individual section failures gracefully without
    stopping the entire pipeline.
    """

    def __init__(
        self,
        delay_between_calls: float = 1.0,
    ) -> None:
        """
        Args:
            delay_between_calls: seconds to wait between API calls.
                                 Groq free tier has rate limits.
                                 1 second is safe.
        """
        self.delay = delay_between_calls

    def run(self, plan: SectionPlan) -> GeneratedReport:
        """
        Main entry point. Runs the pipeline for all ready sections.

        Args:
            plan: SectionPlan from the SectionPlanner

        Returns:
            GeneratedReport with all generated section texts
        """
        report = GeneratedReport(
            company_name=plan.company_name,
            reporting_year=plan.reporting_year,
        )

        # Mark skipped sections immediately
        report.skipped = plan.skipped_sections.copy()

        total = len(plan.ready_sections)
        print(f"\nStarting LLM pipeline for {plan.company_name}")
        print(f"Generating {total} sections...\n")

        for i, section_readiness in enumerate(plan.ready_sections, 1):
            section_id = section_readiness.section.section_id
            title = section_readiness.section.title

            print(f"  [{i}/{total}] Generating: {title}...")

            try:
                # Build the prompt
                messages = build_messages(
                    section_readiness=section_readiness,
                    company_name=plan.company_name,
                    reporting_year=plan.reporting_year,
                )

                # Call the LLM
                text = generate_section(messages)

                # Store the result
                report.sections[section_id] = text
                word_count = len(text.split())
                print(f"         ✓ Done ({word_count} words)")

            except Exception as e:
                # One section failing should not stop the whole report
                print(f"         ✗ Failed: {e}")
                report.failed.append(section_id)

            # Respect rate limits between calls
            if i < total:
                time.sleep(self.delay)

        print(f"\nPipeline complete.")
        print(report.summary())
        return report