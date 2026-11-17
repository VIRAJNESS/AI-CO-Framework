"""Executive PPTX deck builder (python-pptx, 16:9, corporate theme).

Produces a 7-slide boardroom deck for any stage:
  1. Title
  2. Executive Summary & 4 Pillars
  3. High-DPI matplotlib chart (stage signature visual)
  4. Key findings
  5. Architecture / Execution table
  6. Governance & Risk matrix
  7. Recommended next steps
"""

from __future__ import annotations

import io

from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

from app.doc_factory import charts, theme
from app.doc_factory.content import StageContent, build_content

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def _blank_slide(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])  # fully blank layout


def _add_rect(slide, x, y, w, h, hex_fill: str):
    from pptx.enum.shapes import MSO_SHAPE

    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = theme.pptx_color(hex_fill)
    shape.line.fill.background()
    return shape


def _add_text(slide, x, y, w, h, text: str, size: int, hex_color: str,
              bold: bool = False, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(x, y, w, h)
    frame = box.text_frame
    frame.word_wrap = True
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = theme.FONT_HEADING
    run.font.color.rgb = theme.pptx_color(hex_color)
    return box


def _title_band(slide, title: str, subtitle: str):
    """Navy header band used on every content slide."""
    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.0), theme.DEEP_NAVY)
    _add_text(slide, Inches(0.5), Inches(0.12), Inches(11.0), Inches(0.5),
              title, 24, theme.WHITE, bold=True)
    _add_text(slide, Inches(0.5), Inches(0.58), Inches(11.0), Inches(0.35),
              subtitle, 12, "#94A3B8")


def _add_table(slide, headers: list[str], rows: list[list[str]],
               x, y, w, row_h=Inches(0.42)):
    n_rows, n_cols = len(rows) + 1, max(len(headers), 1)
    graphic = slide.shapes.add_table(
        n_rows, n_cols, x, y, w, Emu(int(row_h) * n_rows))
    table = graphic.table
    for c, header in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = header
        cell.fill.solid()
        cell.fill.fore_color.rgb = theme.pptx_color(theme.ELECTRIC_SKY)
        para = cell.text_frame.paragraphs[0]
        para.runs[0].font.bold = True
        para.runs[0].font.size = Pt(12)
        para.runs[0].font.color.rgb = theme.pptx_color(theme.WHITE)
    for r, row in enumerate(rows, start=1):
        for c in range(n_cols):
            cell = table.cell(r, c)
            cell.text = str(row[c]) if c < len(row) else ""
            cell.fill.solid()
            cell.fill.fore_color.rgb = theme.pptx_color(
                theme.WHITE if r % 2 else theme.LIGHT_GREY)
            para = cell.text_frame.paragraphs[0]
            if para.runs:
                para.runs[0].font.size = Pt(10)
                para.runs[0].font.color.rgb = theme.pptx_color(theme.SLATE)
    return table


def generate_stage_pptx(stage_num: int, engagement_data: dict,
                        stage_result: dict) -> bytes:
    """Render the boardroom deck for a stage; returns .pptx bytes."""
    content: StageContent = build_content(stage_num, engagement_data, stage_result)
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # --- Slide 1: Title ---------------------------------------------------------
    slide = _blank_slide(prs)
    _add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, theme.DEEP_NAVY)
    _add_rect(slide, 0, Inches(4.9), SLIDE_W, Inches(0.12), theme.ELECTRIC_SKY)
    _add_text(slide, Inches(0.8), Inches(2.1), Inches(11.7), Inches(1.0),
              f"Stage {content.stage_num}: {content.stage_name}",
              40, theme.WHITE, bold=True)
    _add_text(slide, Inches(0.8), Inches(3.3), Inches(11.7), Inches(0.6),
              f"{content.client_name}  •  {content.industry}  •  "
              f"{content.domain_track} track", 18, "#94A3B8")
    _add_text(slide, Inches(0.8), Inches(5.4), Inches(11.7), Inches(0.5),
              "AI Head Coach — Executive Deliverable", 14, theme.EMERALD)

    # --- Slide 2: Executive summary & 4 pillars -----------------------------------
    slide = _blank_slide(prs)
    _title_band(slide, "Executive Summary", "The 4 Pillars: Vision • Trust • Depth • Solving")
    _add_text(slide, Inches(0.5), Inches(1.2), Inches(12.3), Inches(1.1),
              content.executive_summary, 15, theme.SLATE)
    positions = [(0.5, 2.6), (6.9, 2.6), (0.5, 4.9), (6.9, 4.9)]
    for (px, py), (pillar, text) in zip(positions, content.pillars.items()):
        _add_rect(slide, Inches(px), Inches(py), Inches(5.9), Inches(2.0),
                  theme.LIGHT_GREY)
        _add_text(slide, Inches(px + 0.2), Inches(py + 0.1), Inches(5.5),
                  Inches(0.4), pillar.upper(), 14, theme.ELECTRIC_SKY, bold=True)
        _add_text(slide, Inches(px + 0.2), Inches(py + 0.55), Inches(5.5),
                  Inches(1.35), text, 11, theme.SLATE)

    # --- Slide 3: Signature chart ---------------------------------------------------
    slide = _blank_slide(prs)
    _title_band(slide, "Evidence Visual", content.table_title)
    chart_png = charts.stage_chart(stage_num, stage_result or {})
    slide.shapes.add_picture(io.BytesIO(chart_png), Inches(1.3), Inches(1.3),
                             width=Inches(10.7))

    # --- Slide 4: Key findings -------------------------------------------------------
    slide = _blank_slide(prs)
    _title_band(slide, "Key Findings", f"Stage {content.stage_num} diagnostics")
    y = 1.4
    for finding in content.key_findings[:5]:
        _add_rect(slide, Inches(0.5), Inches(y), Inches(0.14), Inches(0.7),
                  theme.EMERALD)
        _add_text(slide, Inches(0.85), Inches(y), Inches(11.8), Inches(0.8),
                  finding, 14, theme.SLATE)
        y += 1.05

    # --- Slide 5: Architecture / execution table ---------------------------------------
    slide = _blank_slide(prs)
    _title_band(slide, content.table_title, "Execution detail")
    if content.table_rows:
        _add_table(slide, content.table_headers, content.table_rows[:8],
                   Inches(0.5), Inches(1.4), Inches(12.3))
    else:
        _add_text(slide, Inches(0.5), Inches(1.6), Inches(12.0), Inches(0.6),
                  "Detail will populate after stage execution.", 14, theme.SLATE)

    # --- Slide 6: Governance & risk matrix -----------------------------------------------
    slide = _blank_slide(prs)
    _title_band(slide, "Governance & Risk Matrix", "Five gates guard every stage execution")
    rows = [[gate, status, notes[:60]] for gate, status, notes
            in content.governance_rows]
    table = _add_table(slide, ["Gate", "Status", "Notes"], rows,
                       Inches(0.5), Inches(1.4), Inches(12.3))
    # Color the status column by gate state.
    for r, (_, status, _) in enumerate(content.governance_rows, start=1):
        cell = table.cell(r, 1)
        cell.fill.solid()
        cell.fill.fore_color.rgb = theme.pptx_color(
            theme.STATUS_COLORS.get(status, theme.SLATE))
        para = cell.text_frame.paragraphs[0]
        if para.runs:
            para.runs[0].font.color.rgb = theme.pptx_color(theme.WHITE)
            para.runs[0].font.bold = True

    # --- Slide 7: Next steps ------------------------------------------------------------
    slide = _blank_slide(prs)
    _title_band(slide, "Recommended Next Steps", "Decision-ready actions")
    y = 1.5
    for idx, step in enumerate(content.next_steps[:5], start=1):
        _add_rect(slide, Inches(0.5), Inches(y), Inches(0.55), Inches(0.55),
                  theme.ELECTRIC_SKY)
        _add_text(slide, Inches(0.5), Inches(y + 0.02), Inches(0.55), Inches(0.5),
                  str(idx), 18, theme.WHITE, bold=True, align=PP_ALIGN.CENTER)
        _add_text(slide, Inches(1.3), Inches(y + 0.04), Inches(11.3), Inches(0.6),
                  step, 15, theme.SLATE)
        y += 0.95
    _add_rect(slide, 0, Inches(6.9), SLIDE_W, Inches(0.6), theme.DEEP_NAVY)
    _add_text(slide, Inches(0.5), Inches(6.98), Inches(12.0), Inches(0.4),
              f"{content.client_name} — Stage {content.stage_num} • "
              f"AI Coach Mastery", 11, "#94A3B8")

    buffer = io.BytesIO()
    prs.save(buffer)
    return buffer.getvalue()
