# Task Breakdown — Document Generation Factory (Step 4)

Implementing the approved plan (Option A: builder modules + content registry).

## T1 — Scaffolding & deps
- [x] `app/doc_factory/` package; `matplotlib==3.9.2` added to requirements
- [x] Router mounted in `main.py` under `/api/v1/engine` (documents prefix)

## T2 — Theme & charts
- [x] `theme.py`: Deep Navy #0F172A, Electric Sky #0284C7, Slate #334155,
      Emerald #059669, white backgrounds; pptx/docx RGB converters;
      status colors for governance matrices
- [x] `charts.py`: headless Agg, 200 DPI PNG factories — copilot-vs-agent
      trajectory, maturity radar, architecture footprint, evaluator confidence,
      A/B CI distribution (NEV fallback), 30-60-90 Gantt; themed placeholder
      on missing data (chart can never sink a deliverable)

## T3 — Content & builders
- [x] `content.py`: StageContent dataclass + per-stage extractors (defensive
      defaults), governance rows from stage_result when forwarded
- [x] `pptx_builder.py` — `generate_stage_pptx(stage, engagement, result) -> bytes`:
      7-slide 16:9 deck (Title, Exec Summary & 4 Pillars, Chart, Key Findings,
      Execution Table, Governance & Risk matrix with colored statuses, Next Steps)
- [x] `docx_builder.py` — `generate_stage_docx(...) -> bytes`: navy cover
      header, executive callout box, pillars table, findings bullets, detail
      table, embedded chart PNG, governance matrix, sign-off checklist

## T4 — Endpoint
- [x] `router.py` — `POST /api/v1/engine/documents/render`
      {stageNum, format pptx|docx, engagementData, stageResult} → persists via
      storage adapter (local `/data/artifacts` or S3/Blob/GCS by env) and
      streams bytes with Content-Disposition + X-Artifact-Key headers;
      ASCII-safe filename slug (bug found & fixed by the unicode edge test)

## T5 — Tests
- [x] `tests/test_doc_factory.py`: 27 tests — all 6 stages × both formats via
      the endpoint (with storage assertion), OPC package validation (7 slides,
      embedded PNGs, document.xml content), chart PNG checks, placeholder
      fallback, invalid stage/format 422s, empty-payload edge, unicode client
      name edge, unconfigured cloud storage 501 edge, governance-row override

## T6 — Verification & wrap-up
- [x] Full ai-engine suite green: 83 passed (17 + 39 + 27), verified
      2026-11-17 on the Python 3.14 venv
- [x] AGENTS.md, docs and memory graph updated
