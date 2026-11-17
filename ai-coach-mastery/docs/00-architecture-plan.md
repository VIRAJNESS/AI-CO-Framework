# AI Coach Mastery — Architecture Plan (Step 1: Local-First Monorepo)

## Goal

Initialize a production-grade, cloud-agnostic monorepo with three services
(Angular frontend, Spring Boot core API, FastAPI AI engine) orchestrated
locally via Docker Compose, with skeleton IaC (Terraform + Helm) for later
Azure / AWS / GCP deployment. Step 1 must run out-of-the-box with **zero
cloud keys** (`LLM_PROVIDER=mock`, `STORAGE_PROVIDER=local`).

## Options Considered

### Option A — Single-repo polyrepo-style folders (chosen)
Plain folders per service (`/frontend`, `/core-api`, `/ai-engine`, `/infra`)
with a root `Makefile` as the orchestration entry point.

- **Pros:** Zero tooling lock-in; each service keeps its idiomatic build tool
  (npm/ng, Maven, pip); Dockerfiles are self-contained; trivially splittable
  later; CI can path-filter.
- **Cons (devil's advocate):** No shared dependency graph or task caching;
  cross-service type contracts must be maintained manually (mitigated by
  OpenAPI specs each framework generates natively).

### Option B — Nx / Turborepo managed monorepo
- **Pros:** Task graph, caching, affected-only builds.
- **Cons (devil's advocate):** Nx's Java/Python support is plugin-based and
  second-class; adds a JS-toolchain dependency on top of Maven/pip teams;
  violates "keep each stack idiomatic"; overkill for 3 services.

### Option C — Bazel
- **Pros:** True polyglot hermetic builds.
- **Cons (devil's advocate):** Very steep learning curve; rules_jvm/rules_python
  maintenance burden; slows iteration for a Step-1 bootstrap dramatically.

**Recommendation: Option A.** Simplest thing that is production-credible,
cloud-agnostic, and keeps every stack idiomatic. Revisit Nx/Bazel only if the
service count grows past ~8.

## Cloud-Agnosticism Strategy (12-Factor)

All environment-specific behavior is injected via environment variables —
never compiled in:

| Variable           | Values                                                    | Default (local) |
|--------------------|-----------------------------------------------------------|-----------------|
| `STORAGE_PROVIDER` | `local` \| `s3` \| `azure_blob` \| `gcs`                  | `local`         |
| `LLM_PROVIDER`     | `mock` \| `openai` \| `anthropic` \| `azure_openai` \| `bedrock` \| `vertex` | `mock` |
| `DB_URL`           | JDBC / SQLAlchemy URL                                     | local Postgres  |
| `REDIS_URL`        | Redis connection URL                                      | local Redis     |
| `S3_ENDPOINT`      | MinIO locally, real endpoint in cloud                     | `http://minio:9000` |

Provider selection is implemented behind **ports-and-adapters interfaces**
(`StorageProvider`, `LLMProvider`) in `ai-engine`, so swapping cloud backends
is config-only. MinIO gives S3-compatibility locally so the `s3` adapter is
testable without AWS.

## Service Topology (local)

```
frontend (4200, Angular dev server / nginx)
   └─► core-api (8080, Spring Boot: domain, JPA, Flyway)
          └─► postgres:16 + pgvector (5432)
   └─► ai-engine (8000, FastAPI: stats, docs-gen, mock LLM)
          ├─► postgres (shared instance, separate schema)
          ├─► redis:7 (6379, caching/queues)
          └─► minio (9000/9001, artifact storage when STORAGE_PROVIDER=s3)
```

Health checks: `/actuator/health` (core-api), `/health` (ai-engine),
`/` (frontend), `pg_isready`, `redis-cli ping`, MinIO `/minio/health/live`.

## Key Decisions

1. **Shared Postgres instance, separate schemas** (`core`, `ai`) — one
   container locally, maps cleanly to separate managed DBs in cloud.
2. **pgvector** enabled via init script — ready for embeddings later.
3. **Mock LLM = deterministic intelligent simulator** — seeded hashing of the
   prompt produces stable, plausible structured responses; no network calls.
4. **Flyway owns the `core` schema**; SQLAlchemy owns `ai` schema.
5. **Helm chart is provider-neutral**: one chart, values files per cloud;
   Terraform modules are skeletons defining the contract (inputs/outputs) only.
6. **No secrets in the repo** — `.env.example` documents everything; compose
   uses safe local-only defaults.

## Out of Scope for Step 1

Real cloud provisioning, auth (OIDC), CI pipelines, real LLM adapters beyond
interface stubs, K8s manifests beyond the Helm chart skeleton.
