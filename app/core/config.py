"""
app/core/config.py
──────────────────
Central configuration for the report generator.
Reads from environment variables (.env file).
"""

from pydantic_settings import BaseSettings
from pathlib import Path

# Project root — two levels up from this file
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # ── LLM Provider ──────────────────────────────────────────────
    llm_provider: str = "groq"          # "groq" or "openai"
    groq_api_key: str = ""
    openai_api_key: str = ""
    groq_model: str = "llama3-70b-8192"
    openai_model: str = "gpt-4o-mini"
    max_tokens_per_section: int = 800

    # ── File Paths ─────────────────────────────────────────────────
    output_dir: Path = ROOT_DIR / "outputs"
    temp_dir: Path = ROOT_DIR / "temp"
    sample_csv_dir: Path = ROOT_DIR / "data" / "sample_csvs"

    # ── Report Defaults ────────────────────────────────────────────
    report_author: str = "AI Sustainability Report Generator"
    report_disclaimer: str = (
        "This report was generated with AI assistance. "
        "All figures should be verified against source data "
        "before external publication."
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Single shared instance — import this everywhere
settings = Settings()