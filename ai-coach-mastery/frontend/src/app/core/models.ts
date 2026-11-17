/** Shared domain models mirroring core-api and ai-engine contracts. */

export type DomainTrack = 'SDLC' | 'PDLC' | 'STARTUP' | 'LEGACY';
export type AdvisorTier =
  | 'DIAGNOSTIC_SPRINT'
  | 'TRANSFORMATION_RETAINER'
  | 'FRACTIONAL_HEAD_COACH';
export type GateStatus = 'PASS' | 'WARN' | 'FAIL';

export interface Engagement {
  id: string;
  clientName: string;
  industry: string;
  domainTrack: DomainTrack;
  currentStage: number;
  currentStageName: string;
  advisorTier: AdvisorTier;
  createdAt: string;
}

export interface GovernanceGate {
  id: string;
  engagementId: string;
  gateName: string;
  status: GateStatus;
  score: number | null;
  notes: string | null;
}

export interface MentoringProgress {
  id: string;
  engagementId: string;
  roleTrack: string;
  moduleName: string;
  phase: 'SEE_ONE' | 'CO_BUILD_ONE' | 'LEAD_ONE';
  completionPct: number;
}

export interface StageArtifact {
  id: string;
  engagementId: string;
  stageNumber: number;
  stageName: string;
  inputPayloadJson: string | null;
  diagnosticOutputJson: string | null;
  pptxFileUrl: string | null;
  docxFileUrl: string | null;
  generatedAt: string;
}

/** Canonical stage metadata for the stepper. */
export const STAGES: ReadonlyArray<{ num: number; short: string; name: string }> = [
  { num: 1, short: 'Pitch', name: 'Discovery & Audit' },
  { num: 2, short: 'Diagnostic', name: 'Diagnostic & Baseline' },
  { num: 3, short: 'Blueprint', name: 'Pilot Design' },
  { num: 4, short: 'Live Demo', name: 'Execution & Coaching' },
  { num: 5, short: 'Statistical ROI', name: 'Measurement & ROI' },
  { num: 6, short: '30-60-90 & Mentor', name: 'Scale & Handoff' },
];
