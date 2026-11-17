import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';

import { ApiService, Coach } from './api.service';

/**
 * ApiService tests — happy path, negative path (backend down) and edge cases
 * (empty roster, malformed health payload, repeated refresh).
 */
describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  // --- Happy paths ---------------------------------------------------------

  it('marks services UP when health endpoints respond UP', () => {
    service.refreshHealth();

    httpMock.expectOne('/health/core').flush({ status: 'UP' });
    httpMock.expectOne('/health/ai').flush({ status: 'UP', llm_provider: 'mock' });

    expect(service.coreHealth().status).toBe('UP');
    expect(service.aiHealth().status).toBe('UP');
    expect(service.aiHealth().detail).toBe('llm: mock');
  });

  it('loads coaches into the signal', () => {
    const roster: Coach[] = [
      { id: '1', name: 'Ada', email: 'ada@x.dev', specialty: 'SDLC', createdAt: '2025-01-01' }
    ];
    service.loadCoaches();
    httpMock.expectOne('/api/core/coaches').flush(roster);

    expect(service.coaches().length).toBe(1);
    expect(service.coaches()[0].name).toBe('Ada');
  });

  // --- Negative path --------------------------------------------------------

  it('marks a service DOWN when its health endpoint errors', () => {
    service.refreshHealth();

    httpMock.expectOne('/health/core').error(new ProgressEvent('network'));
    httpMock.expectOne('/health/ai').flush({ status: 'UP' });

    expect(service.coreHealth().status).toBe('DOWN');
    expect(service.aiHealth().status).toBe('UP');
  });

  // --- Edge cases -----------------------------------------------------------

  it('edge: empty roster yields empty signal, not an error', () => {
    service.loadCoaches();
    httpMock.expectOne('/api/core/coaches').flush([]);
    expect(service.coaches()).toEqual([]);
  });

  it('edge: unexpected health status string maps to DOWN', () => {
    service.refreshHealth();
    httpMock.expectOne('/health/core').flush({ status: 'DEGRADED' });
    httpMock.expectOne('/health/ai').flush({ status: 'UP' });
    expect(service.coreHealth().status).toBe('DOWN');
  });

  it('edge: coaches endpoint failure falls back to empty list', () => {
    service.loadCoaches();
    httpMock.expectOne('/api/core/coaches').error(new ProgressEvent('network'));
    expect(service.coaches()).toEqual([]);
  });

  // --- Engagement + engine methods -----------------------------------------

  it('listEngagements hits the core proxy path', () => {
    service.listEngagements().subscribe((list) => expect(list.length).toBe(1));
    const req = httpMock.expectOne('/api/core/engagements');
    expect(req.request.method).toBe('GET');
    req.flush([{ id: 'x', clientName: 'Acme', industry: 'FinTech',
      domainTrack: 'SDLC', currentStage: 1, currentStageName: 'Discovery & Audit',
      advisorTier: 'DIAGNOSTIC_SPRINT', createdAt: '' }]);
  });

  it('runStage posts to the ai-engine proxy path', () => {
    service.runStage('stage1/pitch-simulator', { a: 1 }).subscribe();
    const req = httpMock.expectOne('/api/ai/engine/stage1/pitch-simulator');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ a: 1 });
    req.flush({ ok: true });
  });

  it('renderDocument requests a blob with the full payload', () => {
    service.renderDocument(3, 'pptx', { clientName: 'Acme' }, { theme: 'x' })
      .subscribe((blob) => expect(blob instanceof Blob).toBeTrue());
    const req = httpMock.expectOne('/api/ai/engine/documents/render');
    expect(req.request.responseType).toBe('blob');
    expect(req.request.body).toEqual({
      stageNum: 3, format: 'pptx',
      engagementData: { clientName: 'Acme' }, stageResult: { theme: 'x' }
    });
    req.flush(new Blob(['PK']));
  });

  it('edge: createEngagement propagates server errors to the caller', () => {
    let failed = false;
    service.createEngagement({ clientName: 'A', industry: 'B',
      domainTrack: 'SDLC', advisorTier: 'DIAGNOSTIC_SPRINT' })
      .subscribe({ error: () => (failed = true) });
    httpMock.expectOne('/api/core/engagements')
      .flush({ title: 'oops' }, { status: 500, statusText: 'Server Error' });
    expect(failed).toBeTrue();
  });
});
