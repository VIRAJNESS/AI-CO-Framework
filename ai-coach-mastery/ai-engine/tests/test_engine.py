"""Tests for the /api/v1/engine stage routers — happy, negative and edge cases."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.engine.stage5_stats import cohens_kappa, population_stability_index
from app.main import app

client = TestClient(app)

BASE = "/api/v1/engine"


@pytest.fixture(autouse=True)
def mock_mode(monkeypatch, tmp_path):
    """Force deterministic mock providers for every engine test."""
    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("STORAGE_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    yield
    get_settings.cache_clear()


# =========================== Stage 1 — pitch simulator ===========================


def _pitch_payload(**overrides):
    payload = {
        "industry": "FinTech",
        "domainTrack": "SDLC",
        "engineeringHeadcount": 100,
        "monthlyTicketVolume": 5000,
        "currentCloudSpend": 50000,
    }
    payload.update(overrides)
    return payload


def test_stage1_happy_path_structure_and_pillars():
    res = client.post(f"{BASE}/stage1/pitch-simulator", json=_pitch_payload())
    assert res.status_code == 200
    body = res.json()
    assert body["horizonMonths"] == 12
    assert set(body["fourPillars"].keys()) == {"vision", "trust", "depth", "solving"}
    assert body["traditionalCopilots"]["taskLiftRange"]["low"] == 0.12
    assert body["agenticWorkflows"]["toilReductionRange"]["high"] == 0.65
    # Agentic mid-case should beat copilots mid-case at this scale.
    assert body["agenticAdvantageMidCase"] > 0


def test_stage1_deterministic():
    a = client.post(f"{BASE}/stage1/pitch-simulator", json=_pitch_payload()).json()
    b = client.post(f"{BASE}/stage1/pitch-simulator", json=_pitch_payload()).json()
    assert a == b


def test_stage1_rejects_zero_headcount():
    res = client.post(f"{BASE}/stage1/pitch-simulator",
                      json=_pitch_payload(engineeringHeadcount=0))
    assert res.status_code == 422


def test_stage1_edge_zero_tickets_and_zero_cloud():
    # Edge: no tickets & no cloud spend — deflection contributes nothing,
    # platform cost is zero, model must still be coherent.
    res = client.post(f"{BASE}/stage1/pitch-simulator",
                      json=_pitch_payload(monthlyTicketVolume=0, currentCloudSpend=0))
    assert res.status_code == 200
    body = res.json()
    assert body["baseline"]["annualTicketHandlingCost"] == 0
    assert body["agenticWorkflows"]["annualPlatformCost"] == 0


def test_stage1_edge_unknown_track_rejected():
    res = client.post(f"{BASE}/stage1/pitch-simulator",
                      json=_pitch_payload(domainTrack="MAINFRAME"))
    assert res.status_code == 422


# =========================== Stage 2 — diagnostic audit ===========================


_ALL_PILLARS = {
    "STRATEGY_KPI_ALIGNMENT": 4,
    "DATA_ONTOLOGY_READINESS": 3,
    "CLOUD_AGENT_ARCHITECTURE": 2,
    "RESPONSIBLE_AI_GUARDRAILS": 5,
    "TALENT_PDLC_CULTURE": 3,
}


def test_stage2_happy_path_maturity_and_roadmap():
    res = client.post(f"{BASE}/stage2/diagnostic-audit", json={
        "domainTrack": "LEGACY",
        "pillarScores": _ALL_PILLARS,
        "trackProbes": [{"name": "Parity harness coverage", "score": 2}],
    })
    assert res.status_code == 200
    body = res.json()
    assert 0 <= body["maturityIndex"] <= 100
    assert body["criticalRedFlags"] == ["CLOUD_AGENT_ARCHITECTURE"]
    assert body["trackProbeRedFlags"] == ["Parity harness coverage"]
    assert body["remediationRoadmap"][0]["pillar"] == "CLOUD_AGENT_ARCHITECTURE"
    assert len(body["remediationRoadmap"]) == 5


def test_stage2_missing_pillar_rejected():
    incomplete = dict(_ALL_PILLARS)
    incomplete.pop("TALENT_PDLC_CULTURE")
    res = client.post(f"{BASE}/stage2/diagnostic-audit", json={
        "domainTrack": "SDLC", "pillarScores": incomplete,
    })
    assert res.status_code == 422


def test_stage2_edge_all_ones_is_zero_maturity():
    # Edge: minimum scores across the board => index 0, band AD_HOC.
    res = client.post(f"{BASE}/stage2/diagnostic-audit", json={
        "domainTrack": "STARTUP",
        "pillarScores": {k: 1 for k in _ALL_PILLARS},
    })
    body = res.json()
    assert body["maturityIndex"] == 0.0
    assert body["maturityBand"] == "AD_HOC"
    assert len(body["criticalRedFlags"]) == 5


def test_stage2_edge_all_fives_is_full_maturity():
    # Edge: maximum scores => index 100, TRANSFORMATIVE, no red flags.
    res = client.post(f"{BASE}/stage2/diagnostic-audit", json={
        "domainTrack": "PDLC",
        "pillarScores": {k: 5 for k in _ALL_PILLARS},
    })
    body = res.json()
    assert body["maturityIndex"] == 100.0
    assert body["maturityBand"] == "TRANSFORMATIVE"
    assert body["criticalRedFlags"] == []


def test_stage2_edge_out_of_range_score_rejected():
    res = client.post(f"{BASE}/stage2/diagnostic-audit", json={
        "domainTrack": "SDLC",
        "pillarScores": {**_ALL_PILLARS, "STRATEGY_KPI_ALIGNMENT": 9},
    })
    assert res.status_code == 422


# =========================== Stage 3 — domain blueprint ===========================


@pytest.mark.parametrize("track,expected_component", [
    ("SDLC", "Claude/LLM SDK Workbench"),
    ("PDLC", "Customer Telemetry & Rage-Click Synthesis"),
    ("STARTUP", "Lean Agentic Pod Topology"),
    ("LEGACY", "Automated Codebase Archaeology"),
])
def test_stage3_blueprints_per_track(track, expected_component):
    res = client.post(f"{BASE}/stage3/domain-blueprint",
                      json={"domainTrack": track, "clientName": "Acme"})
    assert res.status_code == 200
    body = res.json()
    names = [c["name"] for c in body["components"]]
    assert expected_component in names
    assert len(body["components"]) == 3
    assert len(body["governanceGates"]) == 5


def test_stage3_edge_client_name_optional():
    res = client.post(f"{BASE}/stage3/domain-blueprint", json={"domainTrack": "SDLC"})
    assert res.status_code == 200
    assert res.json()["clientName"] is None


def test_stage3_invalid_track_rejected():
    res = client.post(f"{BASE}/stage3/domain-blueprint", json={"domainTrack": "COBOL"})
    assert res.status_code == 422


# =========================== Stage 4 — live demo ===========================


def test_stage4_bug_log_full_trace():
    bug = ("FATAL Exception in thread main java.lang.NullPointerException\n"
           "    at com.acme.PaymentService.charge(PaymentService.java:42)\n"
           "Request failed with error 500, timeout after retry")
    res = client.post(f"{BASE}/stage4/live-demo", json={"inputText": bug})
    assert res.status_code == 200
    body = res.json()
    assert body["llmProvider"] == "mock"
    assert [s["step"] for s in body["trace"]] == [1, 2, 3, 4]
    assert body["trace"][0]["detectedIntent"] == "BUG_LOG"
    assert body["trace"][2]["mode"] == "mock-deterministic"
    assert body["finalVerdict"] in {"APPROVE", "HUMAN_REVIEW"}


def test_stage4_pii_is_redacted():
    text = ("Customer john.doe@example.com is frustrated and wants a refund. "
            "SSN 123-45-6789 on file.")
    res = client.post(f"{BASE}/stage4/live-demo", json={"inputText": text})
    body = res.json()
    guard = body["trace"][1]
    assert guard["status"] == "PASS_WITH_REDACTIONS"
    assert "EMAIL" in guard["findings"]
    assert "SSN_LIKE" in guard["findings"]
    # Redacted text must never reach the worker output verbatim.
    assert "john.doe@example.com" not in body["trace"][2]["output"]


def test_stage4_deterministic_for_same_input():
    payload = {"inputText": "As a user I want a dashboard. Acceptance criteria: KPI visible."}
    a = client.post(f"{BASE}/stage4/live-demo", json=payload).json()
    b = client.post(f"{BASE}/stage4/live-demo", json=payload).json()
    assert a == b


def test_stage4_hint_overrides_classification():
    # Edge: ambiguous text + explicit hint must obey the hint.
    res = client.post(f"{BASE}/stage4/live-demo",
                      json={"inputText": "hello world", "hint": "legacy"})
    assert res.json()["trace"][0]["detectedIntent"] == "LEGACY_CODE"


def test_stage4_edge_blank_input_rejected():
    res = client.post(f"{BASE}/stage4/live-demo", json={"inputText": "   "})
    assert res.status_code == 422


def test_stage4_edge_no_signals_defaults_to_prd():
    # Edge: neutral prose with no intent signals falls back to PRODUCT_PRD.
    res = client.post(f"{BASE}/stage4/live-demo",
                      json={"inputText": "lorem ipsum dolor sit amet"})
    assert res.json()["trace"][0]["detectedIntent"] == "PRODUCT_PRD"


# =========================== Stage 5 — statistical ROI ===========================


def test_stage5_ab_test_significant_uplift():
    res = client.post(f"{BASE}/stage5/statistical-roi", json={
        "abTest": {"control": [10, 11, 9, 10, 10.5, 9.5],
                   "treatment": [15, 16, 14.5, 15.5, 16.2, 15.8]},
    })
    assert res.status_code == 200
    ab = res.json()["abTest"]
    assert ab["significantAt005"] is True
    assert ab["ci95"]["low"] < ab["meanDifference"] < ab["ci95"]["high"]
    assert ab["welchT"]["pValue"] < 0.05
    assert ab["mannWhitney"]["pValue"] < 0.05


def test_stage5_did_positive_lift():
    res = client.post(f"{BASE}/stage5/statistical-roi", json={
        "did": {"treatmentPre": [100, 102], "treatmentPost": [130, 132],
                "controlPre": [100, 101], "controlPost": [105, 106]},
    })
    did = res.json()["did"]
    assert did["didLift"] == pytest.approx(25.0)
    assert "Positive causal lift" in did["interpretation"]


def test_stage5_judge_kappa_perfect_agreement():
    res = client.post(f"{BASE}/stage5/statistical-roi", json={
        "judgeAgreement": {"llmLabels": ["pass", "fail", "pass", "pass"],
                           "humanLabels": ["pass", "fail", "pass", "pass"]},
    })
    judge = res.json()["judgeAgreement"]
    assert judge["cohensKappa"] == 1.0
    assert judge["agreementBand"] == "ALMOST_PERFECT"


def test_stage5_hallucination_and_economics():
    res = client.post(f"{BASE}/stage5/statistical-roi", json={
        "hallucination": {"totalClaims": 200, "contradictedClaims": 6},
        "economics": {"annualGrossSavings": 1_000_000, "annualInferenceCost": 120_000,
                      "annualOrchestrationCost": 80_000, "annualGovernanceCost": 50_000,
                      "oneTimeImplementation": 250_000},
    })
    body = res.json()
    assert body["hallucination"]["hallucinationRate"] == 0.03
    assert body["hallucination"]["withinProductionThreshold"] is True
    econ = body["economics"]
    assert econ["netEconomicValue"] == 750_000
    assert econ["cfoVerdict"] == "VALUE_POSITIVE"
    assert econ["paybackMonths"] == 4.0


def test_stage5_drift_detects_shift():
    baseline = [float(i % 10) for i in range(100)]
    shifted = [float(i % 10) + 5 for i in range(100)]
    res = client.post(f"{BASE}/stage5/statistical-roi", json={
        "drift": {"baseline": baseline, "current": shifted},
    })
    drift = res.json()["drift"]
    assert drift["alertLevel"] == "SEVERE_DRIFT"
    assert drift["actionRequired"] is True


def test_stage5_negative_empty_request_rejected():
    res = client.post(f"{BASE}/stage5/statistical-roi", json={})
    assert res.status_code == 422


def test_stage5_edge_identical_ab_samples():
    # Edge: zero variance both arms — degenerate CI, not significant, no crash.
    res = client.post(f"{BASE}/stage5/statistical-roi", json={
        "abTest": {"control": [5, 5, 5], "treatment": [5, 5, 5]},
    })
    ab = res.json()["abTest"]
    assert ab["meanDifference"] == 0.0
    assert ab["significantAt005"] is False
    assert ab["ci95"]["low"] == ab["ci95"]["high"] == 0.0


def test_stage5_edge_hallucination_overflow_rejected():
    # Edge: contradicted > total must 422, not produce rate > 1.
    res = client.post(f"{BASE}/stage5/statistical-roi", json={
        "hallucination": {"totalClaims": 10, "contradictedClaims": 11},
    })
    assert res.status_code == 422


def test_stage5_edge_kappa_mismatched_lengths():
    res = client.post(f"{BASE}/stage5/statistical-roi", json={
        "judgeAgreement": {"llmLabels": ["a", "b", "a"], "humanLabels": ["a", "b"]},
    })
    assert res.status_code == 422


def test_kappa_and_psi_pure_functions():
    # Pure-function sanity: zero agreement beyond chance => kappa <= 0.
    assert cohens_kappa(["a", "b"], ["b", "a"]) <= 0
    # PSI of identical distributions ~ 0.
    same = [float(i) for i in range(50)]
    assert population_stability_index(same, same) == pytest.approx(0.0, abs=1e-9)


# =========================== Stage 6 — roadmap mentor ===========================


def test_stage6_full_plan_all_roles():
    res = client.post(f"{BASE}/stage6/roadmap-mentor", json={"domainTrack": "SDLC"})
    assert res.status_code == 200
    body = res.json()
    assert [p["window"] for p in body["plan"]] == ["Days 1-30", "Days 31-60", "Days 61-90"]
    assert len(body["mentoringCurriculum"]) == 4  # all roles by default
    phases = [p["phase"] for p in body["mentoringCurriculum"][0]["phases"]]
    assert phases == ["SEE_ONE", "CO_BUILD_ONE", "LEAD_ONE"]
    assert all(p["kpis"] for role in body["mentoringCurriculum"] for p in role["phases"])


def test_stage6_low_maturity_adds_remediation_action():
    res = client.post(f"{BASE}/stage6/roadmap-mentor",
                      json={"domainTrack": "LEGACY", "maturityIndex": 30})
    body = res.json()
    assert body["maturityAdjusted"] is True
    assert any("red-flag" in a for a in body["plan"][0]["actions"])


def test_stage6_edge_single_role_track():
    res = client.post(f"{BASE}/stage6/roadmap-mentor",
                      json={"domainTrack": "STARTUP", "roleTracks": ["ENGINEER"]})
    body = res.json()
    assert len(body["mentoringCurriculum"]) == 1
    assert body["mentoringCurriculum"][0]["roleTrack"] == "ENGINEER"


def test_stage6_edge_invalid_maturity_rejected():
    res = client.post(f"{BASE}/stage6/roadmap-mentor",
                      json={"domainTrack": "SDLC", "maturityIndex": 101})
    assert res.status_code == 422


def test_stage6_edge_high_maturity_not_adjusted():
    # Edge: boundary — exactly 50 must NOT trigger low-maturity remediation.
    res = client.post(f"{BASE}/stage6/roadmap-mentor",
                      json={"domainTrack": "PDLC", "maturityIndex": 50})
    assert res.json()["maturityAdjusted"] is False
