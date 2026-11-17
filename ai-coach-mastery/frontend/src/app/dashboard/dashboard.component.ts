import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { catchError, forkJoin, of } from 'rxjs';

import { ApiService } from '../core/api.service';
import { ToastService } from '../core/toast.service';
import {
  AdvisorTier,
  DomainTrack,
  Engagement,
  GovernanceGate,
  MentoringProgress
} from '../core/models';

/** Per-client headline metrics used on showcase cards + KPI aggregation. */
const SHOWCASE_METRICS: Record<string, { toilReductionPct: number; netRoiUsd: number; headline: string }> = {
  'NovaTel Global Telecom': {
    toilReductionPct: 68, netRoiUsd: 11_200_000,
    headline: '31% ticket deflection • 85% faster deploys • p < 0.001'
  },
  'FinPulse Digital Banking': {
    toilReductionPct: 34, netRoiUsd: 2_400_000,
    headline: 'Checkout drop-off 46% → 18% in live PoC'
  },
  'VeloceAI Series-B SaaS': {
    toilReductionPct: 22, netRoiUsd: 310_000,
    headline: '-54% inference unit cost blueprint ready'
  },
  'OmniCare Core Insurance': {
    toilReductionPct: 0, netRoiUsd: 0,
    headline: 'Data/Ontology 2.0/5 red flag — strangler-fig path set'
  }
};

const TRACK_BADGE: Record<DomainTrack, string> = {
  SDLC: 'bg-sky/15 text-sky',
  PDLC: 'bg-violet-100 text-violet-700',
  STARTUP: 'bg-amber-100 text-amber-700',
  LEGACY: 'bg-rose-100 text-rose-700'
};

/**
 * Executive Portfolio Dashboard: showcase client cards, aggregate KPI strip,
 * and the New Client Engagement wizard modal.
 */
@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [FormsModule, LucideAngularModule],
  template: `
    <header class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-navy">Client Portfolio</h1>
        <p class="text-sm text-slateink/70">AI Head Coach engagements across all delivery tracks</p>
      </div>
      <button (click)="wizardOpen.set(true)"
              class="flex items-center gap-2 rounded-lg bg-sky px-4 py-2.5 text-sm
                     font-semibold text-white shadow transition hover:bg-sky/90">
        <lucide-icon name="plus" class="h-4 w-4"></lucide-icon>
        New Client Engagement
      </button>
    </header>

    <!-- KPI strip -->
    <section class="mb-8 grid grid-cols-2 gap-4 xl:grid-cols-4">
      <div class="rounded-xl bg-white p-4 shadow-sm">
        <p class="text-xs font-medium uppercase tracking-wide text-slateink/60">Avg Toil Reduction</p>
        <p class="mt-1 text-2xl font-bold text-navy">{{ avgToil() }}%</p>
      </div>
      <div class="rounded-xl bg-white p-4 shadow-sm">
        <p class="text-xs font-medium uppercase tracking-wide text-slateink/60">Projected Net ROI</p>
        <p class="mt-1 text-2xl font-bold text-emeraldok">\${{ totalRoiM() }}M</p>
      </div>
      <div class="rounded-xl bg-white p-4 shadow-sm">
        <p class="text-xs font-medium uppercase tracking-wide text-slateink/60">Active Governance Gates</p>
        <p class="mt-1 text-2xl font-bold text-navy">{{ gateCount() }}
          @if (failingGates() > 0) {
            <span class="ml-1 align-middle text-sm font-semibold text-rose-600">
              ({{ failingGates() }} FAIL)</span>
          }
        </p>
      </div>
      <div class="rounded-xl bg-white p-4 shadow-sm">
        <p class="text-xs font-medium uppercase tracking-wide text-slateink/60">Mentoring Completion</p>
        <p class="mt-1 text-2xl font-bold text-navy">{{ mentoringAvg() }}%</p>
      </div>
    </section>

    <!-- Client cards -->
    <section class="grid gap-5 md:grid-cols-2">
      @for (e of engagements(); track e.id) {
        <button (click)="open(e)"
                class="group rounded-xl bg-white p-5 text-left shadow-sm transition
                       hover:shadow-md hover:ring-2 hover:ring-sky/40">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="text-lg font-bold text-navy group-hover:text-sky">{{ e.clientName }}</h3>
              <p class="text-xs text-slateink/60">{{ e.industry }} • {{ tierLabel(e.advisorTier) }}</p>
            </div>
            <span class="rounded-full px-2.5 py-1 text-[11px] font-bold"
                  [class]="trackBadge(e.domainTrack)">{{ e.domainTrack }}</span>
          </div>
          <p class="mt-3 text-sm text-slateink">{{ headline(e.clientName) }}</p>
          <div class="mt-4">
            <div class="mb-1 flex justify-between text-[11px] font-medium text-slateink/60">
              <span>Stage {{ e.currentStage }} of 6 — {{ e.currentStageName }}</span>
              <span class="flex items-center gap-1 text-sky">
                Open workspace <lucide-icon name="arrow-right" class="h-3 w-3"></lucide-icon>
              </span>
            </div>
            <div class="h-1.5 w-full rounded-full bg-slate-200">
              <div class="h-1.5 rounded-full bg-sky transition-all"
                   [style.width.%]="(e.currentStage / 6) * 100"></div>
            </div>
          </div>
        </button>
      } @empty {
        <p class="col-span-2 rounded-xl bg-white p-8 text-center text-sm text-slateink/60">
          No engagements yet — the showcase seeds on first core-api startup,
          or create one with the wizard.
        </p>
      }
    </section>

    <!-- New Client Engagement Wizard -->
    @if (wizardOpen()) {
      <div class="fixed inset-0 z-40 flex items-center justify-center bg-navy/60 p-4"
           (click)="wizardOpen.set(false)">
        <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl"
             (click)="$event.stopPropagation()">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="flex items-center gap-2 text-lg font-bold text-navy">
              <lucide-icon name="sparkles" class="h-5 w-5 text-sky"></lucide-icon>
              New Client Engagement
            </h2>
            <button class="text-slateink/60 hover:text-navy" (click)="wizardOpen.set(false)">
              <lucide-icon name="x" class="h-5 w-5"></lucide-icon>
            </button>
          </div>

          <div class="space-y-4">
            <div>
              <label class="mb-1 block text-xs font-semibold text-slateink">Client name</label>
              <input [(ngModel)]="wiz.clientName" placeholder="Acme Industries"
                     class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm
                            focus:border-sky focus:outline-none" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-semibold text-slateink">Industry</label>
              <input [(ngModel)]="wiz.industry" placeholder="Manufacturing"
                     class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm
                            focus:border-sky focus:outline-none" />
            </div>
            <div>
              <label class="mb-1 block text-xs font-semibold text-slateink">Domain track</label>
              <div class="grid grid-cols-4 gap-2">
                @for (track of tracks; track track) {
                  <button (click)="wiz.domainTrack = track"
                          class="rounded-lg border px-2 py-2 text-xs font-bold transition"
                          [class]="wiz.domainTrack === track
                                   ? 'border-sky bg-sky/10 text-sky'
                                   : 'border-slate-300 text-slateink hover:border-sky/50'">
                    {{ track }}
                  </button>
                }
              </div>
            </div>
            <div>
              <label class="mb-1 block text-xs font-semibold text-slateink">Advisory tier</label>
              <select [(ngModel)]="wiz.advisorTier"
                      class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm
                             focus:border-sky focus:outline-none">
                <option value="DIAGNOSTIC_SPRINT">Diagnostic Sprint</option>
                <option value="TRANSFORMATION_RETAINER">Transformation Retainer</option>
                <option value="FRACTIONAL_HEAD_COACH">Fractional Head Coach</option>
              </select>
            </div>
          </div>

          <button (click)="createEngagement()"
                  [disabled]="!wiz.clientName.trim() || !wiz.industry.trim() || creating()"
                  class="mt-6 w-full rounded-lg bg-navy py-2.5 text-sm font-semibold text-white
                         transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-40">
            {{ creating() ? 'Creating…' : 'Create & open workspace' }}
          </button>
        </div>
      </div>
    }
  `
})
export class DashboardComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);

  protected readonly engagements = signal<Engagement[]>([]);
  protected readonly wizardOpen = signal(false);
  protected readonly creating = signal(false);

  private readonly allGates = signal<GovernanceGate[]>([]);
  private readonly allMentoring = signal<MentoringProgress[]>([]);

  protected readonly tracks: DomainTrack[] = ['SDLC', 'PDLC', 'STARTUP', 'LEGACY'];

  protected wiz: {
    clientName: string; industry: string;
    domainTrack: DomainTrack; advisorTier: AdvisorTier;
  } = { clientName: '', industry: '', domainTrack: 'SDLC', advisorTier: 'DIAGNOSTIC_SPRINT' };

  // --- KPI aggregates (signals-derived) --------------------------------------

  protected readonly avgToil = computed(() => {
    const vals = this.engagements()
      .map((e) => SHOWCASE_METRICS[e.clientName]?.toilReductionPct)
      .filter((v): v is number => v !== undefined && v > 0);
    return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
  });

  protected readonly totalRoiM = computed(() => {
    const total = this.engagements()
      .reduce((sum, e) => sum + (SHOWCASE_METRICS[e.clientName]?.netRoiUsd ?? 0), 0);
    return (total / 1_000_000).toFixed(1);
  });

  protected readonly gateCount = computed(() => this.allGates().length);
  protected readonly failingGates = computed(
    () => this.allGates().filter((g) => g.status === 'FAIL').length);

  protected readonly mentoringAvg = computed(() => {
    const rows = this.allMentoring();
    return rows.length
      ? Math.round(rows.reduce((a, m) => a + m.completionPct, 0) / rows.length)
      : 0;
  });

  ngOnInit(): void {
    this.api.listEngagements()
      .pipe(catchError(() => of([] as Engagement[])))
      .subscribe((list) => {
        this.engagements.set(list);
        this.loadAggregates(list);
      });
  }

  /** Fan-out gates + mentoring for the KPI strip. */
  private loadAggregates(list: Engagement[]): void {
    if (!list.length) return;
    forkJoin(list.map((e) =>
      this.api.listGates(e.id).pipe(catchError(() => of([] as GovernanceGate[])))))
      .subscribe((all) => this.allGates.set(all.flat()));
    forkJoin(list.map((e) =>
      this.api.listMentoring(e.id).pipe(catchError(() => of([] as MentoringProgress[])))))
      .subscribe((all) => this.allMentoring.set(all.flat()));
  }

  protected open(e: Engagement): void {
    this.router.navigate(['/engagements', e.id]);
  }

  protected createEngagement(): void {
    this.creating.set(true);
    this.api.createEngagement({
      clientName: this.wiz.clientName.trim(),
      industry: this.wiz.industry.trim(),
      domainTrack: this.wiz.domainTrack,
      advisorTier: this.wiz.advisorTier
    }).subscribe({
      next: (created) => {
        this.creating.set(false);
        this.wizardOpen.set(false);
        this.toast.success(`Engagement created for ${created.clientName}`);
        this.router.navigate(['/engagements', created.id]);
      },
      error: () => {
        this.creating.set(false);
        this.toast.error('Could not create engagement — is core-api up?');
      }
    });
  }

  protected headline(client: string): string {
    return SHOWCASE_METRICS[client]?.headline ?? 'Engagement in progress';
  }

  protected trackBadge(track: DomainTrack): string {
    return TRACK_BADGE[track];
  }

  protected tierLabel(tier: AdvisorTier): string {
    return tier.replaceAll('_', ' ').toLowerCase()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
}
