import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';

import { ApiService } from '../../core/api.service';
import { EngagementStateService } from '../../core/engagement-state.service';
import { ToastService } from '../../core/toast.service';
import { DomainTrack } from '../../core/models';

interface BlueprintComponentModel {
  name: string;
  purpose: string;
  agents: string[];
  integrations: string[];
  kpis: string[];
}

/**
 * Stage 3 — Domain Execution Blueprint: track selector on the left,
 * interactive architecture flow (component cards chained with arrows) center.
 */
@Component({
  selector: 'app-stage3-blueprint',
  standalone: true,
  imports: [FormsModule, LucideAngularModule],
  template: `
    <div class="grid gap-6 xl:grid-cols-[300px,1fr]">
      <!-- Left: track selector -->
      <aside class="space-y-4 rounded-xl bg-white p-5 shadow-sm">
        <h3 class="text-sm font-bold text-navy">Execution Track</h3>
        <div class="grid grid-cols-2 gap-2">
          @for (track of tracks; track track) {
            <button (click)="selectedTrack = track"
                    class="rounded-lg border px-3 py-3 text-xs font-bold transition"
                    [class]="selectedTrack === track
                             ? 'border-sky bg-sky/10 text-sky'
                             : 'border-slate-300 text-slateink hover:border-sky/50'">
              {{ track }}
            </button>
          }
        </div>
        <button (click)="run()" [disabled]="running()"
                class="flex w-full items-center justify-center gap-2 rounded-lg bg-sky
                       py-2.5 text-sm font-semibold text-white transition
                       hover:bg-sky/90 disabled:opacity-40">
          <lucide-icon name="play" class="h-4 w-4"></lucide-icon>
          {{ running() ? 'Generating…' : 'Run / Recalculate Stage' }}
        </button>
        @if (theme()) {
          <div class="rounded-lg bg-navy p-3 text-xs text-white">
            <p class="font-bold text-sky">Blueprint theme</p>
            <p class="mt-1">{{ theme() }}</p>
          </div>
        }
      </aside>

      <!-- Center: architecture flow -->
      <section class="space-y-4">
        <div class="rounded-xl bg-white p-5 shadow-sm">
          <h3 class="mb-4 flex items-center gap-2 text-sm font-bold text-navy">
            <lucide-icon name="workflow" class="h-4 w-4 text-sky"></lucide-icon>
            Domain Execution Architecture Flow
          </h3>
          @if (components().length) {
            <div class="flex flex-col gap-2 lg:flex-row lg:items-stretch">
              @for (comp of components(); track comp.name; let last = $last) {
                <div class="flex flex-1 flex-col rounded-xl border-2 border-sky/30
                            bg-slate-50 p-4">
                  <h4 class="text-sm font-bold text-navy">{{ comp.name }}</h4>
                  <p class="mt-1 flex-1 text-xs text-slateink/80">{{ comp.purpose }}</p>
                  <div class="mt-3 space-y-1.5">
                    <div class="flex flex-wrap gap-1">
                      @for (agent of comp.agents; track agent) {
                        <span class="rounded bg-sky/15 px-1.5 py-0.5 text-[10px]
                                     font-bold text-sky">⚙ {{ agent }}</span>
                      }
                    </div>
                    <p class="text-[10px] text-slateink/60">
                      <strong>KPIs:</strong> {{ comp.kpis.join(', ') }}</p>
                  </div>
                </div>
                @if (!last) {
                  <div class="flex items-center justify-center text-sky">
                    <lucide-icon name="arrow-right" class="hidden h-5 w-5 lg:block"></lucide-icon>
                  </div>
                }
              }
            </div>
          } @else {
            <p class="py-8 text-center text-sm text-slateink/60">
              Run the stage to generate the architecture.</p>
          }
        </div>

        @if (foundations().length) {
          <div class="rounded-xl bg-white p-5 shadow-sm">
            <h3 class="mb-2 text-sm font-bold text-navy">Shared Foundations</h3>
            <ul class="grid gap-1 text-sm text-slateink md:grid-cols-2">
              @for (item of foundations(); track item) {
                <li class="flex items-center gap-2">
                  <lucide-icon name="check-circle" class="h-4 w-4 text-emeraldok"></lucide-icon>
                  {{ item }}
                </li>
              }
            </ul>
          </div>
        }
      </section>
    </div>
  `
})
export class Stage3BlueprintComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly state = inject(EngagementStateService);
  private readonly toast = inject(ToastService);

  protected readonly tracks: DomainTrack[] = ['SDLC', 'PDLC', 'STARTUP', 'LEGACY'];
  protected selectedTrack: DomainTrack = 'SDLC';

  protected readonly running = signal(false);
  protected readonly theme = signal<string | null>(null);
  protected readonly components = signal<BlueprintComponentModel[]>([]);
  protected readonly foundations = signal<string[]>([]);

  ngOnInit(): void {
    this.selectedTrack = this.state.engagement()?.domainTrack ?? 'SDLC';
    const prior = this.state.getStageResult(3);
    if (prior) {
      this.render(prior);
    } else {
      this.run();
    }
  }

  protected run(): void {
    this.running.set(true);
    this.api.runStage('stage3/domain-blueprint', {
      domainTrack: this.selectedTrack,
      clientName: this.state.engagement()?.clientName ?? ''
    }).subscribe({
      next: (result) => {
        this.running.set(false);
        this.state.setStageResult(3, result);
        this.render(result);
        this.toast.success(`${this.selectedTrack} blueprint generated`);
      },
      error: () => {
        this.running.set(false);
        this.toast.error('Stage 3 computation failed');
      }
    });
  }

  private render(result: Record<string, unknown>): void {
    this.theme.set(result['theme'] as string);
    this.components.set((result['components'] as BlueprintComponentModel[]) ?? []);
    this.foundations.set((result['sharedFoundations'] as string[]) ?? []);
  }
}
