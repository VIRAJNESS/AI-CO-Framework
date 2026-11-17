# Showcase Seeder — 4 Enterprise Engagements (Step 5 Plan)

## Goal

Instant "look-alike" live showcase: 4 realistic enterprise engagements covering
all 4 tracks and all 6 lifecycle stages, with 90-day temporal spread,
pre-computed metrics, governance gate statuses, working demo inputs and real
downloadable `.pptx`/`.docx` artifacts.

## Showcase roster

| Client | Track | Stage | Signature numbers |
|--------|-------|-------|-------------------|
| NovaTel Global Telecom | SDLC | 6 (mature) | 450 eng, 180K tickets/mo, 31% deflection, 68% triage-toil cut, 85% faster deploys, p<0.001, Kappa 0.86 |
| FinPulse Digital Banking | PDLC | 4 (active PoC) | 46% checkout drop-off → 18% in live demo; Maturity 3.1/5 |
| VeloceAI Series-B SaaS | STARTUP | 3 (blueprinting) | 35 engineers, $48K/mo tokens, −54% inference unit cost target |
| OmniCare Core Insurance | LEGACY | 2 (discovery audit) | 22-yr Java monolith + mainframe; Data/Ontology 2.0/5 red flag |

## Options considered

### Option A — Split ownership: Java `DataSeeder` (DB) + Python `seed_showcase.py` (artifacts) — chosen
- Java `CommandLineRunner` auto-seeds core tables on first startup when
  `client_engagements` is empty (toggle `app.seed-demo-data`, default true);
  fixed UUIDs, deterministic artifact keys, timestamps staggered over 90 days.
- Python script computes real stage results via the engine's pure functions
  and renders/stores the actual PPTX/DOCX files at exactly those keys via the
  storage port. `make seed` runs it inside the ai-engine container.
- **Pros:** respects schema ownership (Flyway/JPA own `core`), artifacts are
  genuine doc_factory output (not fakes), each side independently idempotent,
  works in mock mode with zero keys.
- **Cons (devil's advocate):** artifact URLs exist in DB before files exist if
  user never runs `make seed` — acceptable: keys are deterministic and the UI
  degrades to "generate on demand"; running `make seed` completes the picture.

### Option B — Python does everything incl. DB inserts via SQLAlchemy
- **Cons:** violates the "Flyway/core-api owns the core schema" convention;
  duplicates entity invariants in SQL strings. Rejected.

### Option C — Giant Flyway seed migration
- **Cons:** migrations are schema, not demo data; can't generate real binary
  artifacts; makes clean production deploys carry demo rows. Rejected.

## Design decisions

1. **Deterministic artifact keys:** `showcase/{slug}/stage{n}.{pptx|docx}` so
   DB rows and generated files always align.
2. **Old `seed.sql` slims down to coaches only** — engagements now come from
   `DataSeeder`; `make seed` becomes: SQL coaches + `seed_showcase.py`.
3. **DataSeeder is skip-if-nonempty** (count>0 ⇒ no-op) and test-covered.
4. **Timestamps:** NovaTel started ~88d ago (full arc), FinPulse ~60d,
   VeloceAI ~35d, OmniCare ~14d; artifacts spaced realistically inside each.
5. **Stage results in seed_showcase.py** come from the real engine functions
   (`compute_pitch`, `compute_audit`, `build_blueprint`, live-demo helpers,
   `statistical-roi` analyzers, `build_roadmap`) — numbers tuned via inputs to
   land on the scenario headlines (e.g. identical-seed friction log, Kappa
   labels crafted to 0.86).

## Task breakdown

- [x] T1 Java `DataSeeder` (4 engagements + 15 artifacts + 16 gates +
      mentoring, 90-day timestamps, deterministic keys, APP_SEED_DEMO_DATA
      toggle, skip-if-nonempty)
- [x] T2 `application.yml` property (`app.seed-demo-data`) + test-profile
      disable (seeding covered explicitly by DataSeederTest)
- [x] T3 `DataSeederTest` — 7 tests (tracks/stages, deterministic keys +
      NovaTel stats JSON, skip-when-nonempty, 90-day window, VeloceAI FinOps
      FAIL gate, NovaTel LEAD_ONE maturity, OmniCare stage cap)
- [x] T4 `ai-engine/seed_showcase.py` — 30 real PPTX/DOCX deliverables via
      doc_factory + storage port; stage results from the engine's own pure
      functions (Kappa labels engineered to exactly 0.86, toil samples to
      p<0.001 and −68%)
- [x] T5 `tests/test_seed_showcase.py` — 8 tests (30-artifact contract, key
      format parity with Java, headline-number assertions, gcs 501 guard,
      stage-coverage mirror, determinism, idempotent overwrite, binary content)
- [x] T6 Makefile `seed` now: coaches SQL + `python seed_showcase.py` in the
      ai-engine container; seed.sql slimmed to coaches; Dockerfile copies the
      script into test+runtime stages
- [x] T7 Verified 2026-11-17: Java 59/59 green (incl. DataSeederTest),
      Python 91/91 green; docs/AGENTS/memory updated
