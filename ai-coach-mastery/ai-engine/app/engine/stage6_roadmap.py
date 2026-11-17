"""Stage 6 — 30-60-90 Day Roadmap & Role-Based Mentoring.

Generates a customized 30-60-90 day execution plan and a mentoring curriculum
per role track following the See One / Co-Build One / Lead One progression,
each phase with target KPIs. Track-aware so the plan speaks the client's
delivery language.
"""

from __future__ import annotations

from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.engine.stage1_pitch import DomainTrack

router = APIRouter(prefix="/stage6", tags=["engine:stage6-roadmap"])


class RoleTrack(str, Enum):
    C_SUITE = "C_SUITE"
    ARCHITECT = "ARCHITECT"
    ENGINEER = "ENGINEER"
    PRODUCT_MANAGER = "PRODUCT_MANAGER"


class RoadmapRequest(BaseModel):
    domain_track: DomainTrack = Field(alias="domainTrack")
    role_tracks: list[RoleTrack] = Field(
        alias="roleTracks",
        default_factory=lambda: list(RoleTrack))
    maturity_index: float | None = Field(alias="maturityIndex", default=None,
                                         ge=0, le=100)

    model_config = {"populate_by_name": True}


_TRACK_FLAGSHIP = {
    DomainTrack.SDLC: "automated PR review + test generation pilot",
    DomainTrack.PDLC: "intent-driven deflection pilot on the top support intent",
    DomainTrack.STARTUP: "one lean agentic pod with token FinOps guardrails",
    DomainTrack.LEGACY: "codebase archaeology sweep + parity harness on one module",
}

_CURRICULUM: dict[RoleTrack, dict] = {
    RoleTrack.C_SUITE: {
        "seeOne": {
            "module": "AI Value Storytelling & Governance Literacy",
            "kpis": ["can articulate the 5 governance gates",
                     "sponsors a published AI value scorecard"],
        },
        "coBuildOne": {
            "module": "Co-own one quarterly AI KPI review",
            "kpis": ["chairs 1 metric deep-dive", "approves gate thresholds"],
        },
        "leadOne": {
            "module": "Lead the scale/no-scale investment decision",
            "kpis": ["decision backed by DiD + NEV evidence",
                     "communicates outcome org-wide"],
        },
    },
    RoleTrack.ARCHITECT: {
        "seeOne": {
            "module": "Reference Agent Architecture Walkthrough",
            "kpis": ["maps current estate to router/worker/evaluator pattern"],
        },
        "coBuildOne": {
            "module": "Co-design the retrieval/ontology core",
            "kpis": ["retrieval precision >= 0.8 on golden set",
                     "12-factor provider switches implemented"],
        },
        "leadOne": {
            "module": "Lead one production agent workflow end-to-end",
            "kpis": ["shadow parity >= 0.92 before cutover",
                     "runbook + rollback documented"],
        },
    },
    RoleTrack.ENGINEER: {
        "seeOne": {
            "module": "Prompt Engineering & Eval Foundations",
            "kpis": ["passes eval-writing exercise", "uses prompt registry"],
        },
        "coBuildOne": {
            "module": "Co-build a worker agent with guardrails",
            "kpis": ["agent passes PII + determinism gates in CI"],
        },
        "leadOne": {
            "module": "Own an agent's reliability budget",
            "kpis": ["confidence >= 0.85 sustained 4 weeks",
                     "hallucination rate <= 5%"],
        },
    },
    RoleTrack.PRODUCT_MANAGER: {
        "seeOne": {
            "module": "Signal-to-Backlog: telemetry synthesis literacy",
            "kpis": ["reads friction-theme reports unaided"],
        },
        "coBuildOne": {
            "module": "Co-design one agentic experiment",
            "kpis": ["hypothesis with measurable success metric",
                     "experiment shipped within one cycle"],
        },
        "leadOne": {
            "module": "Lead a deflection or velocity KPI",
            "kpis": ["KPI improves with statistical significance",
                     "owns the executive narrative"],
        },
    },
}


def build_roadmap(req: RoadmapRequest) -> dict:
    """30-60-90 plan + per-role curriculum, tuned by maturity when supplied."""
    flagship = _TRACK_FLAGSHIP[req.domain_track]
    low_maturity = req.maturity_index is not None and req.maturity_index < 50

    day30 = {
        "window": "Days 1-30",
        "theme": "Baseline & Foundations",
        "actions": [
            "Instrument baseline metrics (cycle time, ticket cost, toil share)",
            "Stand up governance gates as hard CI checks",
            "Run discovery audit and publish maturity scorecard",
            *(["Remediate critical red-flag pillars before any pilot"]
              if low_maturity else []),
        ],
        "targetKpis": ["baseline dashboard live", "5 gates enforced in CI"],
    }
    day60 = {
        "window": "Days 31-60",
        "theme": "Flagship Pilot",
        "actions": [
            f"Launch the {flagship}",
            "Run pilot in shadow mode with parity scoring",
            "Start See One mentoring sessions for all enrolled role tracks",
        ],
        "targetKpis": ["pilot live in shadow mode", "shadow parity >= 0.90",
                       "100% See One attendance"],
    }
    day90 = {
        "window": "Days 61-90",
        "theme": "Prove & Decide",
        "actions": [
            "A/B or DiD evaluation of pilot vs control",
            "CFO Net Economic Value review with real run-rate costs",
            "Co-Build One mentoring underway; scale/no-scale decision taken",
        ],
        "targetKpis": ["statistically significant lift (p < 0.05)",
                       "NEV positive", "scale decision documented"],
    }

    curriculum = [
        {
            "roleTrack": role.value,
            "phases": [
                {"phase": "SEE_ONE", **_CURRICULUM[role]["seeOne"]},
                {"phase": "CO_BUILD_ONE", **_CURRICULUM[role]["coBuildOne"]},
                {"phase": "LEAD_ONE", **_CURRICULUM[role]["leadOne"]},
            ],
        }
        for role in req.role_tracks
    ]

    return {
        "domainTrack": req.domain_track.value,
        "maturityIndex": req.maturity_index,
        "maturityAdjusted": low_maturity,
        "plan": [day30, day60, day90],
        "mentoringCurriculum": curriculum,
    }


@router.post("/roadmap-mentor")
def roadmap_mentor(req: RoadmapRequest) -> dict:
    """Customized 30-60-90 execution plan + See/Co-Build/Lead One curriculum."""
    return build_roadmap(req)
