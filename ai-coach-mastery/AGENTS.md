# AGENTS.md — AI Coach Mastery

Guidance for AI agents working in this repository.

## What this repo is

Cloud-agnostic monorepo (Step 1 complete): Angular 18 frontend, Spring Boot
3.3 core-api, FastAPI ai-engine, orchestrated locally via
`infra/local/docker-compose.yml`. Skeleton Terraform modules + a
provider-neutral Helm chart live under `infra/cloud/`.

## Non-negotiable conventions

1. **12-factor everywhere.** Behavior switches only via env vars:
   `STORAGE_PROVIDER` (local|s3|azure_blob|gcs), `LLM_PROVIDER`
   (mock|openai|anthropic|azure_openai|bedrock|vertex), `DB_URL`, `REDIS_URL`.
   Never hardcode cloud specifics in application code.
2. **Ports & adapters.** New LLM/storage backends implement the ABCs in
   `ai-engine/app/providers/` and are wired in the factory functions only.
3. **Local-first.** `make up` must always work with zero cloud keys
   (mock LLM + local storage defaults). Never break this.
4. **Schema ownership.** Flyway owns Postgres schema `core`
   (core-api/src/main/resources/db/migration); the ai-engine owns schema `ai`.
   The local init script (`infra/local/postgres/init/01-init.sql`) creates
   both schemas + pgvector.
5. **No secrets in the repo.** `.env` is gitignored; `.env.example` documents
   variables; Helm references an `existingSecret`.
6. **Tests accompany all new work** (happy, negative, ≥3 edge cases):
   - core-api: JUnit 5 + Mockito + MockMvc (H2 in PG mode for test profile)
   - ai-engine: pytest + FastAPI TestClient (`ai-engine/tests/`)
   - frontend: Jasmine/Karma specs next to sources

## Key entry points

| Concern            | Location                                              |
|--------------------|-------------------------------------------------------|
| Orchestration      | `Makefile` (up/down/seed/test/build-all)              |
| Compose stack      | `infra/local/docker-compose.yml`                      |
| Core API health    | `GET :8080/actuator/health`                           |
| AI engine health   | `GET :8000/health` (reports active providers)         |
| Mock LLM           | `ai-engine/app/providers/llm.py` (deterministic)      |
| Storage port       | `ai-engine/app/providers/storage.py`                  |
| Helm chart         | `infra/cloud/helm/ai-coach-mastery`                   |
| Terraform contracts| `infra/cloud/terraform/modules/{azure,aws,gcp}`       |

## Core API domain (Step 2)

- **6-stage lifecycle** (`Stage` enum, 1..6): Discovery & Audit → Diagnostic &
  Baseline → Pilot Design → Execution & Coaching → Measurement & ROI →
  Scale & Handoff. Forward transitions advance exactly one stage; backward
  moves (rework) allowed; enforced in `EngagementService.transitionStage`.
- **Aggregates** (package-by-feature): `engagement.ClientEngagement`,
  `artifact.StageArtifact`, `governance.GovernanceGate` (unique per
  engagement+gate, upsert semantics), `mentoring.MentoringProgress` (unique
  per engagement+role+module+phase, upsert).
- **Stage execution** (`orchestration.StageExecutionService`):
  `POST /api/v1/engagements/{id}/stages/{n}/execute` → validates n == current
  stage, governance gates (FAIL ⇒ 409, WARN ⇒ surfaced), calls ai-engine
  (`AiEngineClient` via RestClient: /api/v1/coach/insights + /api/v1/reports
  pptx & docx), persists `StageArtifact`, auto-advances (capped at 6).
  Upstream failure ⇒ 502, zero state mutation (upstream calls precede saves).
- **Error model:** RFC-7807 via `GlobalExceptionHandler` — 404 not-found,
  409 `BusinessRuleException`, 502 `UpstreamServiceException`, 400 validation.
- **OpenAPI:** springdoc; Swagger UI at `/swagger-ui.html`.
- **Flyway baseline is `V1__init_schema.sql`** (replaced bootstrap V1;
  `coaches` kept, demo `engagements` superseded by `client_engagements`).
- Mappers are manual `@Component` classes (MapStruct deliberately avoided —
  see `docs/02-core-api-lifecycle-plan.md` Option analysis).

## AI Engine intelligence routers (Step 3)

- Package `ai-engine/app/engine/` — one router module per lifecycle stage,
  mounted in `main.py` under `/api/v1/engine`:
  `stage1/pitch-simulator`, `stage2/diagnostic-audit`, `stage3/domain-blueprint`,
  `stage4/live-demo`, `stage5/statistical-roi`, `stage6/roadmap-mentor`.
- Pure computation functions beside thin routers; Pydantic v2 schemas with
  camelCase aliases (`populate_by_name=True`).
- Stage 4 trace: Intent Router → PII guardrail (regex redaction) → Worker
  agent (mock deterministic SHA-256-seeded, or live via LLMProvider port) →
  Evaluator confidence + shadow diff. Non-mock providers return 501 until
  adapters are implemented.
- Stage 5 blocks are all optional (`abTest`, `did`, `judgeAgreement`,
  `hallucination`, `drift`, `economics`); at least one required, else 422.
- No new Python dependencies were added for Step 3.

## Document Generation Factory (Step 4)

- Package `ai-engine/app/doc_factory/`: `theme.py` (corporate palette: Deep
  Navy #0F172A, Electric Sky #0284C7, Slate #334155, Emerald #059669),
  `charts.py` (matplotlib Agg, 200 DPI, placeholder fallback), `content.py`
  (per-stage StageContent registry), `pptx_builder.py` (7-slide deck),
  `docx_builder.py` (consulting doc with sign-off checklist), `router.py`.
- `POST /api/v1/engine/documents/render` {stageNum 1..6, format pptx|docx,
  engagementData, stageResult} → persists via the storage port and streams
  the file (Content-Disposition attachment + X-Artifact-Key header).
- Filename slugs must stay ASCII (HTTP headers are latin-1) — see
  `router._slug`. Charts must never raise; they fall back to a placeholder.
- `services/reports.py` (simple generic renderer used by core-api Step 2)
  deliberately remains separate from doc_factory.

## Showcase seeding (Step 5)

- **Two-part seeder with split ownership:**
  - `core-api config.DataSeeder` (CommandLineRunner) auto-seeds 4 engagements
    + 15 stage artifacts + 16 governance gates + mentoring rows on first
    startup when `client_engagements` is empty. Toggle:
    `APP_SEED_DEMO_DATA` / `app.seed-demo-data` (default true; false in the
    test profile). Fixed UUIDs (NovaTel/FinPulse/VeloceAI/OmniCare).
  - `ai-engine/seed_showcase.py` generates the 30 matching PPTX/DOCX binaries
    through doc_factory + storage port at the deterministic keys
    `showcase/{slug}/stage{n}.{pptx|docx}`. Run by `make seed`.
- **Showcase roster:** NovaTel (SDLC, stage 6, p<0.001/Kappa 0.86/31% deflection),
  FinPulse (PDLC, stage 4, drop-off 46%→18%), VeloceAI (STARTUP, stage 3,
  FINOPS_CAP **FAIL** gate — demonstrates 409 execution blocking), OmniCare
  (LEGACY, stage 2, Data/Ontology 2/5 red flag). Timestamps span 90 days.
- When changing engine math, keep `seed_showcase.novatel_results` headline
  assertions in `tests/test_seed_showcase.py` in sync (kappa exactly 0.86 via
  engineered label sets: observed .93 / expected .50).

## Frontend executive console (Step 6)

- Navy-sidebar shell (`app.component.ts`) with signal-based toast overlay
  (`core/toast.service.ts`); Tailwind palette mirrors doc_factory
  (navy/sky/slateink/emeraldok in `tailwind.config.js`).
- Routes: `/` portfolio dashboard, `/engagements/:id` lifecycle workspace
  (both lazy standalone).
- `core/api.service.ts`: engagement CRUD + gates/mentoring/artifacts,
  `runStage(path, body)` → ai-engine sandbox, `renderDocument(...)` → Blob.
  All through the existing dev proxy (`/api/core`, `/api/ai`).
- `core/engagement-state.service.ts`: shared signals (engagement, gates,
  mentoring, activeStage, per-stage sandbox results); the Artifact Studio
  reads the active stage's latest result when rendering PPTX/DOCX.
- Lifecycle stepper allows free jumping (UI-level); "Run / Recalculate"
  buttons hit ai-engine stage endpoints directly (ungoverned sandbox) —
  governed execution stays in core-api's /execute.
- Stage 4 console animates trace steps at 600ms intervals with 4 presets;
  charts are plain Chart.js (registered once in `main.ts`), recreated per run
  and destroyed on unmount.

## Local execution modes & smoke tests (Step 7)

- **Docker mode:** `make up` (compose networking verified: frontend proxy
  → core-api:8080 / ai-engine:8000; core-api → ai-engine + postgres).
- **Docker-free fallback:** `start-local.ps1` / `start-local.sh` — Spring
  `local` profile (`application-local.yml`: H2 file DB in PG mode, Flyway
  off, DataSeeder on; H2 is runtime-scoped in pom.xml for this) + ai-engine
  venv uvicorn + `ng serve --proxy-config proxy.local.json`.
- **Smoke tests:** `scripts/smoke_test.py` (stdlib-only; `make smoke`;
  env CORE_URL/AI_URL overrides) — 23 checks: 4 seeded clients + stage
  positions, Stage 2 radar/red-flags + OmniCare gates, Stage 4 trace,
  stages 1-6 × PPTX/DOCX OPC-valid downloads. Verified 23/23 PASS on the
  live fallback stack 2026-11-17.
- Root `README.md` is the <2-minute quickstart (both modes + smoke).

## Completed task history

- **Step 1 (bootstrap):** full monorepo scaffold, local compose stack,
  health checks, mock-LLM deterministic simulator, local/S3 storage adapters,
  seed data, test suites for all 3 services, Terraform skeletons,
  provider-neutral Helm chart.
  See `docs/00-architecture-plan.md` and `docs/01-task-breakdown.md`.
- **Step 2 (core-api lifecycle):** 6-stage lifecycle domain (4 aggregates),
  governance gating, mentoring progress, stage-execution orchestration proxy
  to ai-engine, springdoc Swagger UI, 52 unit/web tests green.
  See `docs/02-core-api-lifecycle-plan.md` and
  `docs/03-core-api-lifecycle-tasks.md`.
- **Step 3 (ai-engine intelligence):** six `/api/v1/engine` stage routers —
  pitch ROI simulator, 5-pillar maturity audit, domain blueprints, 4-step
  live multi-agent demo (PII redaction + deterministic mock), full statistical
  ROI suite (Welch/Mann-Whitney/CI, DiD, Kappa, Wilson CI, PSI, NEV/TCO),
  30-60-90 roadmap + mentoring curriculum. 56 pytest tests green.
  See `docs/04-ai-engine-intelligence-plan.md` and
  `docs/05-ai-engine-intelligence-tasks.md`.
- **Step 4 (document factory):** themed boardroom PPTX/DOCX generation for
  all 6 stages with embedded high-DPI matplotlib charts, governance matrices
  and sign-off checklists; `/documents/render` streams + persists via the
  storage adapter. 83 pytest tests green.
  See `docs/06-doc-factory-plan.md` and `docs/07-doc-factory-tasks.md`.
- **Step 5 (showcase seeder):** Java DataSeeder (auto on empty DB) + Python
  seed_showcase.py (30 real deliverables) populating 4 enterprise engagements
  across all tracks/stages with 90-day history, governance statuses and
  statistical proof. Java 59/59 + Python 91/91 tests green.
  See `docs/08-showcase-seeder-plan.md`.
- **Step 6 (frontend console):** executive portfolio dashboard (showcase
  cards, KPI strip, engagement wizard) + 6-stage interactive lifecycle
  workspace (free-jump stepper, per-stage forms/charts, animated multi-agent
  console, statistical/CFO dashboard, 30-60-90 board, PPTX/DOCX Artifact
  Studio with toasts). `ng build` green. See `docs/09-frontend-plan.md`.
- **Step 7 (integration & smoke):** compose wiring verified; Docker-free
  fallback (H2 local profile + start-local scripts + proxy.local.json);
  stdlib smoke suite executed live — 23/23 PASS (seeded clients, Stage 2
  diagnostics+gates, Stage 4 trace, 12 document downloads); quickstart
  README. See `docs/10-integration-smoke-plan.md`.
