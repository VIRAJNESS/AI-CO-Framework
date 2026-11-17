"""Stage 2 — Diagnostic & Maturity Audit.

Scores 1–5 across the 5 Pillars (Strategy & KPI Alignment, Data & Ontology
Readiness, Cloud & Agent Architecture, Responsible AI & Guardrails,
Talent & PDLC Culture) plus optional track-specific probes. Computes a
0–100 Maturity Index, flags critical blockers (score <= 2) and produces a
prioritized remediation roadmap.
"""

from __future__ import annotations

from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.engine.stage1_pitch import DomainTrack

router = APIRouter(prefix="/stage2", tags=["engine:stage2-audit"])


class Pillar(str, Enum):
    STRATEGY_KPI = "STRATEGY_KPI_ALIGNMENT"
    DATA_ONTOLOGY = "DATA_ONTOLOGY_READINESS"
    CLOUD_AGENT_ARCH = "CLOUD_AGENT_ARCHITECTURE"
    RESPONSIBLE_AI = "RESPONSIBLE_AI_GUARDRAILS"
    TALENT_CULTURE = "TALENT_PDLC_CULTURE"


# Pillar weights sum to 1.0; architecture & guardrails weigh slightly more
# because they gate everything downstream.
_PILLAR_WEIGHTS: dict[Pillar, float] = {
    Pillar.STRATEGY_KPI: 0.20,
    Pillar.DATA_ONTOLOGY: 0.20,
    Pillar.CLOUD_AGENT_ARCH: 0.22,
    Pillar.RESPONSIBLE_AI: 0.22,
    Pillar.TALENT_CULTURE: 0.16,
}

_REMEDIATIONS: dict[Pillar, str] = {
    Pillar.STRATEGY_KPI: (
        "Define 3-5 executive KPIs tied to agent outcomes (cycle time, deflection "
        "rate, cost-to-serve) and publish a quarterly AI value scorecard."),
    Pillar.DATA_ONTOLOGY: (
        "Stand up a canonical ontology for your core entities and a retrieval "
        "corpus with ownership, freshness SLAs and PII classification."),
    Pillar.CLOUD_AGENT_ARCH: (
        "Adopt a reference agent architecture: router, worker agents, evaluator, "
        "artifact store — environment-switchable via 12-factor configuration."),
    Pillar.RESPONSIBLE_AI: (
        "Implement the 5 governance gates (PII redaction, determinism threshold, "
        "shadow parity, human-in-loop, FinOps cap) as hard pre-deployment checks."),
    Pillar.TALENT_CULTURE: (
        "Launch role-track mentoring (See One / Co-Build One / Lead One) for "
        "C-suite, architects, engineers and product managers."),
}

_TRACK_PROBE_HINT = {
    DomainTrack.SDLC: "CI/CD telemetry coverage and PR review automation depth",
    DomainTrack.PDLC: "customer telemetry pipelines and experiment velocity",
    DomainTrack.STARTUP: "unit-economics instrumentation and token budgets",
    DomainTrack.LEGACY: "codebase inventory completeness and parity test harnesses",
}


class TrackProbe(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    score: int = Field(ge=1, le=5)


class AuditRequest(BaseModel):
    domain_track: DomainTrack = Field(alias="domainTrack")
    pillar_scores: dict[Pillar, int] = Field(alias="pillarScores")
    track_probes: list[TrackProbe] = Field(alias="trackProbes", default_factory=list)

    model_config = {"populate_by_name": True}


def compute_audit(req: AuditRequest) -> dict:
    """Weighted maturity index + red flags + prioritized remediation roadmap."""
    missing = [p.value for p in Pillar if p not in req.pillar_scores]
    if missing:
        raise ValueError(f"Missing pillar scores: {', '.join(missing)}")
    for pillar, score in req.pillar_scores.items():
        if not 1 <= score <= 5:
            raise ValueError(f"Score for {pillar.value} must be 1..5, got {score}")

    # Weighted pillar index normalized to 0..100 (1 => 0, 5 => 100).
    weighted = sum(
        _PILLAR_WEIGHTS[p] * (req.pillar_scores[p] - 1) / 4.0 for p in Pillar)
    # Track probes refine (not dominate): 85% pillars / 15% probes when present.
    if req.track_probes:
        probe_avg = sum((pr.score - 1) / 4.0 for pr in req.track_probes) / len(req.track_probes)
        maturity = (0.85 * weighted + 0.15 * probe_avg) * 100
    else:
        maturity = weighted * 100
    maturity = round(maturity, 1)

    band = ("AD_HOC" if maturity < 25 else
            "EMERGING" if maturity < 50 else
            "SCALING" if maturity < 75 else "TRANSFORMATIVE")

    red_flags = sorted(
        (p for p in Pillar if req.pillar_scores[p] <= 2),
        key=lambda p: (req.pillar_scores[p], -_PILLAR_WEIGHTS[p]))
    probe_flags = [pr.name for pr in req.track_probes if pr.score <= 2]

    # Roadmap: red flags first (ascending score, descending weight), then the
    # weakest remaining pillars.
    ordered = sorted(Pillar, key=lambda p: (req.pillar_scores[p], -_PILLAR_WEIGHTS[p]))
    roadmap = [
        {
            "priority": idx + 1,
            "pillar": p.value,
            "currentScore": req.pillar_scores[p],
            "isCriticalBlocker": req.pillar_scores[p] <= 2,
            "recommendation": _REMEDIATIONS[p],
        }
        for idx, p in enumerate(ordered)
    ]

    return {
        "domainTrack": req.domain_track.value,
        "maturityIndex": maturity,
        "maturityBand": band,
        "pillarScores": {p.value: req.pillar_scores[p] for p in Pillar},
        "criticalRedFlags": [p.value for p in red_flags],
        "trackProbeRedFlags": probe_flags,
        "trackProbeHint": _TRACK_PROBE_HINT[req.domain_track],
        "remediationRoadmap": roadmap,
    }


@router.post("/diagnostic-audit")
def diagnostic_audit(req: AuditRequest) -> dict:
    """5-pillar maturity audit with red-flag blockers and remediation roadmap."""
    try:
        return compute_audit(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
