import {
  AfterViewInit, Component, ElementRef, OnDestroy, inject, signal, viewChild
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Chart } from 'chart.js';

import { ApiService } from '../../core/api.service';
import { EngagementStateService } from '../../core/engagement-state.service';
import { ToastService } from '../../core/toast.service';

const PILLARS = [
  { key: 'STRATEGY_KPI_ALIGNMENT', label: 'Strategy & KPI Alignment' },
  { key: 'DATA_ONTOLOGY_READINESS', label: 'Data & Ontology Readiness' },
  { key: 'CLOUD_AGENT_ARCHITECTURE', label: 'Cloud & Agent Architecture' },
  { key: 'RESPONSIBLE_AI_GUARDRAILS', label: 'Responsible AI & Guardrails' },
  { key: 'TALENT_PDLC_CULTURE', label: 'Talent & PDLC Culture' }
] as const;

/**
 * Stage 2 — Diagnostic Audit: 5-Pillar score sliders → AI Readiness Radar +
 * maturity index + red-flag governance badges.
 */
@Component({
  selector: 'app-stage2-audit',
  standalone: true,
  imports: [FormsModule, LucideAngularModule],
  template: `
    <div class="grid gap-6 xl:grid-cols-[340px,1fr]">
      <!-- Left: 5-pillar sliders -->
      <aside class="space-y-4 rounded-xl bg-white p-5 shadow-sm">
        <h3 class="text-sm font-bold text-navy">5-Pillar Scores (1–5)</h3>
        @for (pillar of pillarDefs; track pillar.key) {
          <div>
            <label class="text-xs font-semibold text-slateink">{{ pillar.label }}
              <span class="float-right font-bold text-sky">{{ scores[pillar.key] }}</span>
            </label>
            <input type="range" min="1" max="5" step="1"
                   [(ngModel)]="scores[pillar.key]" class="w-full accent-sky" />
          </div>
        }
        <button (click)="run()" [disabled]="running()"
                class="flex w-full items-center justify-center gap-2 rounded-lg bg-sky
                       py-2.5 text-sm font-semibold text-white transition
                       hover:bg-sky/90 disabled:opacity-40">
          <lucide-icon name="play" class="h-4 w-4"></lucide-icon>
          {{ running() ? 'Auditing…' : 'Run / Recalculate Stage' }}
        </button>
      </aside>

      <!-- Center: radar + maturity + red flags -->
      <section class="space-y-4">
        <div class="grid gap-4 lg:grid-cols-[1fr,280px]">
          <div class="rounded-xl bg-white p-5 shadow-sm">
            <h3 class="mb-2 text-sm font-bold text-navy">AI Readiness Radar</h3>
            <canvas #radarCanvas class="mx-auto max-h-80"></canvas>
          </div>
          <div class="space-y-4">
            <div class="rounded-xl bg-navy p-5 text-white shadow-sm">
              <p class="text-xs uppercase tracking-wide text-slate-400">Maturity Index</p>
              <p class="text-4xl font-extrabold">{{ maturity() ?? '—' }}</p>
              <p class="text-sm font-semibold text-sky">{{ band() ?? '' }}</p>
            </div>
            <div class="rounded-xl bg-white p-5 shadow-sm">
              <h4 class="mb-2 flex items-center gap-2 text-xs font-bold text-navy">
                <lucide-icon name="shield" class="h-4 w-4 text-sky"></lucide-icon>
                Red-Flag Blockers
              </h4>
              @if (redFlags().length) {
                <div class="flex flex-wrap gap-2">
                  @for (flag of redFlags(); track flag) {
                    <span class="flex items-center gap-1 rounded-full bg-rose-100 px-2.5
                                 py-1 text-[11px] font-bold text-rose-700">
                      <lucide-icon name="alert-triangle" class="h-3 w-3"></lucide-icon>
                      {{ pretty(flag) }}
                    </span>
                  }
                </div>
              } @else {
                <p class="text-xs text-emeraldok">No critical blockers 🎉</p>
              }
            </div>
          </div>
        </div>

        @if (roadmap().length) {
          <div class="rounded-xl bg-white p-5 shadow-sm">
            <h3 class="mb-3 text-sm font-bold text-navy">Prioritized Remediation Roadmap</h3>
            <ol class="space-y-2">
              @for (item of roadmap(); track item.priority) {
                <li class="flex items-start gap-3 text-sm">
                  <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full
                               text-xs font-bold text-white"
                        [class]="item.isCriticalBlocker ? 'bg-rose-600' : 'bg-sky'">
                    {{ item.priority }}</span>
                  <div>
                    <p class="font-semibold text-navy">{{ pretty(item.pillar) }}
                      <span class="font-normal text-slateink/60">(score {{ item.currentScore }})</span></p>
                    <p class="text-slateink/80">{{ item.recommendation }}</p>
                  </div>
                </li>
              }
            </ol>
          </div>
        }
      </section>
    </div>
  `
})
export class Stage2AuditComponent implements AfterViewInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly state = inject(EngagementStateService);
  private readonly toast = inject(ToastService);

  private readonly canvas = viewChild.required<ElementRef<HTMLCanvasElement>>('radarCanvas');
  private chart?: Chart;

  protected readonly pillarDefs = PILLARS;
  protected scores: Record<string, number> = {
    STRATEGY_KPI_ALIGNMENT: 3, DATA_ONTOLOGY_READINESS: 3,
    CLOUD_AGENT_ARCHITECTURE: 3, RESPONSIBLE_AI_GUARDRAILS: 3,
    TALENT_PDLC_CULTURE: 3
  };

  protected readonly running = signal(false);
  protected readonly maturity = signal<number | null>(null);
  protected readonly band = signal<string | null>(null);
  protected readonly redFlags = signal<string[]>([]);
  protected readonly roadmap = signal<Array<{
    priority: number; pillar: string; currentScore: number;
    isCriticalBlocker: boolean; recommendation: string;
  }>>([]);

  ngAfterViewInit(): void {
    const prior = this.state.getStageResult(2);
    if (prior) {
      this.render(prior);
    } else {
      this.run();
    }
  }

  ngOnDestroy(): void {
    this.chart?.destroy();
  }

  protected run(): void {
    const e = this.state.engagement();
    this.running.set(true);
    this.api.runStage('stage2/diagnostic-audit', {
      domainTrack: e?.domainTrack ?? 'SDLC',
      pillarScores: this.scores
    }).subscribe({
      next: (result) => {
        this.running.set(false);
        this.state.setStageResult(2, result);
        this.render(result);
        this.toast.success('Maturity audit recalculated');
      },
      error: () => {
        this.running.set(false);
        this.toast.error('Stage 2 computation failed');
      }
    });
  }

  private render(result: Record<string, unknown>): void {
    this.maturity.set(result['maturityIndex'] as number);
    this.band.set(result['maturityBand'] as string);
    this.redFlags.set((result['criticalRedFlags'] as string[]) ?? []);
    this.roadmap.set((result['remediationRoadmap'] as never[]) ?? []);

    const pillarScores = (result['pillarScores'] as Record<string, number>) ?? {};
    this.chart?.destroy();
    this.chart = new Chart(this.canvas().nativeElement, {
      type: 'radar',
      data: {
        labels: PILLARS.map((p) => p.label.split(' & ')),
        datasets: [{
          label: 'Readiness',
          data: PILLARS.map((p) => pillarScores[p.key] ?? 0),
          borderColor: '#0284C7',
          backgroundColor: 'rgba(2, 132, 199, 0.18)',
          pointBackgroundColor: '#0284C7'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { r: { min: 0, max: 5, ticks: { stepSize: 1 } } },
        plugins: { legend: { display: false } }
      }
    });
  }

  protected pretty(value: string): string {
    return value.replaceAll('_', ' ').toLowerCase()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
}
