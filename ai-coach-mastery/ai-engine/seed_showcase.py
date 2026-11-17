"""Showcase artifact seeder — generates real boardroom deliverables.

Renders genuine PPTX + DOCX files (via the doc_factory) for every completed
stage of the 4 showcase engagements and stores them at the deterministic keys
referenced by core-api's DataSeeder:

    showcase/{slug}/stage{n}.pptx / .docx

Stage results are computed with the engine's real pure functions (pitch
economics, maturity audit, blueprints, live demo trace, statistical suite,
roadmap) using inputs tuned to each client's scenario — so every number in a
downloaded deck matches the seeded database narrative.

Usage (inside the ai-engine container or a venv with requirements installed):
    python seed_showcase.py

Idempotent: re-running overwrites the same keys. Cloud-agnostic: artifacts go
through the storage port (local /data/artifacts by default; S3/Blob/GCS via
STORAGE_PROVIDER).
"""

from __future__ import annotations

from app.core.config import get_settings
from app.doc_factory.docx_builder import generate_stage_docx
from app.doc_factory.pptx_builder import generate_stage_pptx
from app.engine.stage1_pitch import DomainTrack, PitchRequest, compute_pitch
from app.engine.stage2_audit import AuditRequest, Pillar, TrackProbe, compute_audit
from app.engine.stage3_blueprint import BlueprintRequest, build_blueprint
from app.engine.stage4_livedemo import _evaluate, _guardrail_check, _route_intent, _worker_execute
from app.engine.stage5_stats import (
    AbTestInput,
    DidInput,
    EconomicsInput,
    HallucinationInput,
    JudgeAgreementInput,
    analyze_ab,
    analyze_did,
    analyze_economics,
    analyze_hallucination,
    analyze_judge,
)
from app.engine.stage6_roadmap import RoadmapRequest, RoleTrack, build_roadmap
from app.providers.storage import get_storage_provider

_CONTENT_TYPES = {
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _pillar_scores(strategy: int, data: int, arch: int, rai: int, talent: int) -> dict:
    return {
        Pillar.STRATEGY_KPI: strategy,
        Pillar.DATA_ONTOLOGY: data,
        Pillar.CLOUD_AGENT_ARCH: arch,
        Pillar.RESPONSIBLE_AI: rai,
        Pillar.TALENT_CULTURE: talent,
    }


def _live_demo(text: str, hint: str | None = None) -> dict:
    """Run the real 4-step trace helpers (deterministic in mock mode)."""
    settings = get_settings()
    step1 = _route_intent(text, hint)
    step2, sanitized = _guardrail_check(text)
    step3 = _worker_execute(step1["detectedIntent"], sanitized, settings)
    step4 = _evaluate(sanitized, step3["output"])
    return {"llmProvider": settings.llm_provider.value,
            "trace": [step1, step2, step3, step4],
            "finalVerdict": step4["verdict"]}


# --- Showcase stage-result builders (one per client) -----------------------------


def novatel_results() -> dict[int, dict]:
    """NovaTel: SDLC, stage 6 mature — statistical proof p<0.001, Kappa 0.86."""
    pitch = compute_pitch(PitchRequest(
        industry="Telecommunications", domain_track=DomainTrack.SDLC,
        engineering_headcount=450, monthly_ticket_volume=180_000,
        current_cloud_spend=820_000))
    audit = compute_audit(AuditRequest(
        domain_track=DomainTrack.SDLC,
        pillar_scores=_pillar_scores(4, 3, 4, 4, 3),
        track_probes=[TrackProbe(name="CI/CD telemetry coverage", score=4)]))
    blueprint = build_blueprint(BlueprintRequest(
        domain_track=DomainTrack.SDLC, client_name="NovaTel Global Telecom"))
    demo = _live_demo(
        "FATAL Exception in NetworkOrchestrator: timeout after retry, error 500 "
        "in BSS provisioning pipeline; stack trace attached.", hint="bug")

    # Triage-toil hours per 100 tickets: before ~ 42h, after ~ 13.4h (−68%);
    # strongly separated samples drive p < 0.001.
    stats = {
        "abTest": analyze_ab(AbTestInput(
            control=[41.8, 42.5, 41.2, 43.0, 42.2, 41.9, 42.7, 42.1],
            treatment=[13.5, 13.2, 13.8, 13.1, 13.6, 13.3, 13.7, 13.4])),
        "did": analyze_did(DidInput(
            treatment_pre=[100, 102, 101], treatment_post=[32, 33, 31],
            control_pre=[100, 101, 99], control_post=[97, 96, 98])),
        # 100 labels, 7 asymmetric disagreements with a uniform LLM marginal
        # => observed 0.93, expected 0.50, kappa = exactly 0.86.
        "judgeAgreement": analyze_judge(JudgeAgreementInput(
            llm_labels=(["resolve"] * 50 + ["escalate"] * 50),
            human_labels=(["resolve"] * 46 + ["escalate"] * 4
                          + ["resolve"] * 3 + ["escalate"] * 47))),
        "hallucination": analyze_hallucination(HallucinationInput(
            total_claims=500, contradicted_claims=9)),
        "economics": analyze_economics(EconomicsInput(
            annual_gross_savings=14_900_000, annual_inference_cost=2_100_000,
            annual_orchestration_cost=950_000, annual_governance_cost=650_000,
            one_time_implementation=1_800_000)),
    }
    roadmap = build_roadmap(RoadmapRequest(
        domain_track=DomainTrack.SDLC, role_tracks=list(RoleTrack),
        maturity_index=audit["maturityIndex"]))
    roadmap["scaleDecision"] = "APPROVED"
    roadmap["headline"] = ("31% autonomous ticket deflection, 68% triage toil "
                           "reduction, 85% faster deployment cycles")
    return {1: pitch, 2: audit, 3: blueprint, 4: demo, 5: stats, 6: roadmap}


def finpulse_results() -> dict[int, dict]:
    """FinPulse: PDLC, stage 4 active PoC — drop-off 46% → 18%."""
    pitch = compute_pitch(PitchRequest(
        industry="Digital Banking", domain_track=DomainTrack.PDLC,
        engineering_headcount=120, monthly_ticket_volume=42_000,
        current_cloud_spend=210_000))
    audit = compute_audit(AuditRequest(
        domain_track=DomainTrack.PDLC,
        pillar_scores=_pillar_scores(3, 3, 2, 4, 3),
        track_probes=[TrackProbe(name="experiment velocity", score=3)]))
    audit["maturityScoreOutOf5"] = 3.1  # scenario headline framing
    blueprint = build_blueprint(BlueprintRequest(
        domain_track=DomainTrack.PDLC, client_name="FinPulse Digital Banking"))
    demo = _live_demo(
        "Customer complaint: checkout keeps failing on card entry, I am "
        "frustrated and about to cancel; rage clicks on the pay button, "
        "support was no help. 46% of mobile users drop at this step.",
        hint="complaint")
    demo["frictionOutcome"] = {"dropoffBeforePct": 46, "dropoffAfterPct": 18}
    return {1: pitch, 2: audit, 3: blueprint, 4: demo}


def veloceai_results() -> dict[int, dict]:
    """VeloceAI: STARTUP, stage 3 blueprinting — −54% inference unit cost."""
    pitch = compute_pitch(PitchRequest(
        industry="B2B SaaS", domain_track=DomainTrack.STARTUP,
        engineering_headcount=35, monthly_ticket_volume=2_500,
        current_cloud_spend=48_000))
    audit = compute_audit(AuditRequest(
        domain_track=DomainTrack.STARTUP,
        pillar_scores=_pillar_scores(2, 3, 3, 3, 3),
        track_probes=[TrackProbe(name="token budget instrumentation", score=1)]))
    blueprint = build_blueprint(BlueprintRequest(
        domain_track=DomainTrack.STARTUP, client_name="VeloceAI Series-B SaaS"))
    blueprint["inferenceUnitCostReductionTargetPct"] = 54
    blueprint["currentMonthlyTokenSpendUsd"] = 48_000
    return {1: pitch, 2: audit, 3: blueprint}


def omnicare_results() -> dict[int, dict]:
    """OmniCare: LEGACY, stage 2 discovery — Data/Ontology 2/5 red flag."""
    pitch = compute_pitch(PitchRequest(
        industry="Insurance", domain_track=DomainTrack.LEGACY,
        engineering_headcount=210, monthly_ticket_volume=55_000,
        current_cloud_spend=160_000))
    pitch["pitchOutcome"] = "SIGNED"
    audit = compute_audit(AuditRequest(
        domain_track=DomainTrack.LEGACY,
        pillar_scores=_pillar_scores(3, 2, 2, 3, 2),
        track_probes=[TrackProbe(name="codebase inventory completeness", score=2),
                      TrackProbe(name="parity test harness", score=1)]))
    audit["recommendation"] = ("Strangler-Fig API wrappers + Semantic Parity "
                               "Harness before any rewrite")
    return {1: pitch, 2: audit}


SHOWCASE = [
    ("novatel", {"clientName": "NovaTel Global Telecom",
                 "industry": "Telecommunications", "domainTrack": "SDLC"},
     novatel_results),
    ("finpulse", {"clientName": "FinPulse Digital Banking",
                  "industry": "Financial Services", "domainTrack": "PDLC"},
     finpulse_results),
    ("veloceai", {"clientName": "VeloceAI Series-B SaaS",
                  "industry": "B2B SaaS", "domainTrack": "STARTUP"},
     veloceai_results),
    ("omnicare", {"clientName": "OmniCare Core Insurance",
                  "industry": "Insurance", "domainTrack": "LEGACY"},
     omnicare_results),
]


def seed_artifacts() -> list[str]:
    """Render and store every showcase deliverable; returns stored keys."""
    settings = get_settings()
    storage = get_storage_provider(settings)
    stored: list[str] = []

    for slug, engagement, results_fn in SHOWCASE:
        results = results_fn()
        for stage_num, stage_result in results.items():
            for fmt, generator in (("pptx", generate_stage_pptx),
                                   ("docx", generate_stage_docx)):
                data = generator(stage_num, engagement, stage_result)
                key = f"showcase/{slug}/stage{stage_num}.{fmt}"
                storage.put(key, data, _CONTENT_TYPES[fmt])
                stored.append(key)
        print(f"  seeded {engagement['clientName']}: stages "
              f"{sorted(results)} ({2 * len(results)} files)")
    return stored


if __name__ == "__main__":
    print("Seeding showcase deliverables via doc_factory + storage port...")
    keys = seed_artifacts()
    print(f"Done — {len(keys)} artifacts stored "
          f"(provider: {get_settings().storage_provider.value}).")
