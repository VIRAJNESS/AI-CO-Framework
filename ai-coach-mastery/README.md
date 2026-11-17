# AI Coach Mastery

Cloud-agnostic AI Head Coach platform: Angular 18 executive console,
Spring Boot 3.3 lifecycle API, and a FastAPI intelligence engine that runs
the full 6-stage coaching lifecycle with **zero cloud keys**
(`LLM_PROVIDER=mock`, `STORAGE_PROVIDER=local`).

## 🚀 Start locally in under 2 minutes

### Option A — Docker (recommended)

```bash
cd ai-coach-mastery
make up                       # builds + starts postgres/redis/minio + 3 services
make seed                     # coaches SQL + 30 showcase PPTX/DOCX deliverables
# open http://localhost:4200  — 4 showcase clients auto-seeded on first start
```

No `make`? Use compose directly:

```bash
copy .env.example .env        # (cp on macOS/Linux)
docker compose -f infra/local/docker-compose.yml --env-file .env up -d --build
```

### Option B — Docker-free fallback (H2 + local filesystem)

Docker Desktop not running? Prereqs: JDK 21+, Python 3.11+, Node 20+.

```powershell
cd ai-coach-mastery
.\start-local.ps1             # Windows — launches all 3 tiers in own windows
```

```bash
./start-local.sh              # macOS/Linux — background PIDs + .local-logs/
```

The `local` Spring profile uses an H2 file DB (showcase auto-seeds);
ai-engine runs in a venv; the frontend proxies via `proxy.local.json`.

### Verify everything is wired

```bash
python scripts/smoke_test.py  # or: make smoke
```

Checks: 4 seeded clients via `GET /api/v1/engagements`, Stage 2 maturity
radar + governance gates, Stage 4 four-step agentic trace, and valid
PPTX/DOCX downloads for all 6 stages (28 assertions).

## What you get

| URL | What |
|-----|------|
| http://localhost:4200 | Executive console — portfolio, 6-stage workspace, artifact studio |
| http://localhost:8080/swagger-ui.html | Core API (engagements, gates, mentoring, governed execution) |
| http://localhost:8000/docs | AI engine (pitch ROI, audit, blueprints, live demo, stats, roadmap, doc factory) |
| http://localhost:9001 | MinIO console (Docker mode; minioadmin/minioadmin) |

**Showcase clients (auto-seeded):** NovaTel (SDLC, stage 6 — p<0.001 proof),
FinPulse (PDLC, stage 4 — drop-off 46%→18%), VeloceAI (STARTUP, stage 3 —
FinOps FAIL gate demo), OmniCare (LEGACY, stage 2 — red-flag audit).

## Everyday commands

```bash
make up / down / logs / ps    # stack lifecycle
make seed                     # demo data + showcase deliverables
make smoke                    # end-to-end smoke tests
make test                     # all unit suites (Java 59, Python 91, Karma)
make clean                    # down + delete volumes
```

## 12-factor switches (cloud portability)

| Variable | Values | Local default |
|----------|--------|---------------|
| `LLM_PROVIDER` | mock \| openai \| anthropic \| azure_openai \| bedrock \| vertex | `mock` |
| `STORAGE_PROVIDER` | local \| s3 \| azure_blob \| gcs | `local` |
| `DB_URL` / `REDIS_URL` | connection URLs | compose-internal |

Cloud skeletons: `infra/cloud/terraform/modules/{azure,aws,gcp}` +
provider-neutral Helm chart `infra/cloud/helm/ai-coach-mastery`.

## Repository layout

```
frontend/      Angular 18 console (standalone + Signals + Tailwind + Chart.js)
core-api/      Spring Boot 3.3 — 6-stage lifecycle, governance, orchestration
ai-engine/     FastAPI — stage intelligence, statistics, PPTX/DOCX factory
infra/local/   docker-compose + Postgres init/seed
infra/cloud/   Terraform skeletons + Helm chart
scripts/       smoke_test.py
docs/          architecture plans & task breakdowns (00–10)
```

See `AGENTS.md` for conventions and `docs/` for every design decision.
