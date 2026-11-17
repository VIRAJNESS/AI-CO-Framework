# AI Engine — Document Generation Factory (Step 4 Plan)

## Goal

A dedicated `app/doc_factory/` package producing boardroom-ready `.pptx` and
`.docx` deliverables for ANY of the 6 stages, with a unified corporate theme,
high-DPI matplotlib charts (headless Agg), persisted via the storage adapter
and streamed back for one-click download via
`POST /api/v1/engine/documents/render`.

## Options considered

### Option A — Builder modules + stage content registry (chosen)
`theme.py` (palette/fonts), `charts.py` (Agg chart PNG factories),
`content.py` (per-stage narrative extraction from `stage_result`),
`pptx_builder.py` / `docx_builder.py` (format renderers), `router.py`.

- **Pros:** Charts and narrative are shared by both formats (zero duplication);
  stage-specific knowledge lives in one registry; builders stay format-pure;
  easy to add stage 7+ later.
- **Cons (devil's advocate):** One more indirection layer vs. inlining content
  in builders — justified because both PPTX and DOCX consume identical content.

### Option B — Jinja-templated HTML → WeasyPrint PDF + conversions
- **Cons (devil's advocate):** Cannot produce native editable `.pptx`/`.docx`
  (hard requirement); conversion tools (libreoffice) balloon the image. Rejected.

### Option C — Extend existing `services/reports.py`
- **Cons (devil's advocate):** reports.py is a deliberately simple generic
  title+summary renderer used by core-api Step 2; mixing a themed multi-slide
  engine into it couples two different consumers. Keep both; doc_factory is
  the rich path. Rejected.

**Recommendation: Option A.**

## Design decisions

1. **Theme:** Deep Navy `#0F172A`, Electric Sky `#0284C7`, Slate `#334155`,
   Emerald `#059669`, white backgrounds — single constants module consumed by
   charts (matplotlib hex) and documents (RGBColor).
2. **Charts (200 DPI PNG bytes, Agg backend set before pyplot import):**
   - stage1 → Copilot vs Agent 12-month trajectory (line)
   - stage2 → Maturity radar (5 pillars)
   - stage3 → Component/agent count bar ("architecture footprint")
   - stage4 → Evaluator confidence vs thresholds (bar + threshold line)
   - stage5 → A/B distribution histogram w/ CI band (falls back to NEV bar)
   - stage6 → 30-60-90 Gantt (broken_barh)
   Charts degrade gracefully: missing data ⇒ themed placeholder chart.
3. **PPTX deck (6–8 slides):** Title → Executive Summary & 4 Pillars → Chart →
   Architecture/Execution table → Governance & Risk matrix → Next steps
   (+ optional stage-specific extras). 16:9, navy title band style.
4. **DOCX deliverable:** styled cover header, executive callout box (table with
   shaded cell), findings sections, formatted tables, embedded chart PNG,
   sign-off checklist table.
5. **Endpoint:** `POST /api/v1/engine/documents/render`
   body: `{stageNum, format: pptx|docx, engagementData{}, stageResult{}}` →
   saves via `get_storage_provider` (local ⇒ `/data/artifacts`, or S3/Blob/GCS
   by env) and returns `Response` with the file bytes +
   `Content-Disposition: attachment` + `X-Artifact-Key` header.
6. **New dependency:** `matplotlib` (Agg only — no GUI libs needed in slim image).

## Out of scope

PDF rendering (reports.py already covers), slide templates per client brand,
async rendering queues.
