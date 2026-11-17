import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';

import { ApiService } from '../../core/api.service';
import { EngagementStateService } from '../../core/engagement-state.service';
import { ToastService } from '../../core/toast.service';

interface PlanPhase {
  window: string;
  theme: string;
  actions: string[];
  targetKpis: string[];
}

interface CurriculumRole {
  roleTrack: string;
  phases: Array<{ phase: string; module: string; kpis: string[] }>;
}

const PHASE_COLORS = ['bg-slateink', 'bg-sky', 'bg-emeraldok'];

/**
 * Stage 6 — 30-60-90 Day Execution Board + Role-Based Mentoring tracker
 * (See One / Co-Build One / Lead One), with live mentoring progress from
 * the engagement record.
 */
@Component({
  selector: 'app-stage6-roadmap',
  standalone: true,
  imports: [FormsModule, LucideAngularModule],
  template: `
    <div class="space-y-6">
      <!-- Controls -->
      <div class="flex items-center gap-4 rounded-xl bg-white p-4 shadow-sm">
        <label class="flex items-center gap-2 text-xs font-semibold text-slateink">
          Maturity index
          <input type="range" min="0" max="100" step="5" [(ngModel)]="maturity"
                 class="w-40 accent-sky" />
          <span class="font-bold text-sky">{{ maturity }}</span>
        </label>
        <button (click)="run()" [disabled]="running()"
                class="flex items-center gap-2 rounded-lg bg-sky px-4 py-2 text-sm
                       font-semibold text-white transition hover:bg-sky/90
                       disabled:opacity-40">
          <lucide-icon name="play" class="h-4 w-4"></lucide-icon>
          {{ running() ? 'Planning…' : 'Run / Recalculate Stage' }}
        </button>
      </div>

      <!-- 30-60-90 board -->
      <div class="grid gap-4 lg:grid-cols-3">
        @for (phase of plan(); track phase.window; let i = $index) {
          <div class="overflow-hidden rounded-xl bg-white shadow-sm">
            <div class="p-4 text-white" [class]="phaseColors[i]">
              <p class="text-xs font-bold uppercase tracking-wide opacity-80">
                {{ phase.window }}</p>
              <p class="text-lg font-bold">{{ phase.theme }}</p>
            </div>
            <div class="space-y-3 p-4">
              <div>
                <p class="mb-1 text-[11px] font-bold uppercase text-slateink/60">Actions</p>
                <ul class="space-y-1 text-xs text-slateink">
                  @for (action of phase.actions; track action) {
                    <li class="flex gap-1.5">
                      <span class="text-sky">▸</span>{{ action }}</li>
                  }
                </ul>
              </div>
              <div>
                <p class="mb-1 text-[11px] font-bold uppercase text-slateink/60">Target KPIs</p>
                <div class="flex flex-wrap gap-1">
                  @for (kpi of phase.targetKpis; track kpi) {
                    <span class="rounded bg-emeraldok/10 px-1.5 py-0.5 text-[10px]
                                 font-semibold text-emeraldok">{{ kpi }}</span>
                  }
                </div>
              </div>
            </div>
          </div>
        } @empty {
          <p class="col-span-3 rounded-xl bg-white p-8 text-center text-sm text-slateink/60">
            Run the stage to build the 30-60-90 plan.</p>
        }
      </div>

      <!-- Mentoring curriculum + live progress -->
      <div class="rounded-xl bg-white p-5 shadow-sm">
        <h3 class="mb-4 text-sm font-bold text-navy">
          Role-Based Mentoring — See One / Co-Build One / Lead One</h3>
        <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          @for (role of curriculum(); track role.roleTrack) {
            <div class="rounded-lg border border-slate-200 p-3">
              <p class="mb-2 text-xs font-bold text-navy">{{ pretty(role.roleTrack) }}</p>
              @for (phase of role.phases; track phase.phase) {
                <div class="mb-2">
                  <p class="text-[10px] font-bold uppercase text-sky">{{ pretty(phase.phase) }}</p>
                  <p class="text-xs text-slateink">{{ phase.module }}</p>
                </div>
              }
            </div>
          }
        </div>

        @if (state.mentoring().length) {
          <h4 class="mb-2 mt-5 text-xs font-bold uppercase text-slateink/60">
            Live progress (from engagement record)</h4>
          <div class="space-y-2">
            @for (row of state.mentoring(); track row.id) {
              <div class="flex items-center gap-3 text-xs">
                <span class="w-32 shrink-0 font-semibold text-navy">{{ pretty(row.roleTrack) }}</span>
                <span class="w-56 shrink-0 truncate text-slateink">{{ row.moduleName }}
                  <span class="text-slateink/50">({{ pretty(row.phase) }})</span></span>
                <div class="h-2 flex-1 rounded-full bg-slate-200">
                  <div class="h-2 rounded-full bg-emeraldok"
                       [style.width.%]="row.completionPct"></div>
                </div>
                <span class="w-10 text-right font-bold text-navy">{{ row.completionPct }}%</span>
              </div>
            }
          </div>
        }
      </div>
    </div>
  `
})
export class Stage6RoadmapComponent implements OnInit {
  private readonly api = inject(ApiService);
  protected readonly state = inject(EngagementStateService);
  private readonly toast = inject(ToastService);

  protected readonly phaseColors = PHASE_COLORS;
  protected maturity = 50;

  protected readonly running = signal(false);
  protected readonly plan = signal<PlanPhase[]>([]);
  protected readonly curriculum = signal<CurriculumRole[]>([]);

  ngOnInit(): void {
    const prior = this.state.getStageResult(6);
    if (prior) {
      this.render(prior);
    } else {
      this.run();
    }
  }

  protected run(): void {
    this.running.set(true);
    this.api.runStage('stage6/roadmap-mentor', {
      domainTrack: this.state.engagement()?.domainTrack ?? 'SDLC',
      maturityIndex: this.maturity
    }).subscribe({
      next: (result) => {
        this.running.set(false);
        this.state.setStageResult(6, result);
        this.render(result);
        this.toast.success('30-60-90 plan regenerated');
      },
      error: () => {
        this.running.set(false);
        this.toast.error('Stage 6 computation failed');
      }
    });
  }

  private render(result: Record<string, unknown>): void {
    this.plan.set((result['plan'] as PlanPhase[]) ?? []);
    this.curriculum.set((result['mentoringCurriculum'] as CurriculumRole[]) ?? []);
  }

  protected pretty(value: string): string {
    return value.replaceAll('_', ' ').toLowerCase()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
}
