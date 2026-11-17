import { EngagementStateService } from './engagement-state.service';
import { Engagement } from './models';

const ENGAGEMENT: Engagement = {
  id: 'e-1', clientName: 'Acme', industry: 'FinTech',
  domainTrack: 'SDLC', currentStage: 3, currentStageName: 'Pilot Design',
  advisorTier: 'DIAGNOSTIC_SPRINT', createdAt: '2025-01-01T00:00:00Z'
};

/** EngagementStateService — happy, negative and edge cases. */
describe('EngagementStateService', () => {
  let service: EngagementStateService;

  beforeEach(() => {
    service = new EngagementStateService();
  });

  // --- Happy paths -------------------------------------------------------------

  it('setEngagement stores the record and syncs activeStage', () => {
    service.setEngagement(ENGAGEMENT);
    expect(service.engagement()?.clientName).toBe('Acme');
    expect(service.activeStage()).toBe(3);
  });

  it('stage results are stored and read back per stage', () => {
    service.setStageResult(2, { maturityIndex: 55 });
    expect(service.getStageResult(2)).toEqual({ maturityIndex: 55 });
  });

  it('activeStageResult tracks the active stage', () => {
    service.setEngagement(ENGAGEMENT);
    service.setStageResult(3, { theme: 'x' });
    expect(service.activeStageResult()).toEqual({ theme: 'x' });

    service.activeStage.set(1);
    expect(service.activeStageResult()).toBeNull();
  });

  // --- Negative path -------------------------------------------------------------

  it('getStageResult returns null for a stage never run', () => {
    expect(service.getStageResult(5)).toBeNull();
  });

  // --- Edge cases -------------------------------------------------------------------

  it('edge: engagementData is empty object before an engagement loads', () => {
    expect(service.engagementData()).toEqual({});
  });

  it('edge: engagementData maps only doc-factory fields', () => {
    service.setEngagement(ENGAGEMENT);
    expect(service.engagementData()).toEqual({
      clientName: 'Acme', industry: 'FinTech', domainTrack: 'SDLC'
    });
  });

  it('edge: setStageResult overwrites prior result for the same stage', () => {
    service.setStageResult(1, { v: 1 });
    service.setStageResult(1, { v: 2 });
    expect(service.getStageResult(1)).toEqual({ v: 2 });
  });

  it('edge: reset clears everything back to defaults', () => {
    service.setEngagement(ENGAGEMENT);
    service.setStageResult(3, { any: true });
    service.gates.set([{ id: 'g', engagementId: 'e-1', gateName: 'FINOPS_CAP',
      status: 'FAIL', score: 1.2, notes: null }]);

    service.reset();

    expect(service.engagement()).toBeNull();
    expect(service.gates()).toEqual([]);
    expect(service.getStageResult(3)).toBeNull();
    expect(service.activeStage()).toBe(1);
  });
});
