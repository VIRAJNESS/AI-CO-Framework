"""Unified corporate visual theme for all generated deliverables.

Single source of truth consumed by matplotlib charts (hex strings) and
python-pptx / python-docx builders (RGBColor).
"""

from __future__ import annotations

from docx.shared import RGBColor as DocxColor
from pptx.dml.color import RGBColor as PptxColor

# --- Brand palette (hex) --------------------------------------------------------
DEEP_NAVY = "#0F172A"
ELECTRIC_SKY = "#0284C7"
SLATE = "#334155"
EMERALD = "#059669"
WHITE = "#FFFFFF"
LIGHT_GREY = "#F1F5F9"   # subtle fill for alternating rows / callouts
AMBER = "#D97706"        # warnings in risk matrices
ROSE = "#E11D48"         # failures in risk matrices


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    value = hex_str.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def pptx_color(hex_str: str) -> PptxColor:
    return PptxColor(*_hex_to_rgb(hex_str))


def docx_color(hex_str: str) -> DocxColor:
    return DocxColor(*_hex_to_rgb(hex_str))


# Typography
FONT_HEADING = "Segoe UI"
FONT_BODY = "Segoe UI"

# Chart defaults
CHART_DPI = 200
CHART_FACE = WHITE
CHART_GRID = "#E2E8F0"

# Status color mapping for governance/risk matrices
STATUS_COLORS = {"PASS": EMERALD, "WARN": AMBER, "FAIL": ROSE, "N/A": SLATE}
