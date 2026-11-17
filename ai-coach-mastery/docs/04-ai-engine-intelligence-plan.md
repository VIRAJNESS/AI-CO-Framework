# AI Engine — Intelligence & Live-Demo Capabilities (Step 3 Plan)

## Goal

Implement all quantitative, diagnostic and live proof-of-demo capabilities of
the AI Head Coach framework as modular FastAPI routers under
`/api/v1/engine/stage{1..6}/...`, working out-of-the-box in `mock` mode
(deterministic, domain-aware) and transparently upgradable to live LLM keys.

## Options considered

### Option A — One router module per stage under `app/engine/` (chosen)
Six self-contained modules (`stage1_pitch.py` … `stage6_roadmap.py`), each
exposing an `APIRouter` + Pydantic v2 schemas + pure computation functions;
`main.py` includes them under the `/api/v1/engine` prefix.

- **Pros:** Pure functions are unit-testable without HTTP; stage boundaries
  match the coaching lifecycle & the core-api orchestration; schemas live next
  to their only consumer; zero cross-stage coupling.
- **Cons (devil's advocate):** Some shared math (CI helpers) could be
  duplicated — mitigated with a tiny `stats_utils` only if duplication
  actually appears (it doesn't at current scope).

### Option B — Single `engine.py` mega-router
- **Pros:** One import, one file.
- **Cons (devil's advocate):** ~1500-line file; merge conflicts; impossible to
  navigate; violates the repo's package-by-feature convention. Rejected.

### Option C — Class-based services + thin routers (DDD-style)
- **Pros:** Mirrors core-api layering.
- **Cons (devil's advocate):** These endpoints are stateless pure
  computations — a service class adds indirection with zero behavioural gain.
  FastAPI idiom favours module-level functions. Rejected.

**Recommendation: Option A.**

## Capability map

| Router | Endpoint | Core math / logic |
|--------|----------|-------------------|
| stage1 | `POST /stage1/pitch-simulator` | 12-month copilot (12–18% task lift, shelfware drag) vs agentic (30–65% toil reduction, deflection, velocity) ROI model from headcount/tickets/cloud-spend; 4-Pillar messaging (Vision/Trust/Depth/Solving) |
| stage2 | `POST /stage2/diagnostic-audit` | Weighted Maturity Index (0–100) over 5 pillars + track probes; red-flag blockers (score ≤ 2); prioritized remediation roadmap |
| stage3 | `POST /stage3/domain-blueprint` | Tailored execution architecture JSON per track (SDLC / PDLC / STARTUP / LEGACY component sets) |
| stage4 | `POST /stage4/live-demo` | 4-step visible trace: Intent & Ontology Router → Guardrail & PII Check (regex redaction) → Worker Agent (LLMProvider port: mock deterministic or live) → Evaluator Confidence & Shadow Diff |
| stage5 | `POST /stage5/statistical-roi` | Welch t-test + Mann-Whitney + 95% CI (scipy), Difference-in-Differences lift, Cohen's Kappa, hallucination/NLI rate, PSI drift, CFO Net Economic Value & TCO |
| stage6 | `POST /stage6/roadmap-mentor` | 30-60-90 day plan + See One / Co-Build One / Lead One curriculum per role track with target KPIs |

## Key decisions

1. **Determinism in mock mode:** stage 4 derives all synth values from
   SHA-256 of the input text (same pattern as `MockLLMProvider`) so demos are
   reproducible; live mode is selected purely by `LLM_PROVIDER` env (ports &
   adapters already in place).
2. **Optional analysis blocks in stage 5:** each statistical section (A/B,
   DiD, judge agreement, drift, economics) is independently optional; the
   endpoint computes what it is given and never fails on absent blocks.
3. **PII guardrail:** regex-based detection/redaction (emails, phones, SSN-like,
   API-key-like) — no external calls, cloud-agnostic.
4. **No new dependencies:** scipy/numpy/statsmodels already pinned in Step 1.
5. **Existing `/api/v1/coach|analysis|reports` endpoints stay untouched**
   (core-api Step 2 depends on them).

## Out of scope

Real LLM adapter implementations (stubs remain), persistence of demo runs,
auth, streaming traces (single JSON response contains the full 4-step trace).
