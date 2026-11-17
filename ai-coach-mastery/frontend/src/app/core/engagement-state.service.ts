import { Injectable, computed, signal } from '@angular/core';

import { Engagement, GovernanceGate, MentoringProgress } from './models';

/**
 * Shared signal state for the lifecycle workspace: the loaded engagement,
 * governance/mentoring context, the active stage, and the latest sandbox
 * result per stage (consumed by the artifact studio for document rendering).
 */
@Injectable({ providedIn: 'root' })
export class EngagementStateService {
  readonly engagement = signal<Engagement | null>(null);
  readonly gates = signal<GovernanceGate[]>([]);
  readonly mentoring = signal<MentoringProgress[]>([]);
  readonly activeStage = signal<number>(1);

  /** Latest run result per stage number (sandbox output). */
  private readonly stageResults = signal<Record<number, Record<string, unknown>>>({});

  readonly activeStageResult = computed(
    () => this.stageResults()[this.activeStage()] ?? null);

  /** Engagement payload forwarded to the document factory. */
  readonly engagementData = computed<Record<string, unknown>>(() => {
    const e = this.engagement();
    return e
      ? { clientName: e.clientName, industry: e.industry, domainTrack: e.domainTrack }
      : {};
  });

  setEngagement(engagement: Engagement): void {
    this.engagement.set(engagement);
    this.activeStage.set(engagement.currentStage);
  }

  setStageResult(stage: number, result: Record<string, unknown>): void {
    this.stageResults.update((map) => ({ ...map, [stage]: result }));
  }

  getStageResult(stage: number): Record<string, unknown> | null {
    return this.stageResults()[stage] ?? null;
  }

  reset(): void {
    this.engagement.set(null);
    this.gates.set([]);
    this.mentoring.set([]);
    this.stageResults.set({});
    this.activeStage.set(1);
  }
}
