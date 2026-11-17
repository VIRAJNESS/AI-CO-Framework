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
 * Stage 5 — Statistical Significance & CFO TCO Dashboard: A/B inputs +
 * economics inputs → CI bar, Kappa/PSI gauges, NEV waterfall.
 */
@Component({
  selector: 'app-stage5-stats',
  standalone: true,
  imports: [FormsModule, LucideAngularModule],
  template: `
    <div class="grid gap-6 xl:grid-cols-[340px,1fr]">
      <!-- Left: A/B + economics inputs -->
      <aside class="space-y-4 rounded-xl bg-white p-5 shadow-sm">
        <h3 class="text-sm font-bold text-navy">A/B Shadow-Mode Samples</h3>
        <div>
          <label class="text-xs font-semibold text-slateink">Control (comma-separated)</label>
          <input [(ngModel)]="controlCsv"
                 class="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono
                        text-xs focus:border-sky focus:outline-none" />
        </div>
        <div>
          <label class="text-xs font-semibold text-slateink">Treatment (comma-separated)</label>
          <input [(ngModel)]="treatmentCsv"
                 class="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono
                        text-xs focus:border-sky focus:outline-none" />
        </div>

        <h3 class="pt-2 text-sm font-bold text-navy">CFO Economics ($/yr)</h3>
        <div class="grid grid-cols-2 gap-2">
          <label class="text-xs font-semibold text-slateink">Gross savings
            <input type="number" [(ngModel)]="grossSavings"
                   class="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5
                          text-xs focus:border-sky focus:outline-none" /></label>
          <label class="text-xs font-semibold text-slateink">Inference cost
            <input type="number" [(ngModel)]="inferenceCost"
                   class="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5
                          text-xs focus:border-sky focus:outline-none" /></label>
          <label class="text-xs font-semibold text-slateink">Orchestration
            <input type="number" [(ngModel)]="orchestrationCost"
                   class="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5
                          text-xs focus:border-sky focus:outline-none" /></label>
          <label class="text-xs font-semibold text-slateink">Governance
            <input type="number" [(ngModel)]="governanceCost"
                   class="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5
                          text-xs focus:border-sky focus:outline-none" /></label>
        </div>

        <button (click)="run()" [disabled]="running()"
                class="flex w-full items-center justify-center gap-2 rounded-lg bg-sky
                       py-2.5 text-sm font-semibold text-white transition
                       hover:bg-sky/90 disabled:opacity-40">
          <lucide-icon name="play" class="h-4 w-4"></lucide-icon>
          {{ running() ? 'Analyzing…' : 'Run / Recalculate Stage' }}
        </button>
      </aside>

      <!-- Center: evidence dashboard -->
      <section class="space-y-4">
        <!-- Significance banner + gauges -->
        <div class="grid gap-4 md:grid-cols-3">
          <div class="rounded-xl p-5 text-white shadow-sm"
               [class]="significant() ? 'bg-emeraldok' : 'bg-slateink'">
            <p class="text-xs uppercase tracking-wide opacity-80">Welch p-value</p>
            <p class="text-3xl font-extrabold">{{ pValue() ?? '—' }}</p>
            <p class="text-xs font-semibold">
              {{ significant() === null ? '' : significant()
                 ? 'Statistically significant (p < 0.05)' : 'Not significant' }}</p>
          </div>
          <div class="rounded-xl bg-white p-5 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-wide text-slateink/60">
              Cohen's Kappa (Judge vs SME)</p>
            <p class="text-3xl font-extrabold text-navy">{{ kappa() ?? '—' }}</p>
            <div class="mt-2 h-2 rounded-full bg-slate-200">
              <div class="h-2 rounded-full bg-sky" [style.width.%]="(kappa() ?? 0) * 100"></div>
            </div>
          </div>
          <div class="rounded-xl bg-white p-5 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-wide text-slateink/60">
              PSI Drift</p>
            <p class="text-3xl font-extrabold"
               [class]="(psi() ?? 0) < 0.1 ? 'text-emeraldok'
                        : (psi() ?? 0) < 0.25 ? 'text-amber-600' : 'text-rose-600'">
              {{ psi() ?? '—' }}</p>
            <p class="text-xs text-slateink/60">{{ psiBand() }}</p>
          </div>
        </div>

        <div class="grid gap-4 lg:grid-cols-2">
          <!-- Confidence interval bar -->
          <div class="rounded-xl bg-white p-5 shadow-sm">
            <h3 class="mb-2 text-sm font-bold text-navy">95% Confidence Interval of Lift</h3>
            <canvas #ciCanvas class="max-h-56"></canvas>
          </div>
          <!-- NEV waterfall -->
          <div class="rounded-xl bg-white p-5 shadow-sm">
            <h3 class="mb-2 text-sm font-bold text-navy">Net Economic Value Waterfall</h3>
            <canvas #nevCanvas class="max-h-56"></canvas>
          </div>
        </div>
      </section>
    </div>
  `
})
export class Stage5StatsComponent implements AfterViewInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly state = inject(EngagementStateService);
  private readonly toast = inject(ToastService);

  private readonly ciCanvas = viewChild.required<ElementRef<HTMLCanvasElement>>('ciCanvas');
  private readonly nevCanvas = viewChild.required<ElementRef<HTMLCanvasElement>>('nevCanvas');
  private ciChart?: Chart;
  private nevChart?: Chart;

  protected controlCsv = '42, 41.5, 43, 42.2, 41.8, 42.6';
  protected treatmentCsv = '13.4, 13.1, 13.8, 13.3, 13.6, 13.2';
  protected grossSavings = 1_000_000;
  protected inferenceCost = 120_000;
  protected orchestrationCost = 80_000;
  protected governanceCost = 50_000;

  protected readonly running = signal(false);
  protected readonly pValue = signal<number | null>(null);
  protected readonly significant = signal<boolean | null>(null);
  protected readonly kappa = signal<number | null>(null);
  protected readonly psi = signal<number | null>(null);
  protected readonly psiBand = signal<string>('');

  ngAfterViewInit(): void {
    const prior = this.state.getStageResult(5);
    if (prior) {
      this.render(prior);
    } else {
      this.run();
    }
  }

  ngOnDestroy(): void {
    this.ciChart?.destroy();
    this.nevChart?.destroy();
  }

  private parseCsv(csv: string): number[] {
    return csv.split(',').map((s) => parseFloat(s.trim())).filter((n) => !isNaN(n));
  }

  protected run(): void {
    const control = this.parseCsv(this.controlCsv);
    const treatment = this.parseCsv(this.treatmentCsv);
    if (control.length < 2 || treatment.length < 2) {
      this.toast.error('Each A/B sample needs at least 2 numeric values');
      return;
    }
    this.running.set(true);
    // Demo-stable judge labels + drift series accompany the editable inputs.
    this.api.runStage('stage5/statistical-roi', {
      abTest: { control, treatment },
      judgeAgreement: {
        llmLabels: Array(46).fill('resolve').concat(Array(4).fill('escalate'),
          Array(3).fill('resolve'), Array(47).fill('escalate')).slice(0, 100),
        humanLabels: Array(50).fill('resolve').concat(Array(50).fill('escalate'))
      },
      drift: {
        baseline: Array.from({ length: 60 }, (_, i) => (i % 10) + 1),
        current: Array.from({ length: 60 }, (_, i) => (i % 10) + 1.5)
      },
      economics: {
        annualGrossSavings: this.grossSavings,
        annualInferenceCost: this.inferenceCost,
        annualOrchestrationCost: this.orchestrationCost,
        annualGovernanceCost: this.governanceCost
      }
    }).subscribe({
      next: (result) => {
        this.running.set(false);
        this.state.setStageResult(5, result);
        this.render(result);
        this.toast.success('Statistical evidence recalculated');
      },
      error: () => {
        this.running.set(false);
        this.toast.error('Stage 5 computation failed');
      }
    });
  }

  private render(result: Record<string, unknown>): void {
    const ab = result['abTest'] as any;
    const judge = result['judgeAgreement'] as any;
    const drift = result['drift'] as any;
    const econ = result['economics'] as any;

    this.pValue.set(ab ? Number(ab.welchT.pValue.toPrecision(3)) : null);
    this.significant.set(ab ? ab.significantAt005 : null);
    this.kappa.set(judge ? judge.cohensKappa : null);
    this.psi.set(drift ? drift.psi : null);
    this.psiBand.set(drift ? drift.alertLevel : '');

    // --- CI bar -----------------------------------------------------------
    if (ab) {
      this.ciChart?.destroy();
      this.ciChart = new Chart(this.ciCanvas().nativeElement, {
        type: 'bar',
        data: {
          labels: ['CI low', 'Observed lift', 'CI high'],
          datasets: [{
            data: [ab.ci95.low, ab.meanDifference, ab.ci95.high],
            backgroundColor: ['#94A3B8', '#0284C7', '#94A3B8']
          }]
        },
        options: {
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } }
        }
      });
    }

    // --- NEV waterfall (bar with signed values) -----------------------------
    if (econ) {
      this.nevChart?.destroy();
      this.nevChart = new Chart(this.nevCanvas().nativeElement, {
        type: 'bar',
        data: {
          labels: ['Gross savings', 'Inference', 'Orchestration', 'Governance', 'Net value'],
          datasets: [{
            data: [
              econ.annualGrossSavings,
              -this.inferenceCost, -this.orchestrationCost, -this.governanceCost,
              econ.netEconomicValue
            ],
            backgroundColor: ['#059669', '#E11D48', '#E11D48', '#E11D48', '#0284C7']
          }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { ticks: { callback: (v) => '$' + Number(v).toLocaleString() } } }
        }
      });
    }
  }
}
