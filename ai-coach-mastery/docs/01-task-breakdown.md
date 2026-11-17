# Task Breakdown — Step 1 Bootstrap

Discrete, self-contained tasks implementing the approved plan (Option A).

## T1 — Root scaffolding
- [x] `Makefile` (`up`, `down`, `seed`, `test`, `build-all`)
- [x] `README.md`, `.gitignore`, `.env.example`, `.editorconfig`

## T2 — Local infrastructure (`/infra/local`)
- [x] `docker-compose.yml`: postgres16+pgvector, redis7, minio, core-api,
      ai-engine, frontend; health checks; named volumes; single network
- [x] `postgres/init/01-init.sql`: schemas `core`/`ai`, `CREATE EXTENSION vector`
- [x] `seed/seed.sql`: demo data for `make seed`

## T3 — core-api (Java 21 / Spring Boot 3.3)
- [x] `pom.xml`: web, data-jpa, flyway, validation, actuator, postgres, tests
- [x] `application.yml` driven by `DB_URL`/`REDIS_URL` env vars
- [x] Flyway `V1__init.sql` (coaches, engagements tables in `core` schema)
- [x] Domain: `Coach` entity, repository, service, REST controller, DTOs
- [x] Health: Actuator `/actuator/health` exposed
- [x] Multi-stage `Dockerfile` (maven build → JRE 21 runtime)
- [x] Unit/web tests (happy, negative, edge cases)

## T4 — ai-engine (Python 3.11 / FastAPI)
- [x] `requirements.txt` + `pyproject.toml`: fastapi, pydantic v2, sqlalchemy,
      scipy, statsmodels, numpy, python-pptx, python-docx, reportlab, weasyprint,
      redis, boto3 (for MinIO/S3 adapter)
- [x] `app/core/config.py`: pydantic-settings, 12-factor env vars
- [x] Ports & adapters: `LLMProvider` (mock deterministic simulator + stubs),
      `StorageProvider` (local + s3/minio + stubs for azure_blob/gcs)
- [x] Routers: `/health`, `/api/v1/analysis/roi` (SciPy/statsmodels),
      `/api/v1/coach/insights` (mock LLM), `/api/v1/reports` (docx/pptx/pdf)
- [x] `Dockerfile` with WeasyPrint system deps
- [x] pytest suite (happy, negative, ≥3 edge cases)

## T5 — frontend (Angular 18)
- [x] Standalone bootstrap (`app.config.ts`, no NgModules)
- [x] Signals-based dashboard component; Chart.js via ng2-charts-free wrapper
      (direct chart.js usage); lucide-angular icons; TailwindCSS
- [x] Environment-driven API base URLs; health proxy
- [x] `Dockerfile` (dev: ng serve; prod stage: nginx)

## T6 — cloud skeletons (`/infra/cloud`)
- [x] Terraform `modules/azure|aws|gcp`: `main.tf`, `variables.tf`, `outputs.tf`
      defining the provisioning contract (db, cache, storage, registry, cluster)
- [x] Helm chart `helm/ai-coach-mastery`: Chart.yaml, values.yaml (+ per-cloud
      values), templates for 3 deployments/services, ingress, configmap, secret

## T7 — verification
- [x] Validate compose config, file tree, Makefile targets, docs updated
