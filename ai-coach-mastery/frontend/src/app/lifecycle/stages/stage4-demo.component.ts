import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';

import { ApiService } from '../../core/api.service';
import { EngagementStateService } from '../../core/engagement-state.service';
import { ToastService } from '../../core/toast.service';

interface TraceStep {
  step: number;
  name: string;
  [key: string]: unknown;
}

const PRESETS: Array<{ label: string; hint: string; text: string }> = [
  {
    label: '🐞 Bug Log', hint: 'bug',
    text: 'FATAL Exception in thread main java.lang.NullPointerException\n'
      + '  at com.acme.PaymentService.charge(PaymentService.java:42)\n'
      + 'Request failed with error 500, timeout after retry on checkout API.'
  },
  {
    label: '🏛 Legacy Code', hint: 'legacy',
    text: 'PROCEDURE DIVISION.\n  PERFORM CALC-PREMIUM THRU CALC-EXIT.\n'
      + '  IF POLICY-TYPE = "A" MOVE 0.04 TO RATE END-IF.\n'
      + 'GOTO VALIDATE-CLAIM. (COBOL claims rules, 22 years old)'
  },
  {
    label: '😠 Customer Complaint', hint: 'complaint',
    text: 'I am extremely frustrated — checkout keeps failing on card entry, '
      + 'I was charged twice, support kept me waiting 40 minutes and I want a '
      + 'refund or I will cancel my account.'
  },
  {
    label: '📋 Product PRD', hint: 'prd',
    text: 'Feature: one-tap reorder. As a returning user I want to reorder my '
      + 'last basket in one tap. Acceptance criteria: reorder completes < 5s; '
      + 'success metric: +12% repeat purchase rate; MVP scope excludes bundles.'
  }
];

const STEP_ICONS = ['brain', 'shield', 'activity', 'gauge'];

/**
 * Stage 4 — Live Multi-Agent Sandbox Console: paste real text (or use a
 * preset), run the 4-step trace, watch steps animate in sequence.
 */
@Component({
  selector: 'app-stage4-demo',
  standalone: true,
  imports: [FormsModule, LucideAngularModule],
  template: `
    <div class="grid gap-6 xl:grid-cols-[380px,1fr]">
      <!-- Left: payload editor + presets -->
      <aside class="space-y-4 rounded-xl bg-white p-5 shadow-sm">
        <h3 class="text-sm font-bold text-navy">Sandbox Input</h3>
        <div class="flex flex-wrap gap-2">
          @for (preset of presets; track preset.label) {
            <button (click)="applyPreset(preset)"
                    class="rounded-full border border-sky/40 px-3 py-1 text-[11px]
                           font-semibold text-sky transition hover:bg-sky/10">
              {{ preset.label }}
            </button>
          }
        </div>
        <textarea [(ngModel)]="inputText" rows="10"
                  placeholder="Paste a bug log, legacy snippet, customer complaint or PRD…"
                  class="w-full rounded-lg border border-slate-300 p-3 font-mono text-xs
                         focus:border-sky focus:outline-none"></textarea>
        <button (click)="run()" [disabled]="running() || !inputText.trim()"
                class="flex w-full items-center justify-center gap-2 rounded-lg bg-sky
                       py-2.5 text-sm font-semibold text-white transition
                       hover:bg-sky/90 disabled:opacity-40">
          <lucide-icon name="play" class="h-4 w-4"></lucide-icon>
          {{ running() ? 'Agents working…' : 'Execute Multi-Agent Trace' }}
        </button>
      </aside>

      <!-- Center: animated trace console -->
      <section class="rounded-xl bg-navy p-5 shadow-sm">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="flex items-center gap-2 text-sm font-bold text-white">
            <lucide-icon name="activity" class="h-4 w-4 text-sky"></lucide-icon>
            Agent Execution Console
          </h3>
          @if (verdict(); as v) {
            <span class="rounded-full px-3 py-1 text-xs font-bold"
                  [class]="v === 'APPROVE'
                           ? 'bg-emerald-500/20 text-emerald-400'
                           : 'bg-amber-500/20 text-amber-400'">
              {{ v === 'APPROVE' ? '✓ APPROVED' : '⚠ HUMAN REVIEW' }}
            </span>
          }
        </div>

        <div class="space-y-3">
          @for (step of visibleSteps(); track step.step; let i = $index) {
            <div class="animate-[fadeIn_0.4s_ease] rounded-lg border border-slate-700
                        bg-slate-800/60 p-4">
              <div class="flex items-center gap-3">
                <span class="flex h-8 w-8 items-center justify-center rounded-full
                             bg-sky/20 text-sky">
                  <lucide-icon [name]="stepIcons[i]" class="h-4 w-4"></lucide-icon>
                </span>
                <div>
                  <p class="text-xs font-bold text-sky">STEP {{ step.step }}</p>
                  <p class="text-sm font-semibold text-white">{{ step.name }}</p>
                </div>
              </div>
              <div class="mt-3 grid gap-1 pl-11 text-xs text-slate-300">
                @if (step['detectedIntent']) {
                  <p>Intent: <span class="font-bold text-white">{{ step['detectedIntent'] }}</span></p>
                }
                @if (step['status']) {
                  <p>Status: <span class="font-bold"
                       [class]="step['status'] === 'PASS' ? 'text-emerald-400' : 'text-amber-400'">
                       {{ step['status'] }}</span>
                     @if (step['redactionApplied']) { <span>— PII redacted</span> }</p>
                }
                @if (step['mode']) { <p>Mode: {{ step['mode'] }}</p> }
                @if (step['output']) {
                  <pre class="mt-1 whitespace-pre-wrap rounded bg-navy/80 p-2
                              font-mono text-[11px] text-slate-200">{{ step['output'] }}</pre>
                }
                @if (step['confidence'] !== undefined) {
                  <p>Confidence: <span class="font-bold text-emerald-400">
                     {{ step['confidence'] }}</span> •
                     Shadow diff: <span class="font-bold text-sky">
                     {{ step['shadowDiffScore'] }}</span></p>
                }
              </div>
            </div>
          } @empty {
            <p class="py-10 text-center text-sm text-slate-400">
              Paste an artifact (or pick a preset) and execute the trace.
            </p>
          }
          @if (running()) {
            <p class="animate-pulse pl-2 text-xs text-sky">▋ agents processing…</p>
          }
        </div>
      </section>
    </div>
  `
})
export class Stage4DemoComponent implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly state = inject(EngagementStateService);
  private readonly toast = inject(ToastService);

  protected readonly presets = PRESETS;
  protected readonly stepIcons = STEP_ICONS;
  protected inputText = '';
  private selectedHint: string | null = null;

  protected readonly running = signal(false);
  protected readonly visibleSteps = signal<TraceStep[]>([]);
  protected readonly verdict = signal<string | null>(null);

  private timers: ReturnType<typeof setTimeout>[] = [];

  ngOnInit(): void {
    const prior = this.state.getStageResult(4);
    if (prior) {
      this.visibleSteps.set((prior['trace'] as TraceStep[]) ?? []);
      this.verdict.set((prior['finalVerdict'] as string) ?? null);
    }
  }

  ngOnDestroy(): void {
    this.timers.forEach(clearTimeout);
  }

  protected applyPreset(preset: { text: string; hint: string }): void {
    this.inputText = preset.text;
    this.selectedHint = preset.hint;
  }

  protected run(): void {
    this.running.set(true);
    this.visibleSteps.set([]);
    this.verdict.set(null);
    this.timers.forEach(clearTimeout);

    this.api.runStage('stage4/live-demo', {
      inputText: this.inputText,
      hint: this.selectedHint
    }).subscribe({
      next: (result) => {
        this.state.setStageResult(4, result);
        const trace = (result['trace'] as TraceStep[]) ?? [];
        // Animated reveal: one agent step every 600ms.
        trace.forEach((step, i) => {
          this.timers.push(setTimeout(() => {
            this.visibleSteps.update((steps) => [...steps, step]);
            if (i === trace.length - 1) {
              this.running.set(false);
              this.verdict.set((result['finalVerdict'] as string) ?? null);
              this.toast.success('Multi-agent trace complete');
            }
          }, 600 * (i + 1)));
        });
      },
      error: () => {
        this.running.set(false);
        this.toast.error('Live demo failed — is ai-engine up?');
      }
    });
  }
}
