import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { catchError, of } from 'rxjs';

import { ApiService } from '../core/api.service';
import { EngagementStateService } from '../core/engagement-state.service';
import { ToastService } from '../core/toast.service';
import { STAGES } from '../core/models';
import { Stage1PitchComponent } from './stages/stage1-pitch.component';
import { Stage2AuditComponent } from './stages/stage2-audit.component';
import { Stage3BlueprintComponent } from './stages/stage3-blueprint.component';
import { Stage4DemoComponent } from './stages/stage4-demo.component';
import { Stage5StatsComponent } from './stages/stage5-stats.component';
import { Stage6RoadmapComponent } from './stages/stage6-roadmap.component';

/**
 * 6-Stage Interactive Lifecycle workspace:
 * horizontal stepper (free jumping), stage panels, and the on-demand
 * Artifact Studio (Download PPTX / DOCX with toast feedback).
 */
@Component({
  selector: 'app-lifecycle',
  standalone: true,
  imports: [
    LucideAngularModule,
    Stage1PitchComponent, Stage2AuditComponent, Stage3BlueprintComponent,
    Stage4DemoComponent, Stage5StatsComponent, Stage6RoadmapComponent
  ],
  template: `
    @if (state.engagement(); as e) {
      <!-- Header + artifact studio -->
      <header class="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <button class="mb-1 text-xs font-medium text-sky hover:underline"
                  (click)="back()">← Portfolio</button>
          <h1 class="text-2xl font-bold text-navy">{{ e.clientName }}</h1>
          <p class="text-sm text-slateink/70">
            {{ e.industry }} • {{ e.domainTrack }} track •
            currently at Stage {{ e.currentStage }} ({{ e.currentStageName }})
          </p>
        </div>

        <!-- Artifact Studio -->
        <div class="flex items-center gap-2">
          <button (click)="download('pptx')" [disabled]="downloading()"
                  class="flex items-center gap-2 rounded-lg bg-navy px-4 py-2.5 text-sm
                         font-semibold text-white transition hover:bg-navy/90
                         disabled:opacity-40">
            <lucide-icon name="download" class="h-4 w-4"></lucide-icon>
            Executive PPTX
          </button>
          <button (click)="download('docx')" [disabled]="downloading()"
                  class="flex items-center gap-2 rounded-lg border-2 border-navy px-4 py-2
                         text-sm font-semibold text-navy transition hover:bg-navy/5
                         disabled:opacity-40">
            <lucide-icon name="file-text" class="h-4 w-4"></lucide-icon>
            Word Report
          </button>
        </div>
      </header>

      <!-- Horizontal stepper (free jumping) -->
      <nav class="mb-6 overflow-x-auto">
        <ol class="flex min-w-max items-center gap-0">
          @for (stage of stages; track stage.num; let last = $last) {
            <li class="flex items-center">
              <button (click)="state.activeStage.set(stage.num)"
                      class="group flex flex-col items-center px-3 py-1 transition">
                <span class="flex h-9 w-9 items-center justify-center rounded-full border-2
                             text-sm font-bold transition"
                      [class]="state.activeStage() === stage.num
                               ? 'border-sky bg-sky text-white'
                               : stage.num <= e.currentStage
                                 ? 'border-emeraldok bg-emeraldok/10 text-emeraldok'
                                 : 'border-slate-300 bg-white text-slateink/60 group-hover:border-sky'">
                  {{ stage.num }}
                </span>
                <span class="mt-1 text-[11px] font-semibold"
                      [class]="state.activeStage() === stage.num ? 'text-sky' : 'text-slateink/60'">
                  {{ stage.short }}
                </span>
              </button>
              @if (!last) {
                <div class="h-0.5 w-10 rounded"
                     [class]="stage.num < e.currentStage ? 'bg-emeraldok' : 'bg-slate-300'"></div>
              }
            </li>
          }
        </ol>
      </nav>

      <!-- Active stage panel -->
      @switch (state.activeStage()) {
        @case (1) { <app-stage1-pitch /> }
        @case (2) { <app-stage2-audit /> }
        @case (3) { <app-stage3-blueprint /> }
        @case (4) { <app-stage4-demo /> }
        @case (5) { <app-stage5-stats /> }
        @case (6) { <app-stage6-roadmap /> }
      }
    } @else {
      <p class="rounded-xl bg-white p-8 text-center text-sm text-slateink/60">
        Loading engagement…
      </p>
    }
  `
})
export class LifecycleComponent implements OnInit, OnDestroy {
  protected readonly state = inject(EngagementStateService);
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);

  protected readonly stages = STAGES;
  protected readonly downloading = signal(false);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.api.getEngagement(id).subscribe({
      next: (engagement) => {
        this.state.setEngagement(engagement);
        this.api.listGates(id).pipe(catchError(() => of([])))
          .subscribe((g) => this.state.gates.set(g));
        this.api.listMentoring(id).pipe(catchError(() => of([])))
          .subscribe((m) => this.state.mentoring.set(m));
      },
      error: () => {
        this.toast.error('Engagement not found');
        this.router.navigate(['/']);
      }
    });
  }

  ngOnDestroy(): void {
    this.state.reset();
  }

  protected back(): void {
    this.router.navigate(['/']);
  }

  /** Artifact Studio: render + instant download of the active stage result. */
  protected download(format: 'pptx' | 'docx'): void {
    const stage = this.state.activeStage();
    const result = this.state.getStageResult(stage) ?? {};
    if (!Object.keys(result).length) {
      this.toast.info('Run the stage first for a fully populated deliverable — generating with defaults.');
    }
    this.downloading.set(true);
    this.api.renderDocument(stage, format, this.state.engagementData(), result)
      .subscribe({
        next: (blob) => {
          this.downloading.set(false);
          const url = URL.createObjectURL(blob);
          const anchor = document.createElement('a');
          anchor.href = url;
          anchor.download = `stage${stage}-${this.slug()}.${format}`;
          anchor.click();
          URL.revokeObjectURL(url);
          this.toast.success(`Stage ${stage} ${format.toUpperCase()} downloaded`);
        },
        error: () => {
          this.downloading.set(false);
          this.toast.error('Document generation failed — is ai-engine up?');
        }
      });
  }

  private slug(): string {
    return (this.state.engagement()?.clientName ?? 'client')
      .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }
}
