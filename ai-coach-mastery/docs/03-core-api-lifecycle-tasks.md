# Task Breakdown — Core API 6-Stage Lifecycle (Step 2)

Discrete tasks implementing the approved plan (Option A, manual mappers).

## T1 — Build & config
- [x] `pom.xml`: add `springdoc-openapi-starter-webmvc-ui`
- [x] `application.yml`: springdoc paths; keep env-driven config
- [x] `OpenApiConfig` bean (title/version/description)

## T2 — Database
- [x] Replace `V1__init.sql` with `V1__init_schema.sql`:
      coaches (kept), client_engagements, stage_artifacts, governance_gates,
      mentoring_progress (+ CHECK constraints, FKs, indexes)
- [x] Update `infra/local/seed/seed.sql` for new tables

## T3 — Domain layer
- [x] Enums: `DomainTrack`, `AdvisorTier`, `GateName`, `GateStatus`,
      `RoleTrack`, `MentoringPhase`, `Stage` (1..6 + names)
- [x] Entities: `ClientEngagement`, `StageArtifact`, `GovernanceGate`,
      `MentoringProgress`
- [x] Repositories for each entity (query methods per feature needs)

## T4 — Application layer
- [x] DTOs per feature (create/update/response records w/ validation)
- [x] Manual mapper classes per feature
- [x] `EngagementService` (CRUD + transition rules)
- [x] `GovernanceService` (upsert + evaluate gates for execution)
- [x] `MentoringService` (record/list progress)
- [x] `AiEngineClient` (RestClient: insights + report generation)
- [x] `StageExecutionService` (orchestration: gates → ai-engine → artifact →
      auto-advance; 502 on upstream failure; no state mutation on failure)

## T5 — Web layer
- [x] `EngagementController` (CRUD + transitions)
- [x] `StageExecutionController` (execute endpoint)
- [x] `GovernanceController`, `MentoringController`, `StageArtifactController`
- [x] Extend `GlobalExceptionHandler` (409 conflict-rule, 502 upstream)

## T6 — Tests (happy / negative / ≥3 edge each area)
- [x] `EngagementServiceTest` (transition rules incl. edges)
- [x] `StageExecutionServiceTest` (gate blocking, upstream failure, stage-6 cap)
- [x] `GovernanceServiceTest` (upsert/evaluation)
- [x] `EngagementControllerTest` + `StageExecutionControllerTest` (web/validation)

## T7 — Wrap-up
- [x] `mvn test` green: 52 tests, 0 failures, 0 errors (verified 2026-11-17)
- [x] Update AGENTS.md, docs, memory graph
