# Frontend — Executive Console (Step 6 Plan)

## Goal

Complete Angular 18 frontend: executive portfolio dashboard (4 showcase
clients + new-engagement wizard + KPI strip) and a 6-stage interactive
lifecycle workspace per engagement with free stage jumping, dynamic input
forms, live Chart.js visualizations, an animated multi-agent sandbox, and an
on-demand artifact studio (Run / PPTX / DOCX downloads with toasts).
Aesthetic: Deep Navy sidebar, slate workspace, sky accents (doc_factory theme).

## Options considered

### Option A — Stage child components + shared signal state service (chosen)
`EngagementStateService` (signals: engagement, per-stage results) + six
standalone stage components under a stepper shell; `ApiService` gains typed
engine/engagement/document methods; downloads via Blob + anchor.

- **Pros:** Stage panels stay independently testable; parent action bar reads
  the active stage's latest result for document rendering; signals keep
  cross-panel sync trivial; matches repo conventions (standalone, signals).
- **Cons (devil's advocate):** A service-per-feature adds a file vs. passing
  inputs — but prop-drilling six stages through a stepper is strictly worse.

### Option B — One mega engagement component with ngSwitch
- **Cons:** ~1200-line component, chart lifecycle chaos on switch, untestable.

### Option C — NgRx store
- **Cons:** Heavy ceremony for a demo console; signals already cover it.

**Recommendation: Option A.**

## Design decisions

1. **Routing:** `/` dashboard, `/engagements/:id` lifecycle (lazy standalone).
2. **Proxy reuse:** `/api/core/*` → core-api `/api/v1/*`; `/api/ai/*` →
   ai-engine `/api/v1/*` (engine + documents/render) — no new infra.
3. **Charts:** direct Chart.js; every stage view re-creates its chart on run;
   destroy on unmount (established pattern).
4. **Stage 4 animation:** trace steps revealed sequentially via timed signal
   updates; 4 one-click sample presets (bug log / legacy / complaint / PRD).
5. **Downloads:** `ApiService.renderDocument` fetches Blob (responseType
   blob), triggers anchor download, toast on success/failure.
6. **Wizard:** modal posting to core-api `POST /engagements`, then navigates
   to the new lifecycle page.
7. **KPI strip:** derived from engagement list + per-client static showcase
   metrics; governance/mentoring aggregates fetched per engagement.
8. **Stage jumping is UI-level** (view any stage freely); core-api execute
   remains governed — "Run / Recalculate" calls the ai-engine stage endpoints
   directly (ungoverned analytical sandbox), matching the demo intent.
9. **Existing ApiService health/coach methods retained** (dashboard spec
   stays green); new methods added alongside.

## Task breakdown

- [x] T1 models.ts + ApiService extension (engagements CRUD/gates/mentoring/
      artifacts, runStage, renderDocument blob)
- [x] T2 ToastService (signal queue, auto-dismiss) + navy sidebar shell with
      toast overlay; Tailwind palette extended (navy/sky/slateink/emeraldok)
- [x] T3 EngagementStateService (engagement/gates/mentoring/activeStage +
      per-stage result map, engagementData computed for doc factory)
- [x] T4 Dashboard: 4 showcase client cards w/ progress bars + headlines,
      KPI strip (avg toil, net ROI, gates w/ FAIL count, mentoring avg),
      New Client Engagement wizard modal → creates + navigates
- [x] T5 Lifecycle shell: free-jump 6-step stepper (completed=emerald,
      active=sky), Artifact Studio (Executive PPTX / Word Report, blob
      download + toasts, uses active stage's latest sandbox result)
- [x] T6 Stage components: 1 ROI curve w/ sliders + 4-pillar cards;
      2 radar + maturity + red-flag badges + roadmap; 3 architecture flow
      cards w/ track selector; 4 animated agent console (4 presets, 600ms
      step reveal, verdict badge); 5 CI bar + Kappa/PSI gauges + NEV
      waterfall w/ editable A/B + economics; 6 30-60-90 board + curriculum
      + live mentoring progress bars
- [x] T7 Routes (/, /engagements/:id lazy), app.config icon registry,
      Chart.js registered once in main.ts
- [x] T8 Specs: ToastService (5), EngagementStateService (8), ApiService
      +4 new-method tests (proxy paths, blob payload, error propagation)
- [x] T9 `ng build` green (zero errors; lazy chunks for dashboard +
      lifecycle confirm routing), verified 2026-11-17
