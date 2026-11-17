"""Stage 1 — Pitch Simulator.

Computes a deterministic 12-month ROI comparison between Traditional Copilots
(12–18% individual task lift, significant license shelfware) and Autonomous
Agentic Workflows (30–65% end-to-end toil reduction, ticket deflection,
deployment velocity lift), plus tailored messaging across the 4 Pillars:
Vision, Trust, Depth, Solving.

All math is a transparent model — assumptions are returned in the payload so
coaches can defend every number in the room.
"""

from __future__ import annotations

from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/stage1", tags=["engine:stage1-pitch"])


class DomainTrack(str, Enum):
    SDLC = "SDLC"
    PDLC = "PDLC"
    STARTUP = "STARTUP"
    LEGACY = "LEGACY"


# --- Model assumptions (single source of truth, surfaced in the response) ----

FULLY_LOADED_ENGINEER_MONTHLY_COST = 12_500.0   # USD, blended global average
COST_PER_TICKET = 22.0                           # human-handled support ticket
COPILOT_LICENSE_PER_SEAT_MONTHLY = 39.0
COPILOT_SHELFWARE_RATE = 0.35                    # licenses paid but unused
COPILOT_TASK_LIFT = (0.12, 0.18)                 # individual task-level lift
COPILOT_TOIL_SHARE_ADDRESSED = 0.30              # share of work copilots touch
AGENTIC_TOIL_REDUCTION = (0.30, 0.65)            # end-to-end toil reduction
AGENTIC_TICKET_DEFLECTION = (0.25, 0.45)         # tickets never reaching humans
AGENTIC_DEPLOY_VELOCITY_LIFT = (0.20, 0.40)      # release throughput gain
AGENTIC_PLATFORM_COST_RATE = 0.06                # % of cloud spend for agents
ENGINEER_TOIL_SHARE = 0.40                       # engineering time that is toil

# Track-specific emphasis used for the 4-pillar messaging
_TRACK_ANGLE = {
    DomainTrack.SDLC: ("ship software", "PR review, test generation and AIOps toil"),
    DomainTrack.PDLC: ("learn from customers", "telemetry synthesis and digital deflection"),
    DomainTrack.STARTUP: ("find product-market fit", "lean agentic pods and token FinOps"),
    DomainTrack.LEGACY: ("modernize safely", "codebase archaeology and parity harnesses"),
}


class PitchRequest(BaseModel):
    industry: str = Field(min_length=1, max_length=120)
    domain_track: DomainTrack = Field(alias="domainTrack")
    engineering_headcount: int = Field(alias="engineeringHeadcount", ge=1, le=100_000)
    monthly_ticket_volume: int = Field(alias="monthlyTicketVolume", ge=0, le=10_000_000)
    current_cloud_spend: float = Field(alias="currentCloudSpend", ge=0, le=1e9,
                                       description="Monthly cloud spend in USD")

    model_config = {"populate_by_name": True}


def _range_value(bounds: tuple[float, float]) -> dict:
    low, high = bounds
    return {"low": low, "mid": round((low + high) / 2, 3), "high": high}


def compute_pitch(req: PitchRequest) -> dict:
    """Pure 12-month economics model — deterministic, assumption-transparent."""
    monthly_eng_cost = req.engineering_headcount * FULLY_LOADED_ENGINEER_MONTHLY_COST
    annual_eng_cost = monthly_eng_cost * 12
    annual_toil_cost = annual_eng_cost * ENGINEER_TOIL_SHARE
    annual_ticket_cost = req.monthly_ticket_volume * COST_PER_TICKET * 12

    # --- Traditional copilots -------------------------------------------------
    lift = _range_value(COPILOT_TASK_LIFT)
    # Copilots only touch the addressed share of toil; shelfware erodes licenses.
    copilot_gross = {
        k: round(annual_toil_cost * COPILOT_TOIL_SHARE_ADDRESSED * v, 2)
        for k, v in (("low", lift["low"]), ("mid", lift["mid"]), ("high", lift["high"]))
    }
    copilot_license_cost = round(
        req.engineering_headcount * COPILOT_LICENSE_PER_SEAT_MONTHLY * 12, 2)
    copilot_shelfware_waste = round(copilot_license_cost * COPILOT_SHELFWARE_RATE, 2)
    copilot_net = {k: round(v - copilot_license_cost, 2) for k, v in copilot_gross.items()}

    # --- Autonomous agentic workflows -----------------------------------------
    toil = _range_value(AGENTIC_TOIL_REDUCTION)
    deflect = _range_value(AGENTIC_TICKET_DEFLECTION)
    velocity = _range_value(AGENTIC_DEPLOY_VELOCITY_LIFT)
    agentic_platform_cost = round(req.current_cloud_spend * AGENTIC_PLATFORM_COST_RATE * 12, 2)

    agentic_gross, agentic_net = {}, {}
    for band in ("low", "mid", "high"):
        toil_savings = annual_toil_cost * toil[band]
        deflection_savings = annual_ticket_cost * deflect[band]
        # Velocity gain monetized conservatively at 25% of its throughput value.
        velocity_value = annual_eng_cost * velocity[band] * 0.25
        gross = toil_savings + deflection_savings + velocity_value
        agentic_gross[band] = round(gross, 2)
        agentic_net[band] = round(gross - agentic_platform_cost, 2)

    advantage_mid = round(agentic_net["mid"] - copilot_net["mid"], 2)

    verb, focus = _TRACK_ANGLE[req.domain_track]
    pillars = {
        "vision": (
            f"In {req.industry}, the winners will not be the teams with the most "
            f"copilot seats — they will be the ones whose agents {verb} end-to-end. "
            f"This is a 12-month architecture decision, not a tooling purchase."),
        "trust": (
            "Every agent action is gated: PII redaction, determinism thresholds, "
            "shadow-mode parity and human-in-the-loop sign-off — governance is "
            "built into the runway, not bolted on after an incident."),
        "depth": (
            f"We go beyond demos into {focus}, wired to your real backlog, "
            f"ticket stream and cloud estate — with measurable baselines from day one."),
        "solving": (
            f"At {req.engineering_headcount} engineers and "
            f"{req.monthly_ticket_volume:,} tickets/month, the mid-case agentic "
            f"advantage over copilots is ${advantage_mid:,.0f} in year one — "
            f"and we prove it statistically before you scale it."),
    }

    return {
        "industry": req.industry,
        "domainTrack": req.domain_track.value,
        "horizonMonths": 12,
        "baseline": {
            "annualEngineeringCost": round(annual_eng_cost, 2),
            "annualToilCost": round(annual_toil_cost, 2),
            "annualTicketHandlingCost": round(annual_ticket_cost, 2),
        },
        "traditionalCopilots": {
            "taskLiftRange": lift,
            "annualGrossSavings": copilot_gross,
            "annualLicenseCost": copilot_license_cost,
            "estimatedShelfwareWaste": copilot_shelfware_waste,
            "annualNetValue": copilot_net,
        },
        "agenticWorkflows": {
            "toilReductionRange": toil,
            "ticketDeflectionRange": deflect,
            "deployVelocityLiftRange": velocity,
            "annualPlatformCost": agentic_platform_cost,
            "annualGrossSavings": agentic_gross,
            "annualNetValue": agentic_net,
        },
        "agenticAdvantageMidCase": advantage_mid,
        "fourPillars": pillars,
        "assumptions": {
            "fullyLoadedEngineerMonthlyCost": FULLY_LOADED_ENGINEER_MONTHLY_COST,
            "engineerToilShare": ENGINEER_TOIL_SHARE,
            "costPerTicket": COST_PER_TICKET,
            "copilotLicensePerSeatMonthly": COPILOT_LICENSE_PER_SEAT_MONTHLY,
            "copilotShelfwareRate": COPILOT_SHELFWARE_RATE,
            "copilotToilShareAddressed": COPILOT_TOIL_SHARE_ADDRESSED,
            "agenticPlatformCostRateOfCloudSpend": AGENTIC_PLATFORM_COST_RATE,
            "velocityMonetizationFactor": 0.25,
        },
    }


@router.post("/pitch-simulator")
def pitch_simulator(req: PitchRequest) -> dict:
    """12-month Copilots vs Agentic Workflows ROI projection + 4-pillar pitch."""
    return compute_pitch(req)
