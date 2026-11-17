"""Consulting DOCX deliverable builder (python-docx, corporate theme).

Structure: styled cover header → executive callout box → findings →
formatted detail table → embedded high-DPI chart → governance matrix →
sign-off checklist.
"""

from __future__ import annotations

import io

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from app.doc_factory import charts, theme
from app.doc_factory.content import StageContent, build_content


def _shade_cell(cell, hex_fill: str) -> None:
    """Apply a background fill to a table cell (low-level shading element)."""
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:fill"), hex_fill.lstrip("#"))
    cell._tc.get_or_add_tcPr().append(shading)


def _style_run(run, size: int, hex_color: str, bold: bool = False) -> None:
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = theme.FONT_BODY
    run.font.color.rgb = theme.docx_color(hex_color)


def _heading(doc: Document, text: str, size: int = 16) -> None:
    paragraph = doc.add_paragraph()
    _style_run(paragraph.add_run(text), size, theme.DEEP_NAVY, bold=True)


def _styled_table(doc: Document, headers: list[str],
                  rows: list[list[str]]):
    table = doc.add_table(rows=1, cols=max(len(headers), 1))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for c, header in enumerate(headers):
        cell = table.rows[0].cells[c]
        cell.text = ""
        _style_run(cell.paragraphs[0].add_run(header), 10, theme.WHITE, bold=True)
        _shade_cell(cell, theme.ELECTRIC_SKY)
    for r, row in enumerate(rows):
        cells = table.add_row().cells
        for c in range(len(headers)):
            value = str(row[c]) if c < len(row) else ""
            cells[c].text = ""
            _style_run(cells[c].paragraphs[0].add_run(value), 10, theme.SLATE)
            if r % 2 == 1:
                _shade_cell(cells[c], theme.LIGHT_GREY)
    return table


def generate_stage_docx(stage_num: int, engagement_data: dict,
                        stage_result: dict) -> bytes:
    """Render the consulting deliverable for a stage; returns .docx bytes."""
    content: StageContent = build_content(stage_num, engagement_data, stage_result)
    doc = Document()

    # --- Cover header -------------------------------------------------------------
    header = doc.add_table(rows=1, cols=1)
    header_cell = header.rows[0].cells[0]
    _shade_cell(header_cell, theme.DEEP_NAVY)
    header_cell.text = ""
    p1 = header_cell.paragraphs[0]
    _style_run(p1.add_run(f"Stage {content.stage_num}: {content.stage_name}"),
               22, theme.WHITE, bold=True)
    p2 = header_cell.add_paragraph()
    _style_run(p2.add_run(
        f"{content.client_name}  •  {content.industry}  •  "
        f"{content.domain_track} track  —  AI Head Coach Deliverable"),
        11, "#94A3B8")
    doc.add_paragraph()

    # --- Executive callout box -------------------------------------------------------
    callout = doc.add_table(rows=1, cols=1)
    callout.style = "Table Grid"
    callout_cell = callout.rows[0].cells[0]
    _shade_cell(callout_cell, theme.LIGHT_GREY)
    callout_cell.text = ""
    cp = callout_cell.paragraphs[0]
    _style_run(cp.add_run("EXECUTIVE SUMMARY  "), 11, theme.ELECTRIC_SKY, bold=True)
    _style_run(cp.add_run(content.executive_summary), 11, theme.SLATE)
    doc.add_paragraph()

    # --- 4 pillars ---------------------------------------------------------------------
    _heading(doc, "The Four Pillars", 14)
    pillar_table = _styled_table(
        doc, ["Pillar", "Positioning"],
        [[pillar.title(), text] for pillar, text in content.pillars.items()])
    pillar_table.columns[0].width = Inches(1.5)
    doc.add_paragraph()

    # --- Findings ------------------------------------------------------------------------
    _heading(doc, "Statistical & Diagnostic Findings", 14)
    for finding in content.key_findings:
        bullet = doc.add_paragraph(style="List Bullet")
        _style_run(bullet.add_run(finding), 11, theme.SLATE)
    doc.add_paragraph()

    # --- Detail table -----------------------------------------------------------------------
    _heading(doc, content.table_title, 14)
    if content.table_rows:
        _styled_table(doc, content.table_headers, content.table_rows[:10])
    doc.add_paragraph()

    # --- Embedded chart -------------------------------------------------------------------------
    _heading(doc, "Evidence Visual", 14)
    chart_png = charts.stage_chart(stage_num, stage_result or {})
    chart_paragraph = doc.add_paragraph()
    chart_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    chart_paragraph.add_run().add_picture(io.BytesIO(chart_png), width=Inches(6.2))
    doc.add_paragraph()

    # --- Governance matrix -------------------------------------------------------------------------
    _heading(doc, "Governance & Risk Matrix", 14)
    governance = _styled_table(
        doc, ["Gate", "Status", "Notes"],
        [[gate, status, notes] for gate, status, notes in content.governance_rows])
    for r, (_, status, _) in enumerate(content.governance_rows, start=1):
        cell = governance.rows[r].cells[1]
        _shade_cell(cell, theme.STATUS_COLORS.get(status, theme.SLATE))
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.color.rgb = theme.docx_color(theme.WHITE)
                run.font.bold = True
    doc.add_paragraph()

    # --- Next steps + sign-off checklist --------------------------------------------------------------
    _heading(doc, "Recommended Next Steps", 14)
    for step in content.next_steps:
        numbered = doc.add_paragraph(style="List Number")
        _style_run(numbered.add_run(step), 11, theme.SLATE)
    doc.add_paragraph()

    _heading(doc, "Sign-Off Checklist", 14)
    _styled_table(doc, ["Item", "Owner", "Signature / Date"], [
        ["Findings reviewed with engagement sponsor", "", ""],
        ["Governance gate statuses acknowledged", "", ""],
        ["Next-step owners and dates confirmed", "", ""],
        ["Deliverable archived to engagement workspace", "", ""],
    ])

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
