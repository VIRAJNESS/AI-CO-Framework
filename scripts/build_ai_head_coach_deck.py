"""
Build a professional 'AI Head Coach Contents' PPTX deck.

Summarises the six AI Head Coach practice PDFs, and for each section
provides a glossary mapped to the impactful actions each term drives.

Usage:  python scripts/build_ai_head_coach_deck.py
Output: AI_Head_Coach_Contents.pptx  (workspace root)
"""

import os

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# ----------------------------------------------------------------------------
# Theme palette (professional navy / teal / slate)
# ----------------------------------------------------------------------------
NAVY = RGBColor(0x0B, 0x1F, 0x3A)        # primary dark background
NAVY_2 = RGBColor(0x12, 0x2B, 0x4F)      # secondary panel
TEAL = RGBColor(0x18, 0xB8, 0xA6)        # accent
GOLD = RGBColor(0xF2, 0xB1, 0x34)        # highlight accent
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xE8, 0xEE, 0xF6)       # light text on dark
SLATE = RGBColor(0x44, 0x50, 0x62)       # body text on light
PALE = RGBColor(0xF4, 0xF7, 0xFB)        # light slide background
GRID = RGBColor(0xC9, 0xD4, 0xE2)        # table grid-ish fill
ROW_ALT = RGBColor(0xEA, 0xF0, 0xF8)     # alternating row fill

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]


# ----------------------------------------------------------------------------
# Low-level helpers
# ----------------------------------------------------------------------------
def add_slide(bg=PALE):
    slide = prs.slides.add_slide(BLANK)
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = bg
    return slide


def add_rect(slide, x, y, w, h, color, line=None):
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp


def add_text(slide, x, y, w, h, text, size=14, color=SLATE, bold=False,
             align=PP_ALIGN.LEFT, font="Segoe UI", anchor=MSO_ANCHOR.TOP,
             line_spacing=1.0):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = ln
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = font
    return tb


def add_bullets(slide, x, y, w, h, items, size=13, color=SLATE,
                head_color=NAVY, line_spacing=1.08, space_after=6):
    """items: list of (lead, rest) tuples; lead rendered bold+accent."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, (lead, rest) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        r0 = p.add_run()
        r0.text = "\u25AA  "
        r0.font.size = Pt(size)
        r0.font.color.rgb = TEAL
        r0.font.bold = True
        r1 = p.add_run()
        r1.text = f"{lead}: " if rest else lead
        r1.font.size = Pt(size)
        r1.font.bold = True
        r1.font.color.rgb = head_color
        r1.font.name = "Segoe UI"
        if rest:
            r2 = p.add_run()
            r2.text = rest
            r2.font.size = Pt(size)
            r2.font.color.rgb = color
            r2.font.name = "Segoe UI"
    return tb


def header(slide, number, title, subtitle):
    """Standard section header band."""
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.12), NAVY)
    add_rect(slide, 0, Inches(1.12), SLIDE_W, Inches(0.045), TEAL)
    add_text(slide, Inches(0.45), Inches(0.12), Inches(1.3), Inches(0.9),
             number, size=30, color=GOLD, bold=True, font="Segoe UI Black",
             anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, Inches(1.55), Inches(0.10), Inches(11.3), Inches(0.5),
             title, size=24, color=WHITE, bold=True)
    add_text(slide, Inches(1.55), Inches(0.62), Inches(11.3), Inches(0.45),
             subtitle, size=12.5, color=RGBColor(0x9F, 0xC6, 0xE8))


def set_cell(cell, text, size=11, color=SLATE, bold=False, fill=None,
             align=PP_ALIGN.LEFT):
    if fill is not None:
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill
    cell.margin_left = Inches(0.08)
    cell.margin_right = Inches(0.08)
    cell.margin_top = Inches(0.04)
    cell.margin_bottom = Inches(0.04)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf = cell.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = "Segoe UI"


def glossary_slide(number, section, rows, size=10.5):
    """Create a 'Glossary -> Impactful Action' table slide for a section."""
    slide = add_slide()
    header(slide, number, f"{section} — Glossary & Impact Map",
           "What each term means, and the impactful action it drives on the ground")
    n = len(rows) + 1
    tbl_shape = slide.shapes.add_table(
        n, 3, Inches(0.45), Inches(1.45), Inches(12.45), Inches(5.6))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(2.55)
    tbl.columns[1].width = Inches(4.90)
    tbl.columns[2].width = Inches(5.00)

    set_cell(tbl.cell(0, 0), "GLOSSARY TERM", size=11, color=WHITE,
             bold=True, fill=NAVY)
    set_cell(tbl.cell(0, 1), "WHAT IT MEANS", size=11, color=WHITE,
             bold=True, fill=NAVY)
    set_cell(tbl.cell(0, 2), "HOW IT DRIVES IMPACTFUL ACTION", size=11,
             color=WHITE, bold=True, fill=NAVY)

    for i, (term, meaning, impact) in enumerate(rows, start=1):
        fill = ROW_ALT if i % 2 == 0 else WHITE
        set_cell(tbl.cell(i, 0), term, size=size, color=NAVY, bold=True,
                 fill=fill)
        set_cell(tbl.cell(i, 1), meaning, size=size, fill=fill)
        set_cell(tbl.cell(i, 2), impact, size=size, color=SLATE, fill=fill)
    return slide


# ============================================================================
# SLIDE 1 — Title
# ============================================================================
s = add_slide(NAVY)
add_rect(s, 0, Inches(4.95), SLIDE_W, Inches(0.05), TEAL)
add_rect(s, Inches(0.0), Inches(0.0), Inches(0.18), SLIDE_H, TEAL)
add_text(s, Inches(0.9), Inches(1.55), Inches(11.5), Inches(0.5),
         "EXECUTIVE ADVISORY & ENGINEERING TRANSFORMATION",
         size=15, color=TEAL, bold=True)
add_text(s, Inches(0.9), Inches(2.1), Inches(11.8), Inches(1.6),
         "AI HEAD COACH", size=54, color=WHITE, bold=True,
         font="Segoe UI Black")
add_text(s, Inches(0.9), Inches(3.15), Inches(11.8), Inches(0.7),
         "Practice Framework, Contents & Glossary-to-Impact Map",
         size=24, color=GOLD, bold=True)
add_text(s, Inches(0.9), Inches(3.95), Inches(11.5), Inches(0.8),
         "Moving organizations beyond ad-hoc prompting to governed, autonomous AI execution\n"
         "across SDLC  •  PDLC  •  Startups  •  Legacy Estates",
         size=15, color=LIGHT, line_spacing=1.2)
add_text(s, Inches(0.9), Inches(5.35), Inches(11.5), Inches(0.5),
         "Synthesized from the 6-document AI Head Coach Practice Toolkit",
         size=12, color=RGBColor(0x9F, 0xC6, 0xE8))

# ============================================================================
# SLIDE 2 — Framework at a Glance (Contents)
# ============================================================================
s = add_slide()
header(s, "\u2302", "The AI Head Coach Toolkit — Contents at a Glance",
       "Six interlocking assets that take a client from first diagnostic to CFO-grade proof of value")

cards = [
    ("01", "Strategy & Positioning",
     "Breaks the \u201CChatGPT solves everything\u201D illusion. Four Pillars of advisory, "
     "Copilot-vs-Agent paradigm, and the 4-stage maturity journey."),
    ("02", "Domain Execution Playbooks",
     "Common cross-domain foundations plus mutually exclusive field tactics for "
     "SDLC, PDLC, Startups, and Legacy modernization."),
    ("03", "Measurement, Metrics & Mentoring",
     "\u201CNo Vanity Metrics\u201D rule, master KPI scorecard, 30-60-90 day cadence, "
     "and role-based mentoring to build self-sustaining talent."),
    ("04", "Client Pitch & Brochure",
     "The executive dilemma, outcome benchmarks (30%+ deflection, 69% toil cut), "
     "and three commercial engagement tiers."),
    ("05", "Discovery & Diagnostic Audit",
     "10-day field instrument: 5-Pillar readiness rubric, universal audit gates, "
     "track-specific probes, and red-flag stop conditions."),
    ("06", "Statistical Methods & AI ROI",
     "Causal experiment designs (A/B, DiD, bandits), agent evaluation statistics, "
     "and a CFO-ready TCO / payback model."),
]
cx, cy = Inches(0.45), Inches(1.45)
cw, ch = Inches(4.08), Inches(2.72)
gap = Inches(0.12)
for i, (num, title, desc) in enumerate(cards):
    col, row = i % 3, i // 3
    x = cx + col * (cw + gap)
    y = cy + row * (ch + gap)
    add_rect(s, x, y, cw, ch, WHITE, line=GRID)
    add_rect(s, x, y, cw, Inches(0.07), TEAL)
    add_text(s, x + Inches(0.18), y + Inches(0.16), Inches(1.0), Inches(0.5),
             num, size=22, color=GOLD, bold=True, font="Segoe UI Black")
    add_text(s, x + Inches(0.95), y + Inches(0.20), cw - Inches(1.1),
             Inches(0.75), title, size=14.5, color=NAVY, bold=True)
    add_text(s, x + Inches(0.18), y + Inches(0.95), cw - Inches(0.36),
             ch - Inches(1.1), desc, size=11, color=SLATE, line_spacing=1.12)

# ============================================================================
# SLIDE 3 — Section 01 Summary: Strategy & Positioning
# ============================================================================
s = add_slide()
header(s, "01", "Strategy & Positioning — Vision, Trust, Depth, Solving",
       "The AI Head Coach is an embedded transformation architect — not a prompt trainer")
add_bullets(s, Inches(0.45), Inches(1.4), Inches(6.3), Inches(5.6), [
    ("The Market Reality", "licensing Claude/GPT seats \u2260 transformation. "
     "Teams hit the Prompting Trap — isolated speed, no systemic throughput."),
    ("Hidden Costs", "unchecked generation creates technical debt, hallucination "
     "risk, architectural drift, and compliance failures."),
    ("Core Proposition", "bridge raw LLM capability and production-grade, "
     "zero-touch business outcomes via Vision, Trust, Depth & Solving."),
    ("Copilots vs. Agents", "copilots give 10–20% task speed-up (often absorbed by "
     "review bottlenecks); autonomous agents cut 50–70%+ of operational toil."),
    ("Commercial Model", "3 tiers — Diagnostic Blueprint (2–3 wks), Embedded "
     "Fractional Coach (3–6 mo), Executive Advisory (retainer)."),
], size=12.5)

add_rect(s, Inches(7.0), Inches(1.4), Inches(5.9), Inches(5.6), NAVY_2)
add_text(s, Inches(7.25), Inches(1.55), Inches(5.4), Inches(0.4),
         "4-STAGE MATURITY JOURNEY", size=14, color=GOLD, bold=True)
stages = [
    ("STAGE 1 — Assisted Augmentation",
     "Standardized copilots, prompt libraries, shadow-AI elimination."),
    ("STAGE 2 — Context-Grounded Workflows",
     "RAG over proprietary knowledge, codebase graphs, SDK workbenches."),
    ("STAGE 3 — Supervised Multi-Agent Orchestration",
     "Planner / Coder / Security / QA sub-agents, human-on-the-loop gates."),
    ("STAGE 4 — Intent-Driven Zero-Touch Ops",
     "Self-healing infra, automated triage, cost circuit-breakers, ROI scorecards."),
]
yy = Inches(2.05)
for t, d in stages:
    add_text(s, Inches(7.25), yy, Inches(5.5), Inches(0.35), t,
             size=12.5, color=TEAL, bold=True)
    add_text(s, Inches(7.25), yy + Inches(0.33), Inches(5.5), Inches(0.62),
             d, size=11, color=LIGHT, line_spacing=1.05)
    yy += Inches(1.18)

# ============================================================================
# SLIDE 4 — Section 01 Glossary
# ============================================================================
glossary_slide("01", "Strategy & Positioning", [
    ("Prompting Trap",
     "Using AI as glorified autocomplete; isolated pockets of speed with zero systemic gain.",
     "Triggers workflow re-engineering around autonomous decisioning instead of buying more seats."),
    ("Four Pillars (Vision, Trust, Depth, Solving)",
     "The advisory differentiation model vs. typical consultants.",
     "Anchors every initiative to P&L, embeds guardrails Day 1, builds real architecture, and upskills internal staff."),
    ("Copilot vs. Autonomous Agent",
     "Assistive, human-triggered micro-tasks vs. event-driven, end-to-end orchestration with persistent memory.",
     "Guides when a copilot suffices and when to invest in agents — avoiding both under- and over-engineering."),
    ("Human-in-the-Loop (HITL)",
     "Confidence thresholds where humans approve critical agent actions.",
     "Unblocks legal/security sign-off so autonomous deployments actually reach production."),
    ("Knowledge Graph / Domain Ontology",
     "Structured representation of the client's rules, schemas and architecture standards.",
     "Grounds agents in truth, eliminating shallow-RAG failures and hallucinated outputs."),
    ("Zero-Touch Operations",
     "Stage-4 state: self-healing infrastructure and exception-only human escalation.",
     "Defines the executive north star: 50–70%+ toil reduction and step-change SLA gains."),
])

# ============================================================================
# SLIDE 5 — Section 02 Summary: Domain Execution Playbooks
# ============================================================================
s = add_slide()
header(s, "02", "Domain Execution Playbooks — SDLC, PDLC, Startups, Legacy",
       "Common non-negotiable foundations + mutually exclusive field tactics per client archetype")
add_text(s, Inches(0.45), Inches(1.35), Inches(12.4), Inches(0.35),
         "FOUR NON-NEGOTIABLE FOUNDATIONS (EVERY ENGAGEMENT)",
         size=13, color=NAVY, bold=True)
add_bullets(s, Inches(0.45), Inches(1.75), Inches(12.4), Inches(1.15), [
    ("1. Baseline Telemetry Capture", "measure pre-AI cycle times, defect rates & toil  "
     "   \u25AA  2. Context & Ontology Grounding: agents reason over truth, not internet priors"),
    ("3. Guardrail & Eval Harness", "automated verification gates before scaling autonomy  "
     "   \u25AA  4. Shadow-to-Autonomous Rollout: go live only when precision > 95%"),
], size=12, space_after=4)

tbl_shape = s.shapes.add_table(5, 3, Inches(0.45), Inches(3.0),
                               Inches(12.45), Inches(4.0))
tbl = tbl_shape.table
tbl.columns[0].width = Inches(2.3)
tbl.columns[1].width = Inches(4.7)
tbl.columns[2].width = Inches(5.45)
set_cell(tbl.cell(0, 0), "TRACK", 11, WHITE, True, NAVY)
set_cell(tbl.cell(0, 1), "PRIMARY BOTTLENECK", 11, WHITE, True, NAVY)
set_cell(tbl.cell(0, 2), "MUTUALLY EXCLUSIVE FIELD METHOD", 11, WHITE, True, NAVY)
track_rows = [
    ("SDLC (Engineering)",
     "PR review queues, brittle tests, environment drift, incident triage toil.",
     "AI Engineering Workbench + autonomous PR/test-gen agents + zero-touch AIOps triage."),
    ("PDLC (Product & UX)",
     "Slow discovery, disconnected feedback, ambiguous PRDs, high drop-off.",
     "Voice-of-customer synthesis \u2192 spec-to-prototype sprints \u2192 in-app digital deflection agents."),
    ("Startups (Seed–Series B)",
     "Capital constraints, tiny headcount, need PMF without tech debt.",
     "Agentic pod topology (1 engineer = 5-person pod), data/ontology moat, multi-model FinOps routing."),
    ("Legacy (Enterprise Core)",
     "Undocumented monoliths, COBOL/Java debt, outage fear, compliance.",
     "Codebase archaeology \u2192 knowledge graph \u2192 semantic parity harness \u2192 Strangler-Fig APIs."),
]
for i, (a, b, c) in enumerate(track_rows, 1):
    fill = ROW_ALT if i % 2 == 0 else WHITE
    set_cell(tbl.cell(i, 0), a, 11, NAVY, True, fill)
    set_cell(tbl.cell(i, 1), b, 11, SLATE, False, fill)
    set_cell(tbl.cell(i, 2), c, 11, SLATE, False, fill)

# ============================================================================
# SLIDE 6 — Section 02 Glossary
# ============================================================================
glossary_slide("02", "Domain Execution Playbooks", [
    ("Shadow Mode",
     "Agents log recommendations alongside human actions without executing them.",
     "De-risks rollout: autonomy is switched on only after precision exceeds 95% — no leap of faith."),
    ("Guardrail & Eval Harness",
     "Automated gates: security scans, schema validators, hallucination checks.",
     "Lets teams scale agent autonomy safely instead of throttling everything through human review."),
    ("Agentic Pod Topology",
     "One engineer orchestrating specialized agents for scaffolding, docs, QA and DevOps.",
     "A startup engineer operates like a 5-person pod — runway extended, velocity multiplied."),
    ("Strangler-Fig Agents",
     "Intelligent orchestration layer wrapping legacy backends while modules migrate incrementally.",
     "Enables zero-downtime modernization — no big-bang rewrite of mission-critical cores."),
    ("Codebase Archaeology",
     "Static-analysis + LLM agents parse undocumented legacy code into a queryable knowledge graph.",
     "Cuts legacy discovery cost 60%+ and exposes hidden business rules before any refactor."),
    ("Semantic Parity Harness",
     "AI-generated exhaustive input/output characterization tests against the legacy system.",
     "Guarantees 100% behavioral parity in replacements, eliminating regression fear that blocks modernization."),
    ("Model Routing / FinOps Discipline",
     "Lightweight models for classification; frontier models only for complex reasoning.",
     "Protects gross margins as volume scales and prevents runaway token burn."),
])

# ============================================================================
# SLIDE 7 — Section 03 Summary: Measurement, Metrics & Mentoring
# ============================================================================
s = add_slide()
header(s, "03", "Measurement, Metrics & Mentoring Framework",
       "Proving hard business value while building self-sustaining internal AI talent")
add_bullets(s, Inches(0.45), Inches(1.4), Inches(6.35), Inches(3.0), [
    ("\u201CNo Vanity Metrics\u201D Rule", "prompts run, seats activated and lines of AI "
     "code mask churn; anchor on Velocity, Toil & Deflection, Quality & Trust, Financial Impact."),
    ("Master KPI Scorecard", "per-track targets — 40–60% faster PR cycles (SDLC); "
     "25–35% deflection (PDLC); 2–3x velocity per pod (Startups); 99.9% parity (Legacy)."),
    ("Agent Evals", ">95% precision on autonomous actions, <0.5% guardrail breaches, "
     "groundedness and escalation precision tracked continuously."),
], size=12.5)
add_rect(s, Inches(0.45), Inches(4.55), Inches(6.35), Inches(2.5), NAVY_2)
add_text(s, Inches(0.7), Inches(4.7), Inches(5.9), Inches(0.35),
         "COACH'S GOLDEN RULE", size=13, color=GOLD, bold=True)
add_text(s, Inches(0.7), Inches(5.1), Inches(5.9), Inches(1.8),
         "Never build alone in a silo. Every workflow is co-authored with an internal "
         "champion via \u201CSee One, Co-Build One, Lead One\u201D — the client owns 100% "
         "of the capability when the engagement ends.",
         size=12.5, color=LIGHT, line_spacing=1.2)

add_rect(s, Inches(7.0), Inches(1.4), Inches(5.9), Inches(5.65), WHITE, line=GRID)
add_text(s, Inches(7.25), Inches(1.55), Inches(5.4), Inches(0.35),
         "30-60-90 DAY EXECUTION CADENCE", size=13.5, color=NAVY, bold=True)
cadence = [
    ("DAYS 1–30 · Baseline & Quick-Win Pilot",
     "DORA baselines, LLM gateway + PII redaction, one high-visibility agent in shadow mode."),
    ("DAYS 31–60 · Production Cutover & Scaling",
     "Shadow \u2192 live with confidence gates, SDK workbench rollout, mid-point ROI review vs. Day-1 baseline."),
    ("DAYS 61–90 · Institutionalization & CoE",
     "Internal AI Champions own evals/registries/FinOps, patterns replicated cross-org, final ROI & IP review."),
]
yy = Inches(2.1)
for t, d in cadence:
    add_rect(s, Inches(7.25), yy, Inches(0.09), Inches(1.35), TEAL)
    add_text(s, Inches(7.5), yy, Inches(5.25), Inches(0.35), t,
             size=12.5, color=NAVY, bold=True)
    add_text(s, Inches(7.5), yy + Inches(0.36), Inches(5.25), Inches(0.95),
             d, size=11.5, color=SLATE, line_spacing=1.1)
    yy += Inches(1.6)

# ============================================================================
# SLIDE 8 — Section 03 Glossary
# ============================================================================
glossary_slide("03", "Measurement, Metrics & Mentoring", [
    ("Vanity Metrics",
     "Prompts run, Copilot seat activation, lines of AI-generated code.",
     "Banning them forces every initiative onto the four executive outcome dimensions tied to P&L."),
    ("DORA Metrics / MTTR",
     "Deployment frequency, lead time, change failure rate; mean time to restore incidents.",
     "Creates the Day-1 baseline that makes 90-day improvement claims defensible to executives."),
    ("Deflection Rate",
     "Share of inbound tickets/calls resolved autonomously with zero human touch.",
     "Converts AI output directly into OPEX savings the CFO can book."),
    ("Groundedness Score",
     "Degree to which agent answers trace back to retrieved, verified source facts.",
     "Gates customer-facing autonomy; keeps policy-violation rate under 0.5%."),
    ("30-60-90 Cadence",
     "Three transparent milestone gates: baseline \u2192 cutover \u2192 institutionalization.",
     "Keeps stakeholders seeing compounding returns and prevents open-ended pilots."),
    ("Center of Excellence (CoE) Handover",
     "Internal champions trained to run eval harnesses, agent registries, and FinOps alerts.",
     "Makes the coach progressively unnecessary — capability stays with the client."),
    ("See One, Co-Build One, Lead One",
     "Progressive co-authoring model for every workflow built during the engagement.",
     "Guarantees muscle memory transfer, not slide-deck dependency on consultants."),
])

# ============================================================================
# SLIDE 9 — Section 04 Summary: Client Pitch & Brochure
# ============================================================================
s = add_slide()
header(s, "04", "Client Pitch — Beyond Chatbots to Autonomous Execution",
       "Why most AI initiatives stall, and the proof points & commercial tiers that win engagements")
add_bullets(s, Inches(0.45), Inches(1.4), Inches(6.5), Inches(2.6), [
    ("The Executive Dilemma", "fewer than 15% of AI initiatives reach production "
     "with measurable ROI — most fall into the \u201CCopilot Trap.\u201D"),
    ("The Core Fallacy", "\u201Ca smarter prompt will solve our operations.\u201D LLMs are "
     "reasoning engines, not complete systems — they need guardrails, ontologies, evals and orchestration."),
    ("Next Step Offer", "45-minute executive architecture briefing: bring one stalled "
     "pilot, map an agentic path, define 90-day success metrics."),
], size=12.5)

stats = [("30–32%", "Call & ticket deflection"), ("69%", "Reduction in manual toil"),
         ("88%", "Deployment efficiency gain"), ("47%\u219217%", "Drop in user friction")]
sx = Inches(0.45)
for val, lab in stats:
    add_rect(s, sx, Inches(4.15), Inches(3.02), Inches(1.25), NAVY_2)
    add_text(s, sx, Inches(4.28), Inches(3.02), Inches(0.55), val,
             size=20, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
    add_text(s, sx + Inches(0.1), Inches(4.85), Inches(2.82), Inches(0.5), lab,
             size=10.5, color=LIGHT, align=PP_ALIGN.CENTER)
    sx += Inches(3.14)

tbl_shape = s.shapes.add_table(4, 3, Inches(0.45), Inches(5.6),
                               Inches(12.45), Inches(1.6))
tbl = tbl_shape.table
tbl.columns[0].width = Inches(3.4)
tbl.columns[1].width = Inches(2.2)
tbl.columns[2].width = Inches(6.85)
set_cell(tbl.cell(0, 0), "ENGAGEMENT TIER", 10.5, WHITE, True, NAVY)
set_cell(tbl.cell(0, 1), "DURATION", 10.5, WHITE, True, NAVY)
set_cell(tbl.cell(0, 2), "CORE DELIVERABLES", 10.5, WHITE, True, NAVY)
tiers = [
    ("Tier 1 · Diagnostic & Architecture Sprint", "2–3 weeks (fixed)",
     "5-Pillar readiness audit, Copilot\u2192Agent map, TCO/ROI model, 90-day blueprint."),
    ("Tier 2 · Fractional Head Coach & Co-Build", "3–6 months (retainer)",
     "Weekly architecture reviews, SDK & guardrails, production evals, squad mentoring."),
    ("Tier 3 · Executive & Board Advisory", "Quarterly / annual",
     "C-suite alignment, vendor due diligence, governance charter, KPI scorecard audits."),
]
for i, (a, b, c) in enumerate(tiers, 1):
    fill = ROW_ALT if i % 2 == 0 else WHITE
    set_cell(tbl.cell(i, 0), a, 10, NAVY, True, fill)
    set_cell(tbl.cell(i, 1), b, 10, SLATE, False, fill)
    set_cell(tbl.cell(i, 2), c, 10, SLATE, False, fill)

# ============================================================================
# SLIDE 10 — Section 04 Glossary
# ============================================================================
glossary_slide("04", "Client Pitch & Brochure", [
    ("Copilot Trap",
     "Treating generative AI as a standalone chat assistant instead of re-architecting workflows.",
     "Reframes the sales conversation from \u201Cbuy tools\u201D to \u201Credesign operations\u201D — the core wedge of the pitch."),
    ("Operational Deflection",
     "Intent-driven agents resolving inbound calls/tickets with no human involvement (30–32% benchmark).",
     "Quantifies immediate OPEX relief; the headline number executives remember."),
    ("Embedded Guardrails & Eval Gates",
     "LLM safety, automated evaluation and FinOps cost caps built into delivery — not post-hoc compliance.",
     "Converts legal/security from blockers into sponsors, accelerating production sign-off."),
    ("Knowledge-Graph RAG",
     "Retrieval grounded in structured domain graphs rather than raw document dumps.",
     "Delivers production-grade accuracy where shallow prompt-wrappers fail with latency and drift."),
    ("Milestone-Gated Engagement",
     "Fixed-scope sprints and retainers tied to measurable gates — never open-ended hourly billing.",
     "Aligns incentives on speed-to-value and contains client risk, making approval easier."),
    ("Executive Architecture Briefing",
     "45-minute session: one stalled pilot \u2192 agentic execution path + guardrail gaps + 90-day metrics.",
     "A low-friction entry point that converts skeptical leadership into a Tier-1 diagnostic sale."),
])

# ============================================================================
# SLIDE 11 — Section 05 Summary: Discovery & Diagnostic Audit
# ============================================================================
s = add_slide()
header(s, "05", "AI Discovery & Diagnostic Audit Checklist",
       "A 10-day field instrument to baseline maturity, expose risk, and qualify high-ROI agentic workflows")
add_text(s, Inches(0.45), Inches(1.35), Inches(6.4), Inches(0.35),
         "5-PILLAR READINESS RUBRIC (SCORED 1–5)", size=13, color=NAVY, bold=True)
add_bullets(s, Inches(0.45), Inches(1.75), Inches(6.4), Inches(2.9), [
    ("1. Strategy & KPI Alignment", "from vanity seats \u2192 real-time P&L telemetry."),
    ("2. Data & Domain Ontology", "from stale wikis \u2192 versioned knowledge graphs."),
    ("3. Agentic Architecture", "from chat wrappers \u2192 multi-agent state machines."),
    ("4. Trust, Safety & Evals", "from vibe-checks \u2192 LLM-as-a-Judge gates + drift alerts."),
    ("5. Engineering & FinOps", "from unbounded keys \u2192 dynamic routing & cost thresholds."),
], size=12, space_after=4)
add_rect(s, Inches(0.45), Inches(4.85), Inches(6.4), Inches(2.2), NAVY_2)
add_text(s, Inches(0.7), Inches(5.0), Inches(5.9), Inches(0.35),
         "HARD GATE", size=12.5, color=GOLD, bold=True)
add_text(s, Inches(0.7), Inches(5.38), Inches(5.9), Inches(1.6),
         "Any pillar scoring below 2.5 requires foundational remediation before "
         "autonomous agents are deployed to production. Red flags (e.g., AI code into "
         "<30% test coverage, big-bang mainframe rewrites) are stop conditions.",
         size=12, color=LIGHT, line_spacing=1.18)

add_rect(s, Inches(7.05), Inches(1.35), Inches(5.85), Inches(5.7), WHITE, line=GRID)
add_text(s, Inches(7.3), Inches(1.5), Inches(5.4), Inches(0.35),
         "UNIVERSAL AUDIT GATES + 10-DAY SPRINT", size=13, color=NAVY, bold=True)
add_bullets(s, Inches(7.3), Inches(1.95), Inches(5.4), Inches(2.6), [
    ("Baseline telemetry", "90 days of workflow logs must exist."),
    ("PII & lineage audit", "map sensitive data entering context windows; verify ZDR."),
    ("Determinism split", "rule-based code vs. LLM-reasoning steps."),
    ("Blast-radius classing", "Read-Only / Reversible / Irreversible (HITL)."),
    ("Unit-economics stress test", "cost-per-task at 10x volume."),
], size=11.5, space_after=3)
sprint = [("Days 1–3", "Baselines \u2192 Bottleneck & Cost Report"),
          ("Days 4–7", "Deep dive \u2192 Maturity Scorecard & Risk Register"),
          ("Days 8–10", "Blueprint \u2192 90-Day Execution & Mentoring Roadmap")]
yy = Inches(4.75)
for t, d in sprint:
    add_text(s, Inches(7.3), yy, Inches(1.5), Inches(0.35), t,
             size=11.5, color=TEAL, bold=True)
    add_text(s, Inches(8.75), yy, Inches(4.0), Inches(0.6), d,
             size=11.5, color=SLATE)
    yy += Inches(0.72)

# ============================================================================
# SLIDE 12 — Section 05 Glossary
# ============================================================================
glossary_slide("05", "Discovery & Diagnostic Audit", [
    ("5-Pillar Readiness Rubric",
     "1–5 maturity scoring: Strategy/KPI, Data/Ontology, Architecture, Trust/Evals, Engineering/FinOps.",
     "Pinpoints exactly which foundation to remediate first; below 2.5 blocks autonomous deployment."),
    ("Zero-Data-Retention (ZDR)",
     "Vendor agreements guaranteeing prompts/data are not stored or used for training.",
     "Satisfies CISO/legal data-boundary requirements — a prerequisite for enterprise sign-off."),
    ("Failure Blast-Radius",
     "Classifying each agent action as Read-Only, Reversible Write, or Irreversible External Action.",
     "Calibrates autonomy per action type; irreversible actions always keep human approval."),
    ("Determinism vs. Reasoning Split",
     "Separating strict rule-based steps (calculations, permissions, DB writes) from LLM reasoning steps.",
     "Prevents hallucination-prone models from executing deterministic business logic."),
    ("Unit Economics Stress Test",
     "Cost-per-task modeled at 10x current volume vs. human/legacy baseline.",
     "Kills workflows that only look profitable at pilot scale before money is wasted."),
    ("Critical Red Flags",
     "Stop conditions: auto-merge without static analysis, apologize-only chat agents, big-bang rewrites.",
     "Protects the client (and coach credibility) from catastrophic, trust-destroying failures."),
    ("Stakeholder Interview Protocol",
     "Persona-targeted diagnostic questions for CTO, VP Product, CISO and tech leads.",
     "Surfaces the costliest bottlenecks and approval constraints in days, not months."),
])

# ============================================================================
# SLIDE 13 — Section 06 Summary: Statistical Methods & ROI
# ============================================================================
s = add_slide()
header(s, "06", "Statistical Methods & Economic ROI Framework",
       "Replacing anecdotal \u201Cvibe checks\u201D with causal experiments and CFO-grade financial proof")
tbl_shape = s.shapes.add_table(5, 3, Inches(0.45), Inches(1.4),
                               Inches(12.45), Inches(2.75))
tbl = tbl_shape.table
tbl.columns[0].width = Inches(3.1)
tbl.columns[1].width = Inches(3.5)
tbl.columns[2].width = Inches(5.85)
set_cell(tbl.cell(0, 0), "CAUSAL METHOD", 11, WHITE, True, NAVY)
set_cell(tbl.cell(0, 1), "BEST DOMAIN FIT", 11, WHITE, True, NAVY)
set_cell(tbl.cell(0, 2), "PROTOCOL", 11, WHITE, True, NAVY)
methods = [
    ("Randomized Controlled Trial (A/B)", "PDLC & support deflection",
     "Stratified 50/50 or 80/20 session splits; measure conversion, CSAT, containment."),
    ("Shadow-Mode Paired Evaluation", "Legacy & critical triage",
     "Route 100% of inputs to both systems; paired equivalence tests before cutover."),
    ("Difference-in-Differences (DiD)", "SDLC squad productivity",
     "Pilot vs. control squads pre/post deployment; strips seasonal release noise."),
    ("Multi-Armed Bandit / Canary", "Startups & model FinOps",
     "Thompson Sampling shifts traffic across model tiers to maximize quality-per-dollar."),
]
for i, (a, b, c) in enumerate(methods, 1):
    fill = ROW_ALT if i % 2 == 0 else WHITE
    set_cell(tbl.cell(i, 0), a, 10.5, NAVY, True, fill)
    set_cell(tbl.cell(i, 1), b, 10.5, SLATE, False, fill)
    set_cell(tbl.cell(i, 2), c, 10.5, SLATE, False, fill)

add_rect(s, Inches(0.45), Inches(4.4), Inches(6.3), Inches(2.65), NAVY_2)
add_text(s, Inches(0.7), Inches(4.55), Inches(5.8), Inches(0.35),
         "CFO-READY ROI MODEL", size=13, color=GOLD, bold=True)
add_text(s, Inches(0.7), Inches(4.95), Inches(5.85), Inches(2.0),
         "Annualized Net AI Value = [Gross Operational Savings + Revenue Uplift]\n"
         "                                      \u2212 [Build TCO + Run TCO]\n\n"
         "Base case (100K monthly volume, 30% deflection): $1.23M Year-1 net value,\n"
         "1.5-month payback. Conservative case still pays back in 2.7 months.",
         size=11.5, color=LIGHT, line_spacing=1.15)
add_rect(s, Inches(7.0), Inches(4.4), Inches(5.9), Inches(2.65), WHITE, line=GRID)
add_text(s, Inches(7.25), Inches(4.55), Inches(5.4), Inches(0.35),
         "GOVERNANCE CADENCE", size=13, color=NAVY, bold=True)
add_bullets(s, Inches(7.25), Inches(4.95), Inches(5.45), Inches(2.0), [
    ("Weekly", "SPC run charts — success rate, guardrail triggers, token cost."),
    ("Bi-weekly", "error taxonomy & Pareto audit — fix the 20% causing 80% of failures."),
    ("Quarterly", "re-run DiD/A/B holdouts; benchmark cheaper models vs. golden datasets."),
], size=11.5, space_after=4)

# ============================================================================
# SLIDE 14 — Section 06 Glossary
# ============================================================================
glossary_slide("06", "Statistical Methods & AI ROI", [
    ("Minimum Detectable Effect (MDE)",
     "Smallest true improvement (\u22653–5%) an experiment is powered to detect at 95% confidence / 80% power.",
     "Sets correct sample sizes so wins are provable — and tiny, unprovable pilots are avoided."),
    ("Recall@K / MRR",
     "Retrieval quality: whether the right facts appear in the top-K results (Recall@5 \u2265 0.90 gate).",
     "Blocks agents from answering autonomously until grounding quality is proven."),
    ("Cohen's Kappa (\u03BA)",
     "Agreement between LLM-as-a-Judge and human experts on 200+ stratified samples.",
     "Automated CI/CD quality gating is enabled only at \u03BA \u2265 0.80 — scaling evals without losing trust."),
    ("NLI Entailment Check",
     "Verifying each high-risk answer is logically entailed by retrieved source facts.",
     "Enforces the <0.5% critical hallucination ceiling on customer-facing actions."),
    ("Population Stability Index (PSI)",
     "Statistical measure of input/intent distribution drift in production (recalibrate at PSI > 0.20).",
     "Triggers automated model/prompt recalibration before quality silently degrades."),
    ("Payback Period",
     "Implementation investment \u00F7 net monthly value (1.1–2.7 months across scenario cases).",
     "The single number that converts a technology pitch into an approved CFO budget line."),
    ("Pareto Error Taxonomy",
     "Failed traces classified as Retrieval Miss, Reasoning Error, Tool Failure, or Ambiguous Intent.",
     "Focuses engineering effort on the top 20% of root causes driving 80% of agent failures."),
])

# ============================================================================
# SLIDE 15 — Cross-Cutting Glossary → Impact Synthesis
# ============================================================================
s = add_slide()
header(s, "\u2605", "Master Synthesis — How the Glossary Drives Impact",
       "Five cross-cutting vocabulary clusters and the executive outcomes they unlock")
clusters = [
    ("GROUND IN TRUTH", "Knowledge graphs \u00B7 ontologies \u00B7 RAG grounding \u00B7 Recall@K",
     "Agents reason over the client's reality \u2192 production accuracy, not demo-ware.", TEAL),
    ("EARN TRUST FIRST", "Guardrails \u00B7 shadow mode \u00B7 HITL \u00B7 blast-radius \u00B7 ZDR",
     "Security & legal become sponsors \u2192 autonomy actually ships to production.", GOLD),
    ("PROVE, DON'T CLAIM", "A/B \u00B7 DiD \u00B7 MDE \u00B7 Kappa \u00B7 PSI \u00B7 payback period",
     "Causal, CFO-grade evidence \u2192 budgets renewed and programs scaled.", TEAL),
    ("ENGINEER THE ECONOMICS", "FinOps routing \u00B7 token caps \u00B7 unit-economics stress tests",
     "Margins protected at 10x scale \u2192 AI stays cheaper than the human baseline.", GOLD),
    ("TRANSFER THE CAPABILITY", "CoE \u00B7 role-based mentoring \u00B7 See One / Co-Build One / Lead One",
     "Client owns 100% of the muscle \u2192 transformation outlives the engagement.", TEAL),
]
yy = Inches(1.45)
for title, terms, impact, accent in clusters:
    add_rect(s, Inches(0.45), yy, Inches(12.45), Inches(1.04), WHITE, line=GRID)
    add_rect(s, Inches(0.45), yy, Inches(0.12), Inches(1.04), accent)
    add_text(s, Inches(0.75), yy + Inches(0.08), Inches(3.3), Inches(0.9),
             title, size=14, color=NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, Inches(4.1), yy + Inches(0.08), Inches(4.35), Inches(0.9),
             terms, size=10.5, color=SLATE, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, Inches(8.55), yy + Inches(0.08), Inches(4.2), Inches(0.9),
             impact, size=11, color=NAVY, bold=False, anchor=MSO_ANCHOR.MIDDLE)
    yy += Inches(1.14)

# ============================================================================
# SLIDE 16 — Closing / Call to Action
# ============================================================================
s = add_slide(NAVY)
add_rect(s, 0, Inches(2.0), SLIDE_W, Inches(0.05), TEAL)
add_text(s, Inches(0.9), Inches(0.9), Inches(11.5), Inches(1.0),
         "From Terminology to Transformation", size=36, color=WHITE, bold=True,
         font="Segoe UI Black")
steps = [
    ("1", "DIAGNOSE", "Run the 10-day 5-Pillar audit; score maturity and expose red flags."),
    ("2", "DESIGN", "Map Copilot\u2192Agent paths per domain track with guardrails from Day 1."),
    ("3", "DEPLOY", "Shadow-mode pilots \u2192 >95% precision \u2192 production cutover with gates."),
    ("4", "PROVE & TRANSFER", "Causal ROI evidence + CoE handover; the client owns the capability."),
]
sx = Inches(0.9)
for num, t, d in steps:
    add_rect(s, sx, Inches(2.6), Inches(2.78), Inches(2.5), NAVY_2)
    add_rect(s, sx, Inches(2.6), Inches(2.78), Inches(0.07), GOLD)
    add_text(s, sx + Inches(0.2), Inches(2.8), Inches(2.4), Inches(0.55),
             num, size=24, color=TEAL, bold=True, font="Segoe UI Black")
    add_text(s, sx + Inches(0.2), Inches(3.4), Inches(2.4), Inches(0.4),
             t, size=14, color=WHITE, bold=True)
    add_text(s, sx + Inches(0.2), Inches(3.85), Inches(2.4), Inches(1.15),
             d, size=10.5, color=LIGHT, line_spacing=1.12)
    sx += Inches(2.93)
add_text(s, Inches(0.9), Inches(5.65), Inches(11.5), Inches(0.9),
         "Next step: a 45-minute Executive Architecture Briefing — bring one stalled AI pilot "
         "or high-cost workflow;\nleave with an agentic execution path, guardrail gap list, and 90-day success metrics.",
         size=14, color=GOLD, line_spacing=1.25)
add_text(s, Inches(0.9), Inches(6.75), Inches(11.5), Inches(0.4),
         "AI Head Coach Practice Toolkit  |  Global Enterprise & Startup Advisory",
         size=11, color=RGBColor(0x9F, 0xC6, 0xE8))

# ----------------------------------------------------------------------------
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "AI_Head_Coach_Contents.pptx")
prs.save(OUT)
print(f"Saved: {OUT}  ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")
