# Integration Wiring, Fallback Mode & Smoke Tests (Step 7 Plan)

## Goal

Verify the three tiers execute together seamlessly: confirm compose
networking, add a Docker-free fallback (`start-local.*`) using H2 + local
filesystem storage, run automated smoke tests against the live stack, and
ship a <2-minute quickstart README.

## Networking verification (compose)

Already correct and re-confirmed:
- `frontend` (dev stage) runs `ng serve` with `proxy.conf.json`:
  `/api/core/** → http://core-api:8080/api/v1/**`,
  `/api/ai/** → http://ai-engine:8000/api/v1/**`, plus `/health/*` maps.
- `core-api` receives `AI_ENGINE_URL=http://ai-engine:8000` and
  `DB_URL=jdbc:postgresql://postgres:5432/aicoach`; `depends_on` with
  healthchecks ensures ordering. All services share the `acm` bridge network.
- Prod nginx stage mirrors the same proxy contract.

## Options for the fallback mode

### Option A — Spring `local` profile (H2 file DB) + venv uvicorn + ng serve with localhost proxy (chosen)
- **Pros:** zero containers; H2 in PostgreSQL mode reuses JPA entities with
  `ddl-auto=update` (Flyway off); DataSeeder still populates the showcase;
  ai-engine already runs anywhere with STORAGE_PROVIDER=local; one script
  starts everything in background windows.
- **Cons (devil's advocate):** H2 isn't byte-identical to Postgres (no
  pgvector) — acceptable: fallback is for app development/demo, pgvector
  features aren't used yet; Flyway-vs-ddl drift is confined to the `local`
  profile.

### Option B — Testcontainers-style embedded Postgres
- **Cons:** still requires Docker — defeats the purpose. Rejected.

### Option C — SQLite via Hibernate community dialect
- **Cons:** extra dependency + weaker JPA support than H2's PG mode. Rejected.

## Smoke tests

`scripts/smoke_test.py` — stdlib-only (urllib), no pip deps, runs against any
base URLs (env `CORE_URL` / `AI_URL`, defaults localhost:8080/8000):
1. `GET /api/v1/engagements` → exactly the 4 showcase clients.
2. `POST stage2/diagnostic-audit` → maturity radar JSON (5 pillarScores,
   maturityIndex) **and** `GET /engagements/{id}/gates` → governance gates
   present for the showcase client.
3. `POST stage4/live-demo` → 4-step agentic trace (steps 1..4, verdict).
4. For stages 1–6 × {pptx, docx}: `POST documents/render` → HTTP 200,
   non-empty body starting with the OPC `PK\x03\x04` magic (12 downloads).

## Deliverables

- `core-api/src/main/resources/application-local.yml` (H2 + seeder on)
- `start-local.ps1` + `start-local.sh` (deps check → launch 3 tiers)
- `frontend/proxy.local.json` (localhost targets for the fallback mode)
- `scripts/smoke_test.py` (+ `make smoke` target)
- Root `README.md` rewritten with exact <2-minute commands
- Smoke tests executed against the locally started stack (fallback mode,
  since Docker Desktop is unavailable on this machine)

## Execution results (2026-11-17)

Stack started via the fallback path (core-api `local` profile + venv uvicorn):

```
[0] UP core-api / UP ai-engine
[1] 4 showcase clients seeded, lifecycle positions 6/4/3/2        — 3 PASS
[2] Stage 2 radar JSON + maturity + red flags + OmniCare gates    — 5 PASS
[3] Stage 4 four-step agentic trace + verdict                     — 3 PASS
[4] Stages 1-6 × PPTX/DOCX: all valid OPC binaries (>5KB each)    — 12 PASS
==== 23 passed, 0 failed ====
```

Notes: H2 `local` profile booted core-api with DataSeeder populating the
showcase (confirming the fallback DB path); one fix applied during
verification — H2 moved from test to runtime scope in `pom.xml`.
