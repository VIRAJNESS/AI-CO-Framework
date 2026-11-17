import { DecimalPipe } from '@angular/common';
import {
  AfterViewInit, Component, ElementRef, OnDestroy, inject, signal, viewChild
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Chart } from 'chart.js';

import { ApiService } from '../../core/api.service';
import { EngagementStateService } from '../../core/engagement-state.service';
import { ToastService } from '../../core/toast.service';

/**
 * Stage 1 — Pitch Simulator: inputs on the left, interactive
 * Copilot vs Autonomous Agent cumulative ROI curve in the center.
 */
@Component({
  selector: 'app-stage1-pitch',
  standalone: true,
  imports: [DecimalPipe, FormsModule, LucideAngularModule],
  template: `
    <div class="grid gap-6 xl:grid-cols-[320px,1fr]">
      <!-- Left: dynamic input form -->
      <aside class="space-y-4 rounded-xl bg-white p-5 shadow-sm">
        <h3 class="text-sm font-bold text-navy">Pitch Inputs</h3>

        <div>
          <label class="text-xs font-semibold text-slateink">Engineering headcount
            <span class="float-right text-sky">{{ headcount }}</span></label>
          <input type="range" min="10" max="2000" step="10" [(ngModel)]="headcount"
                 class="w-full accent-sky" />
        </div>
        <div>
          <label class="text-xs font-semibold text-slateink">Monthly ticket volume
            <span class="float-right text-sky">{{ tickets | number }}</span></label>
          <input type="range" min="0" max="300000" step="1000" [(ngModel)]="tickets"
                 class="w-full accent-sky" />
        </div>
        <div>
          <label class="text-xs font-semibold text-slateink">Monthly cloud spend ($)
            <span class="float-right text-sky">{{ cloudSpend | number }}</span></label>
          <input type="range" min="0" max="2000000" step="10000" [(ngModel)]="cloudSpend"
                 class="w-full accent-sky" />
        </div>

        <button (click)="run()" [disabled]="running()"
                class="flex w-full items-center justify-center gap-2 rounded-lg bg-sky
                       py-2.5 text-sm font-semibold text-white transition
                       hover:bg-sky/90 disabled:opacity-40">
          <lucide-icon name="play" class="h-4 w-4"></lucide-icon>
          {{ running() ? 'Computing…' : 'Run / Recalculate Stage' }}
        </button>
      </aside>

      <!-- Center: ROI curve + pillars -->
      <section class="space-y-4">
        <div class="rounded-xl bg-white p-5 shadow-sm">
          <h3 class="mb-3 text-sm font-bold text-navy">
            Copilot vs Autonomous Agent — 12-Month Cumulative Net Value</h3>
          <canvas #roiCanvas class="max-h-80 w-full"></canvas>
        </div>

        @if (pillars(); as fp) {
          <div class="grid gap-3 md:grid-cols-2">
            @for (pillar of pillarKeys; track pillar) {
              <div class="rounded-xl bg-white p-4 shadow-sm">
                <p class="text-xs font-bold uppercase tracking-wide text-sky">{{ pillar }}</p>
                <p class="mt-1 text-sm text-slateink">{{ fp[pillar] }}</p>
              </div>
            }
          </div>
        }
      </section>
    </div>
  `
})
export class Stage1PitchComponent implements AfterViewInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly state = inject(EngagementStateService);
  private readonly toast = inject(ToastService);

  private readonly canvas = viewChild.required<ElementRef<HTMLCanvasElement>>('roiCanvas');
  private chart?: Chart;

  protected headcount = 100;
  protected tickets = 5000;
  protected cloudSpend = 50000;
  protected readonly running = signal(false);
  protected readonly pillars = signal<Record<string, string> | null>(null);
  protected readonly pillarKeys = ['vision', 'trust', 'depth', 'solving'];

  ngAfterViewInit(): void {
    const prior = this.state.getStageResult(1);
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
    this.api.runStage('stage1/pitch-simulator', {
      industry: e?.industry ?? 'Technology',
      domainTrack: e?.domainTrack ?? 'SDLC',
      engineeringHeadcount: this.headcount,
      monthlyTicketVolume: this.tickets,
      currentCloudSpend: this.cloudSpend
    }).subscribe({
      next: (result) => {
        this.running.set(false);
        this.state.setStageResult(1, result);
        this.render(result);
        this.toast.success('Pitch economics recalculated');
      },
      error: () => {
        this.running.set(false);
        this.toast.error('Stage 1 computation failed');
      }
    });
  }

  /** Draw the cumulative 12-month curves from the engine result. */
  private render(result: Record<string, unknown>): void {
    const copilot = (result['traditionalCopilots'] as any)?.annualNetValue?.mid ?? 0;
    const agentic = (result['agenticWorkflows'] as any)?.annualNetValue?.mid ?? 0;
    this.pillars.set((result['fourPillars'] as Record<string, string>) ?? null);

    const months = Array.from({ length: 12 }, (_, i) => i + 1);
    // Agentic ramps with an S-curve (matches the doc_factory chart model).
    const ramp = months.map((m) => 1 / (1 + Math.exp(-(m - 4) / 1.6)));
    const rampMax = ramp[ramp.length - 1];

    this.chart?.destroy();
    this.chart = new Chart(this.canvas().nativeElement, {
      type: 'line',
      data: {
        labels: months.map((m) => `M${m}`),
        datasets: [
          {
            label: 'Traditional Copilots',
            data: months.map((m) => Math.round(copilot * m / 12)),
            borderColor: '#334155',
            backgroundColor: 'transparent',
            tension: 0.3
          },
          {
            label: 'Agentic Workflows',
            data: months.map((m, i) => Math.round(agentic * (ramp[i] / rampMax) * m / 12)),
            borderColor: '#0284C7',
            backgroundColor: 'rgba(2, 132, 199, 0.12)',
            fill: '-1',
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
        scales: { y: { ticks: { callback: (v) => '$' + Number(v).toLocaleString() } } }
      }
    });
  }
}
