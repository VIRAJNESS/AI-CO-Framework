# Task Breakdown — AI Engine Intelligence Routers (Step 3)

Implementing the approved plan (Option A: one router module per stage).

## T1 — Scaffolding
- [x] `app/engine/` package created; routers wired in `main.py` under `/api/v1/engine`

## T2 — Stage routers
- [x] `stage1_pitch.py` — `/stage1/pitch-simulator`: 12-month Copilots
      (12–18% lift, 35% shelfware) vs Agentic (30–65% toil, 25–45% deflection,
      20–40% velocity) economics + 4-pillar messaging; assumptions in payload
- [x] `stage2_audit.py` — `/stage2/diagnostic-audit`: weighted 5-pillar
      Maturity Index (0–100), bands, red-flag blockers (≤2), track probes,
      prioritized remediation roadmap
- [x] `stage3_blueprint.py` — `/stage3/domain-blueprint`: SDLC/PDLC/STARTUP/
      LEGACY execution architectures (3 components each: agents, integrations,
      KPIs) + shared foundations & governance gates
- [x] `stage4_livedemo.py` — `/stage4/live-demo`: 4-step trace
      (Intent & Ontology Router → Guardrail & PII Check with regex redaction →
      Worker Agent mock/live via LLMProvider port → Evaluator Confidence &
      Shadow Diff); deterministic in mock mode (SHA-256-seeded)
- [x] `stage5_stats.py` — `/stage5/statistical-roi`: Welch t + Mann-Whitney +
      Welch-Satterthwaite 95% CI, DiD lift, Cohen's Kappa, hallucination rate
      with Wilson CI, PSI drift (quantile buckets + Laplace smoothing),
      CFO NEV/TCO/payback; all blocks optional
- [x] `stage6_roadmap.py` — `/stage6/roadmap-mentor`: 30-60-90 plan (maturity-
      adjusted) + See One / Co-Build One / Lead One curriculum per role with KPIs

## T3 — Tests
- [x] `tests/test_engine.py`: 39 tests covering happy, negative and ≥3 edge
      cases per stage (zero-variance A/B, boundary maturity, PII redaction,
      determinism, hint override, empty stats request, kappa mismatch, etc.)

## T4 — Verification & wrap-up
- [x] Full suite green: 56 passed (17 pre-existing + 39 new), verified
      2026-11-17 on Python 3.14 venv (Docker daemon unavailable)
- [x] AGENTS.md, docs and memory graph updated
