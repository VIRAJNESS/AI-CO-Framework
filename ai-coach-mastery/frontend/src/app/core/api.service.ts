import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, catchError, of } from 'rxjs';

import {
  AdvisorTier,
  DomainTrack,
  Engagement,
  GovernanceGate,
  MentoringProgress,
  StageArtifact
} from './models';

/** Service health snapshot used by the dashboard status cards. */
export interface ServiceHealth {
  name: string;
  status: 'UP' | 'DOWN' | 'UNKNOWN';
  detail?: string;
}

export interface Coach {
  id: string;
  name: string;
  email: string;
  specialty: string;
  createdAt: string;
}

/**
 * API gateway service. All backend calls go through the dev-server proxy
 * (proxy.conf.json): /api/core/* -> core-api /api/v1/*, /api/ai/* ->
 * ai-engine /api/v1/* — keeping local/cloud parity (ingress in K8s).
 * Reactive state is exposed as Angular Signals.
 */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  /** Reactive health state per backend service. */
  readonly coreHealth = signal<ServiceHealth>({ name: 'core-api', status: 'UNKNOWN' });
  readonly aiHealth = signal<ServiceHealth>({ name: 'ai-engine', status: 'UNKNOWN' });
  readonly coaches = signal<Coach[]>([]);

  refreshHealth(): void {
    this.http
      .get<{ status: string }>('/health/core')
      .pipe(catchError(() => of({ status: 'DOWN' })))
      .subscribe((res) =>
        this.coreHealth.set({
          name: 'core-api',
          status: res.status === 'UP' ? 'UP' : 'DOWN'
        })
      );

    this.http
      .get<{ status: string; llm_provider?: string }>('/health/ai')
      .pipe(catchError(() => of({ status: 'DOWN' as const, llm_provider: undefined })))
      .subscribe((res) =>
        this.aiHealth.set({
          name: 'ai-engine',
          status: res.status === 'UP' ? 'UP' : 'DOWN',
          detail: res.llm_provider ? `llm: ${res.llm_provider}` : undefined
        })
      );
  }

  loadCoaches(): void {
    this.http
      .get<Coach[]>('/api/core/coaches')
      .pipe(catchError(() => of([] as Coach[])))
      .subscribe((list) => this.coaches.set(list));
  }

  // --- Engagements (core-api) -------------------------------------------------

  listEngagements(): Observable<Engagement[]> {
    return this.http.get<Engagement[]>('/api/core/engagements');
  }

  getEngagement(id: string): Observable<Engagement> {
    return this.http.get<Engagement>(`/api/core/engagements/${id}`);
  }

  createEngagement(body: {
    clientName: string;
    industry: string;
    domainTrack: DomainTrack;
    advisorTier: AdvisorTier;
  }): Observable<Engagement> {
    return this.http.post<Engagement>('/api/core/engagements', body);
  }

  listGates(id: string): Observable<GovernanceGate[]> {
    return this.http.get<GovernanceGate[]>(`/api/core/engagements/${id}/gates`);
  }

  listMentoring(id: string): Observable<MentoringProgress[]> {
    return this.http.get<MentoringProgress[]>(`/api/core/engagements/${id}/mentoring`);
  }

  listArtifacts(id: string): Observable<StageArtifact[]> {
    return this.http.get<StageArtifact[]>(`/api/core/engagements/${id}/artifacts`);
  }

  // --- Intelligence engine (ai-engine) -----------------------------------------

  /** Run a stage computation in the analytical sandbox (ungoverned). */
  runStage(stagePath: string, body: unknown): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`/api/ai/engine/${stagePath}`, body);
  }

  /** Render a boardroom deliverable and return the binary for download. */
  renderDocument(
    stageNum: number,
    format: 'pptx' | 'docx',
    engagementData: Record<string, unknown>,
    stageResult: Record<string, unknown>
  ): Observable<Blob> {
    return this.http.post('/api/ai/engine/documents/render',
      { stageNum, format, engagementData, stageResult },
      { responseType: 'blob' });
  }
}
