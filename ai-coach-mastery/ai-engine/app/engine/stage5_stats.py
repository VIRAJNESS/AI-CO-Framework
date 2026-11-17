"""Stage 5 — Statistical ROI & Evaluation Suite.

Implements the AI Head Coach measurement toolkit with scipy/numpy:

  - abTest        : Welch's t-test + Mann-Whitney U + 95% CI of the mean diff
  - did           : Difference-in-Differences causal lift estimator
  - judgeAgreement: Cohen's Kappa (LLM-as-a-Judge vs human SMEs)
  - hallucination : NLI-labelled hallucination rate with Wilson 95% CI
  - drift         : Population Stability Index (PSI) with alert bands
  - economics     : CFO Net Economic Value & TCO model

Every analysis block is optional — the endpoint computes exactly what it is
given. Pure functions first; the router is a thin shell.
"""

from __future__ import annotations

import math

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from scipy import stats

router = APIRouter(prefix="/stage5", tags=["engine:stage5-stats"])


# --- Schemas -------------------------------------------------------------------


class AbTestInput(BaseModel):
    control: list[float] = Field(min_length=2)
    treatment: list[float] = Field(min_length=2)


class DidInput(BaseModel):
    treatment_pre: list[float] = Field(alias="treatmentPre", min_length=2)
    treatment_post: list[float] = Field(alias="treatmentPost", min_length=2)
    control_pre: list[float] = Field(alias="controlPre", min_length=2)
    control_post: list[float] = Field(alias="controlPost", min_length=2)

    model_config = {"populate_by_name": True}


class JudgeAgreementInput(BaseModel):
    llm_labels: list[str] = Field(alias="llmLabels", min_length=2)
    human_labels: list[str] = Field(alias="humanLabels", min_length=2)

    model_config = {"populate_by_name": True}


class HallucinationInput(BaseModel):
    total_claims: int = Field(alias="totalClaims", ge=1)
    contradicted_claims: int = Field(alias="contradictedClaims", ge=0)

    model_config = {"populate_by_name": True}


class DriftInput(BaseModel):
    baseline: list[float] = Field(min_length=10)
    current: list[float] = Field(min_length=10)
    buckets: int = Field(default=10, ge=4, le=50)


class EconomicsInput(BaseModel):
    annual_gross_savings: float = Field(alias="annualGrossSavings", ge=0)
    annual_inference_cost: float = Field(alias="annualInferenceCost", ge=0)
    annual_orchestration_cost: float = Field(alias="annualOrchestrationCost", ge=0)
    annual_governance_cost: float = Field(alias="annualGovernanceCost", ge=0)
    one_time_implementation: float = Field(alias="oneTimeImplementation", ge=0, default=0)

    model_config = {"populate_by_name": True}


class StatisticalRoiRequest(BaseModel):
    ab_test: AbTestInput | None = Field(alias="abTest", default=None)
    did: DidInput | None = None
    judge_agreement: JudgeAgreementInput | None = Field(alias="judgeAgreement", default=None)
    hallucination: HallucinationInput | None = None
    drift: DriftInput | None = None
    economics: EconomicsInput | None = None

    model_config = {"populate_by_name": True}


# --- Pure analysis functions ------------------------------------------------------


def analyze_ab(inp: AbTestInput) -> dict:
    """Welch's t-test, Mann-Whitney U, and Welch-Satterthwaite 95% CI."""
    control = np.asarray(inp.control, dtype=float)
    treatment = np.asarray(inp.treatment, dtype=float)

    t_stat, t_p = stats.ttest_ind(treatment, control, equal_var=False)
    try:
        u_stat, u_p = stats.mannwhitneyu(treatment, control, alternative="two-sided")
    except ValueError:  # identical values edge case
        u_stat, u_p = float("nan"), 1.0

    diff = float(treatment.mean() - control.mean())
    se = math.sqrt(treatment.var(ddof=1) / len(treatment) + control.var(ddof=1) / len(control))
    if se > 0:
        df_num = (treatment.var(ddof=1) / len(treatment) + control.var(ddof=1) / len(control)) ** 2
        df_den = ((treatment.var(ddof=1) / len(treatment)) ** 2 / (len(treatment) - 1)
                  + (control.var(ddof=1) / len(control)) ** 2 / (len(control) - 1))
        dof = df_num / df_den if df_den > 0 else len(treatment) + len(control) - 2
        t_crit = stats.t.ppf(0.975, dof)
        ci = (diff - t_crit * se, diff + t_crit * se)
    else:
        ci = (diff, diff)  # zero variance edge: degenerate CI at the point

    return {
        "meanControl": float(control.mean()),
        "meanTreatment": float(treatment.mean()),
        "meanDifference": diff,
        "welchT": {"statistic": float(t_stat), "pValue": float(t_p)},
        "mannWhitney": {"statistic": float(u_stat), "pValue": float(u_p)},
        "ci95": {"low": float(ci[0]), "high": float(ci[1])},
        "significantAt005": bool(t_p < 0.05),
    }


def analyze_did(inp: DidInput) -> dict:
    """Difference-in-Differences: (T_post - T_pre) - (C_post - C_pre)."""
    t_pre = float(np.mean(inp.treatment_pre))
    t_post = float(np.mean(inp.treatment_post))
    c_pre = float(np.mean(inp.control_pre))
    c_post = float(np.mean(inp.control_post))
    lift = (t_post - t_pre) - (c_post - c_pre)
    relative = lift / abs(t_pre) * 100 if t_pre != 0 else None
    return {
        "treatmentDelta": t_post - t_pre,
        "controlDelta": c_post - c_pre,
        "didLift": lift,
        "relativeLiftPct": relative,
        "interpretation": (
            "Positive causal lift attributable to the intervention"
            if lift > 0 else
            "No positive causal lift detected — investigate confounders"),
    }


def cohens_kappa(a: list[str], b: list[str]) -> float:
    """Cohen's Kappa for two raters over identical items."""
    if len(a) != len(b):
        raise ValueError("Label lists must be the same length")
    labels = sorted(set(a) | set(b))
    n = len(a)
    observed = sum(1 for x, y in zip(a, b) if x == y) / n
    expected = sum(
        (a.count(lbl) / n) * (b.count(lbl) / n) for lbl in labels)
    if expected == 1.0:
        return 1.0  # degenerate: both raters constant and identical
    return (observed - expected) / (1 - expected)


def analyze_judge(inp: JudgeAgreementInput) -> dict:
    kappa = cohens_kappa(inp.llm_labels, inp.human_labels)
    band = ("POOR" if kappa < 0.20 else
            "FAIR" if kappa < 0.40 else
            "MODERATE" if kappa < 0.60 else
            "SUBSTANTIAL" if kappa < 0.80 else "ALMOST_PERFECT")
    return {
        "cohensKappa": round(float(kappa), 4),
        "agreementBand": band,
        "sampleSize": len(inp.llm_labels),
        "judgeTrustworthy": bool(kappa >= 0.60),
    }


def analyze_hallucination(inp: HallucinationInput) -> dict:
    """NLI contradiction rate with a Wilson score 95% interval."""
    if inp.contradicted_claims > inp.total_claims:
        raise ValueError("contradictedClaims cannot exceed totalClaims")
    p = inp.contradicted_claims / inp.total_claims
    n = inp.total_claims
    z = 1.959963985
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return {
        "hallucinationRate": round(p, 4),
        "wilsonCi95": {"low": round(max(0.0, center - margin), 4),
                       "high": round(min(1.0, center + margin), 4)},
        "withinProductionThreshold": bool(p <= 0.05),
        "threshold": 0.05,
    }


def population_stability_index(baseline: list[float], current: list[float],
                               buckets: int = 10) -> float:
    """PSI over quantile buckets of the baseline distribution."""
    base = np.asarray(baseline, dtype=float)
    curr = np.asarray(current, dtype=float)
    edges = np.unique(np.quantile(base, np.linspace(0, 1, buckets + 1)))
    if len(edges) < 3:
        return 0.0  # constant baseline — no informative buckets
    edges[0], edges[-1] = -np.inf, np.inf
    base_counts, _ = np.histogram(base, bins=edges)
    curr_counts, _ = np.histogram(curr, bins=edges)
    # Laplace smoothing avoids div-by-zero on empty buckets.
    base_pct = (base_counts + 1) / (base_counts.sum() + len(base_counts))
    curr_pct = (curr_counts + 1) / (curr_counts.sum() + len(curr_counts))
    return float(np.sum((curr_pct - base_pct) * np.log(curr_pct / base_pct)))


def analyze_drift(inp: DriftInput) -> dict:
    psi = population_stability_index(inp.baseline, inp.current, inp.buckets)
    alert = ("STABLE" if psi < 0.10 else
             "MODERATE_DRIFT" if psi < 0.25 else "SEVERE_DRIFT")
    return {
        "psi": round(psi, 4),
        "alertLevel": alert,
        "thresholds": {"stable": 0.10, "severe": 0.25},
        "actionRequired": bool(psi >= 0.25),
    }


def analyze_economics(inp: EconomicsInput) -> dict:
    """CFO view: Net Economic Value = gross savings − run-rate overheads."""
    overhead = (inp.annual_inference_cost + inp.annual_orchestration_cost
                + inp.annual_governance_cost)
    nev = inp.annual_gross_savings - overhead
    tco = overhead + inp.one_time_implementation
    roi_pct = (nev / tco * 100) if tco > 0 else None
    payback_months = (
        round(inp.one_time_implementation / (nev / 12), 1)
        if nev > 0 and inp.one_time_implementation > 0 else
        0.0 if inp.one_time_implementation == 0 else None)
    return {
        "annualGrossSavings": inp.annual_gross_savings,
        "annualOverhead": overhead,
        "netEconomicValue": nev,
        "totalCostOfOwnershipYear1": tco,
        "roiPct": round(roi_pct, 1) if roi_pct is not None else None,
        "paybackMonths": payback_months,
        "cfoVerdict": "VALUE_POSITIVE" if nev > 0 else "VALUE_NEGATIVE",
    }


@router.post("/statistical-roi")
def statistical_roi(req: StatisticalRoiRequest) -> dict:
    """Compute every provided analysis block; at least one block is required."""
    blocks = {
        "abTest": (req.ab_test, analyze_ab),
        "did": (req.did, analyze_did),
        "judgeAgreement": (req.judge_agreement, analyze_judge),
        "hallucination": (req.hallucination, analyze_hallucination),
        "drift": (req.drift, analyze_drift),
        "economics": (req.economics, analyze_economics),
    }
    provided = {name: (inp, fn) for name, (inp, fn) in blocks.items() if inp is not None}
    if not provided:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one analysis block: "
                   + ", ".join(blocks.keys()))

    results: dict = {}
    for name, (inp, fn) in provided.items():
        try:
            results[name] = fn(inp)  # type: ignore[arg-type]
        except ValueError as exc:
            raise HTTPException(status_code=422,
                                detail=f"{name}: {exc}") from exc
    return results
