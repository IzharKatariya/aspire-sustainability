"""
app/core/report_template.py
────────────────────────────
Defines the visual structure and layout of the generated Word document.
All document assembly code reads from these dataclasses — no magic numbers
scattered across the codebase.
"""

from dataclasses import dataclass, field
from typing import Optional
from app.core.schema import REPORT_SECTIONS, ReportSection



@dataclass(frozen=True)
class DocumentStyle:
    """
    Font and layout settings for the Word document.
    Sizes are in points. Colors are hex strings (no #).
    """
    # Fonts
    heading_font: str = "Calibri"
    body_font: str = "Calibri"

    # Font sizes (points)
    title_size: int = 28
    heading1_size: int = 16
    heading2_size: int = 13
    body_size: int = 11
    caption_size: int = 9

    # Colors (hex, no #)
    heading_color: str = "1F3864"   # dark navy — professional consulting look
    body_color: str = "000000"      # black
    accent_color: str = "2E86AB"    # teal — sustainability feel
    table_header_bg: str = "1F3864" # navy table headers
    table_header_fg: str = "FFFFFF" # white text on navy

    # Page margins (centimetres)
    margin_top: float = 2.5
    margin_bottom: float = 2.5
    margin_left: float = 2.8
    margin_right: float = 2.8

    # Spacing
    paragraph_space_after: int = 8   # pts after each paragraph
    line_spacing: float = 1.15



@dataclass(frozen=True)
class TitlePageConfig:
    """
    Controls what appears on the title page of the report.
    {company_name} and {reporting_year} are filled at runtime
    from the uploaded CSV data.
    """
    main_title: str = "Sustainability Report"
    subtitle_template: str = "{company_name} | {reporting_year}"
    prepared_by_label: str = "Prepared by"
    prepared_by_value: str = "ASPIRE"

    confidentiality_notice: str = (
        "AI-ASSISTED DRAFT — FOR INTERNAL REVIEW ONLY\n"
        "All figures must be verified against source data "
        "before external publication."
    )
    include_toc: bool = True          # generate a Table of Contents page
    include_gri_index: bool = True    # append a GRI Content Index at the end



# This is the sequence sections appear in the final document.
# We pull directly from schema.py so there is ONE source of truth.
# If you want to reorder, do it here — schema.py stays untouched.

DOCUMENT_SECTION_ORDER: list[ReportSection] = [
    # Front matter
    next(s for s in REPORT_SECTIONS if s.section_id == "overview"),
    next(s for s in REPORT_SECTIONS if s.section_id == "governance"),
    next(s for s in REPORT_SECTIONS if s.section_id == "climate_strategy"),
    # Environmental
    next(s for s in REPORT_SECTIONS if s.section_id == "energy"),
    next(s for s in REPORT_SECTIONS if s.section_id == "emissions"),
    next(s for s in REPORT_SECTIONS if s.section_id == "water"),
    next(s for s in REPORT_SECTIONS if s.section_id == "waste"),
    # Social
    next(s for s in REPORT_SECTIONS if s.section_id == "workforce"),
    next(s for s in REPORT_SECTIONS if s.section_id == "health_safety"),
    next(s for s in REPORT_SECTIONS if s.section_id == "dei"),
    # Governance & Forward Look
    next(s for s in REPORT_SECTIONS if s.section_id == "community_ethics"),
    next(s for s in REPORT_SECTIONS if s.section_id == "targets_outlook"),
]



@dataclass(frozen=True)
class FooterConfig:
    """Footer text on every page of the report."""
    left_text: str = "Confidential — AI-Assisted Draft"
    center_text: str = ""                      # empty = nothing in center
    right_text: str = "Page {page_number}"     # filled by python-docx at render
    font_size: int = 8
    font_color: str = "808080"                 # grey


# Import these in document assembly — don't instantiate new ones

STYLE = DocumentStyle()
TITLE_PAGE = TitlePageConfig()
FOOTER = FooterConfig()