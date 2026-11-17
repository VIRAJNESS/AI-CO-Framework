"""Per-stage narrative registry.

Extracts a format-neutral content model from (stage_num, engagement_data,
stage_result) consumed identically by the PPTX and DOCX builders. Every
extractor is defensive: missing stage_result fields yield sensible defaults
so a deliverable can always be produced.
"""

from __future__ import annotations

from dataclasses import dataclass, field

STAGE_NAMES = {
    1: "Discovery & Audit",
    2: "Diagnostic & Baseline",
    3: "Pilot Design",
    4: "Execution & Coaching",
    5: "Measurement & ROI",
    6: "Scale & Handoff",
}

FOUR_PILLARS_DEFAULT = {
    "vision": "Agents that own outcomes end-to-end, not seat-by-seat tooling.",
    "trust": "Five governance gates enforced before anything ships.",
    "depth": "Wired into the real backlog, tickets and cloud estate.",
    "solving": "Statistically proven value before scale decisions.",
}

GOVERNANCE_ROWS_DEFAULT = [
    ("PII_REDACTION", "N/A", "Pending evaluation"),
    ("DETERMINISM_THRESHOLD", "N/A", "Pending evaluation"),
    ("SHADOW_PARITY", "N/A", "Pending evaluation"),
    ("HUMAN_IN_LOOP", "N/A", "Pending evaluation"),
    ("FINOPS_CAP", "N/A", "Pending evaluation"),
]


@dataclass
class StageContent:
    """Format-neutral deliverable content for one stage."""

    stage_num: int
    stage_name: str
    client_name: str
    industry: str
    domain_track: str
    executive_summary: str
    pillars: dict[str, str]
    key_findings: list[str] = field(default_factory=list)
    table_title: str = "Execution Detail"
    table_headers: list[str] = field(default_factory=list)
    table_rows: list[list[str]] = field(default_factory=list)
    governance_rows: list[tuple[str, str, str]] = field(
        default_factory=lambda: list(GOVERNANCE_ROWS_DEFAULT))
    next_steps: list[str] = field(default_factory=list)


def _fmt_money(value) -> str:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"


def _stage1(result: dict) -> dict:
    agentic = result.get("agenticWorkflows", {}).get("annualNetValue", {})
    copilot = result.get("traditionalCopilots", {}).get("annualNetValue", {})
    advantage = result.get("agenticAdvantageMidCase")
    pillars = result.get("fourPillars", FOUR_PILLARS_DEFAULT)
    summary = (
        f"Mid-case agentic net value {_fmt_money(agentic.get('mid'))}/yr vs "
        f"copilots {_fmt_money(copilot.get('mid'))}/yr — an advantage of "
        f"{_fmt_money(advantage)} in year one."
        if agentic else
        "12-month economics comparison of Traditional Copilots vs Autonomous "
        "Agentic Workflows across toil, deflection and velocity levers.")
    findings = [
        f"Copilot shelfware waste: "
        f"{_fmt_money(result.get('traditionalCopilots', {}).get('estimatedShelfwareWaste'))}",
        f"Agentic platform run-rate: "
        f"{_fmt_money(result.get('agenticWorkflows', {}).get('annualPlatformCost'))}",
        "Velocity monetized conservatively at 25% of throughput value.",
    ]
    rows = []
    for band in ("low", "mid", "high"):
        rows.append([band.upper(), _fmt_money(copilot.get(band)),
                     _fmt_money(agentic.get(band))])
    return {
        "executive_summary": summary,
        "pillars": pillars,
        "key_findings": findings,
        "table_title": "Annual Net Value by Scenario",
        "table_headers": ["Scenario", "Traditional Copilots", "Agentic Workflows"],
        "table_rows": rows,
        "next_steps": [
            "Approve a Diagnostic Sprint to baseline toil and ticket economics",
            "Select the flagship workflow for the first agentic pilot",
            "Nominate executive sponsor and governance owners",
        ],
    }


def _stage2(result: dict) -> dict:
    maturity = result.get("maturityIndex", "—")
    band = result.get("maturityBand", "UNKNOWN")
    red_flags = result.get("criticalRedFlags", [])
    roadmap = result.get("remediationRoadmap", [])
    summary = (f"Maturity Index {maturity}/100 ({band}). "
               + (f"{len(red_flags)} critical blocker(s) identified: "
                  f"{', '.join(red_flags)}." if red_flags
                  else "No critical blockers identified."))
    rows = [[str(item.get("priority", "")),
             item.get("pillar", "").replace("_", " ").title(),
             str(item.get("currentScore", "")),
             "YES" if item.get("isCriticalBlocker") else "no"]
            for item in roadmap[:5]]
    return {
        "executive_summary": summary,
        "pillars": FOUR_PILLARS_DEFAULT,
        "key_findings": [item.get("recommendation", "") for item in roadmap[:3]],
        "table_title": "Prioritized Remediation Roadmap",
        "table_headers": ["Priority", "Pillar", "Score", "Blocker"],
        "table_rows": rows,
        "next_steps": [
            "Remediate critical red-flag pillars before pilot launch",
            "Re-run the diagnostic audit after remediation sprint",
            "Baseline the KPIs tied to the weakest pillars",
        ],
    }


def _stage3(result: dict) -> dict:
    components = result.get("components", [])
    theme_line = result.get("theme", "tailored execution architecture")
    summary = (f"Execution blueprint — {theme_line}: "
               f"{len(components)} core components with "
               f"{sum(len(c.get('agents', [])) for c in components)} agent roles.")
    rows = [[c.get("name", ""), ", ".join(c.get("agents", [])),
             ", ".join(c.get("kpis", []))] for c in components]
    return {
        "executive_summary": summary,
        "pillars": FOUR_PILLARS_DEFAULT,
        "key_findings": [c.get("purpose", "") for c in components],
        "table_title": "Blueprint Components",
        "table_headers": ["Component", "Agents", "KPIs"],
        "table_rows": rows,
        "next_steps": [
            "Confirm integration owners for each component",
            "Stand up the shared retrieval/ontology foundation",
            "Schedule pilot build kickoff with the platform team",
        ],
    }


def _stage4(result: dict) -> dict:
    trace = result.get("trace", [])
    verdict = result.get("finalVerdict", "PENDING")
    intent = next((s.get("detectedIntent") for s in trace if s.get("step") == 1), "—")
    guard = next((s for s in trace if s.get("step") == 2), {})
    evaluator = next((s for s in trace if s.get("step") == 4), {})
    summary = (f"Live multi-agent proof on a {intent} artifact — final verdict "
               f"{verdict} (confidence {evaluator.get('confidence', '—')}, "
               f"shadow diff {evaluator.get('shadowDiffScore', '—')}).")
    rows = [[str(s.get("step", "")), s.get("name", ""),
             s.get("status") or s.get("mode") or s.get("verdict")
             or s.get("detectedIntent", "")]
            for s in trace]
    return {
        "executive_summary": summary,
        "pillars": FOUR_PILLARS_DEFAULT,
        "key_findings": [
            f"PII findings: {guard.get('findings', {}) or 'none'}",
            f"Worker mode: "
            f"{next((s.get('mode') for s in trace if s.get('step') == 3), '—')}",
            f"Evaluator verdict: {verdict}",
        ],
        "table_title": "4-Step Agent Trace",
        "table_headers": ["Step", "Agent", "Outcome"],
        "table_rows": rows,
        "next_steps": [
            "Replay the demo on three more real artifacts from the backlog",
            "Wire the evaluator thresholds into CI as governance gates",
            "Plan the shadow-mode rollout for the chosen workflow",
        ],
    }


def _stage5(result: dict) -> dict:
    findings, rows = [], []
    ab = result.get("abTest")
    if ab:
        findings.append(
            f"A/B lift {ab.get('meanDifference', 0):.2f} "
            f"(p={ab.get('welchT', {}).get('pValue', 1):.4f}; "
            f"{'significant' if ab.get('significantAt005') else 'not significant'}).")
        rows.append(["A/B Welch t", f"p={ab.get('welchT', {}).get('pValue', 1):.4f}",
                     "PASS" if ab.get("significantAt005") else "REVIEW"])
    did = result.get("did")
    if did:
        findings.append(f"DiD causal lift: {did.get('didLift', 0):.2f}.")
        rows.append(["DiD lift", f"{did.get('didLift', 0):.2f}",
                     "PASS" if did.get("didLift", 0) > 0 else "REVIEW"])
    judge = result.get("judgeAgreement")
    if judge:
        rows.append(["Cohen's Kappa", str(judge.get("cohensKappa", "—")),
                     judge.get("agreementBand", "—")])
    hallucination = result.get("hallucination")
    if hallucination:
        rows.append(["Hallucination rate",
                     f"{hallucination.get('hallucinationRate', 0):.2%}",
                     "PASS" if hallucination.get("withinProductionThreshold")
                     else "FAIL"])
    drift = result.get("drift")
    if drift:
        rows.append(["PSI drift", str(drift.get("psi", "—")),
                     drift.get("alertLevel", "—")])
    econ = result.get("economics")
    if econ:
        findings.append(f"Net Economic Value {_fmt_money(econ.get('netEconomicValue'))} "
                        f"({econ.get('cfoVerdict', '—')}).")
        rows.append(["Net Economic Value",
                     _fmt_money(econ.get("netEconomicValue")),
                     econ.get("cfoVerdict", "—")])
    summary = (" ".join(findings) if findings
               else "Statistical evaluation package across A/B, causal, "
                    "agreement, drift and economic dimensions.")
    return {
        "executive_summary": summary,
        "pillars": FOUR_PILLARS_DEFAULT,
        "key_findings": findings or ["Awaiting measurement data."],
        "table_title": "Statistical Evidence Summary",
        "table_headers": ["Metric", "Value", "Status"],
        "table_rows": rows or [["—", "—", "—"]],
        "next_steps": [
            "Review evidence with the CFO and engineering leadership",
            "Take the scale/no-scale decision on statistical grounds",
            "Set drift monitors and re-evaluation cadence",
        ],
    }


def _stage6(result: dict) -> dict:
    plan = result.get("plan", [])
    curriculum = result.get("mentoringCurriculum", [])
    summary = (f"30-60-90 execution plan with {len(curriculum)} role-track "
               f"mentoring curricula (See One / Co-Build One / Lead One).")
    rows = [[p.get("window", ""), p.get("theme", ""),
             "; ".join(p.get("targetKpis", []))] for p in plan]
    findings = [f"{c.get('roleTrack', '')}: "
                + " → ".join(ph.get("module", "") for ph in c.get("phases", []))
                for c in curriculum[:4]]
    return {
        "executive_summary": summary,
        "pillars": FOUR_PILLARS_DEFAULT,
        "key_findings": findings or ["Curriculum pending role-track selection."],
        "table_title": "30-60-90 Plan",
        "table_headers": ["Window", "Theme", "Target KPIs"],
        "table_rows": rows or [["—", "—", "—"]],
        "next_steps": [
            "Confirm mentors and cohort calendars per role track",
            "Publish the 30-60-90 plan to the engagement workspace",
            "Schedule the day-90 scale decision review",
        ],
    }


_EXTRACTORS = {1: _stage1, 2: _stage2, 3: _stage3,
               4: _stage4, 5: _stage5, 6: _stage6}


def build_content(stage_num: int, engagement_data: dict,
                  stage_result: dict) -> StageContent:
    """Build the format-neutral content model for a stage deliverable."""
    if stage_num not in STAGE_NAMES:
        raise ValueError(f"stageNum must be 1..6, got {stage_num}")

    extracted = _EXTRACTORS[stage_num](stage_result or {})

    # Governance rows from stage_result when present (e.g. core-api forwards them).
    gates = (stage_result or {}).get("governanceGates")
    governance_rows = list(GOVERNANCE_ROWS_DEFAULT)
    if isinstance(gates, list) and gates and isinstance(gates[0], dict):
        governance_rows = [
            (g.get("gateName", "—"), g.get("status", "N/A"), g.get("notes") or "—")
            for g in gates
        ]

    return StageContent(
        stage_num=stage_num,
        stage_name=STAGE_NAMES[stage_num],
        client_name=(engagement_data or {}).get("clientName", "Client"),
        industry=(engagement_data or {}).get("industry", "—"),
        domain_track=(engagement_data or {}).get("domainTrack", "—"),
        governance_rows=governance_rows,
        **extracted,
    )
