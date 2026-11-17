# Core API — AI Head Coach 6-Stage Lifecycle & Governance (Step 2 Plan)

## Goal

Implement the complete domain backend in `/core-api`: engagements, stage
artifacts, governance gates, mentoring progress, stage-transition rules, and a
proxy orchestration endpoint that validates governance, invokes `/ai-engine`
for diagnostics + PPTX/DOCX generation, persists artifact metadata, and
returns unified JSON. Swagger UI, CORS for `localhost:4200`, global error
handling, DTOs/mappers and unit tests included.

## Domain model

| Entity              | Key fields                                                                 |
|---------------------|----------------------------------------------------------------------------|
| `ClientEngagement`  | clientName, industry, domainTrack (SDLC/PDLC/STARTUP/LEGACY), currentStage 1..6, advisorTier (DIAGNOSTIC_SPRINT/TRANSFORMATION_RETAINER/FRACTIONAL_HEAD_COACH), createdAt |
| `StageArtifact`     | engagementId, stageNumber 1..6, stageName, inputPayloadJson, diagnosticOutputJson, liveDemoStateJson, pptxFileUrl, docxFileUrl, generatedAt |
| `GovernanceGate`    | engagementId, gateName (PII_REDACTION/DETERMINISM_THRESHOLD/SHADOW_PARITY/HUMAN_IN_LOOP/FINOPS_CAP), status (PASS/WARN/FAIL), score, notes |
| `MentoringProgress` | engagementId, roleTrack (C_SUITE/ARCHITECT/ENGINEER/PRODUCT_MANAGER), moduleName, phase (SEE_ONE/CO_BUILD_ONE/LEAD_ONE), completionPct |

Canonical stage names (1→6): Discovery & Audit, Diagnostic & Baseline,
Pilot Design, Execution & Coaching, Measurement & ROI, Scale & Handoff.

## Options considered

### Option A — Modular package-by-feature + manual mappers (chosen)
Feature packages (`engagement`, `artifact`, `governance`, `mentoring`,
`orchestration`) each with entity/repo/service/DTOs/mapper; thin controllers;
`RestClient` for the ai-engine call; hand-written mapper classes.

- **Pros:** No annotation-processor fragility (MapStruct+Lombok processor
  ordering is a classic CI trap); mappers are trivial and testable; smallest
  dependency surface; feature packages scale cleanly.
- **Cons (devil's advocate):** Manual mappers are boilerplate that MapStruct
  would generate; risk of drift if DTOs grow large (mitigated: mappers are
  single-responsibility and unit-tested via service tests).

### Option B — MapStruct-generated mappers
- **Pros:** Zero mapping boilerplate, compile-time checked.
- **Cons (devil's advocate):** Adds `mapstruct` + `mapstruct-processor` to the
  build; processor misconfiguration fails only at compile time inside Docker;
  for 4 small aggregates the generated-code payoff is marginal.

### Option C — Spring Data REST + projections
- **Pros:** Near-zero controller code.
- **Cons (devil's advocate):** No place for governance validation and proxy
  orchestration logic; HAL output mismatches the required "unified JSON";
  rejected.

**Recommendation: Option A** — most reliable build, clearest seams for the
governance/orchestration business logic the task actually centres on.

## Key rules

1. **Stage transitions:** forward only one step at a time (`current+1`);
   backward moves allowed (rework); target must be 1..6.
2. **Governance gating:** `execute` is blocked (HTTP 409) if any gate for the
   engagement has status `FAIL`; `WARN` gates are allowed but echoed in the
   response. No gates ⇒ pass-through (bootstrapping rule).
3. **Execute contract:** `POST /api/v1/engagements/{id}/stages/{stageNum}/execute`
   must target the engagement's `currentStage`; on success a `StageArtifact`
   is persisted (diagnostics JSON + pptx/docx locators from ai-engine) and the
   engagement auto-advances one stage (capped at 6).
4. **ai-engine integration:** `RestClient` against `app.ai-engine-url`
   (12-factor env `AI_ENGINE_URL`); failures map to HTTP 502 with a clear
   message — the engagement state is never mutated on failure.
5. **Migration naming:** the original demo `V1__init.sql` is replaced by
   `V1__init_schema.sql` (schema was never deployed anywhere, so renaming the
   baseline is safe). The `coaches` table is retained for the existing
   dashboard; the old demo `engagements` table is superseded by
   `client_engagements`. Seed data updated accordingly.

## API surface (all under `/api/v1`)

```
POST   /engagements                                  create
GET    /engagements                                  list
GET    /engagements/{id}                             get
PUT    /engagements/{id}                             update (name/industry/track/tier)
DELETE /engagements/{id}                             delete
POST   /engagements/{id}/stage-transitions           {targetStage} with rules
POST   /engagements/{id}/stages/{stageNum}/execute   governance + ai-engine + artifact
GET    /engagements/{id}/artifacts                   list stage artifacts
GET    /engagements/{id}/gates                       list gates
POST   /engagements/{id}/gates                       upsert gate result
GET    /engagements/{id}/mentoring                   list mentoring progress
POST   /engagements/{id}/mentoring                   record/update progress
```

Swagger UI via springdoc at `/swagger-ui.html`; CORS for `http://localhost:4200`
(already env-overridable through `app.cors-allowed-origins`).

## Out of scope

AuthN/Z, async execution/queues, pagination, ai-engine contract changes.
