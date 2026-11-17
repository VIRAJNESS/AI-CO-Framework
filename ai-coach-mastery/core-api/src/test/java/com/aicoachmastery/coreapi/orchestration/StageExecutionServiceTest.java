package com.aicoachmastery.coreapi.orchestration;

import com.aicoachmastery.coreapi.artifact.ArtifactMapper;
import com.aicoachmastery.coreapi.artifact.StageArtifact;
import com.aicoachmastery.coreapi.artifact.StageArtifactRepository;
import com.aicoachmastery.coreapi.common.BusinessRuleException;
import com.aicoachmastery.coreapi.common.UpstreamServiceException;
import com.aicoachmastery.coreapi.engagement.AdvisorTier;
import com.aicoachmastery.coreapi.engagement.ClientEngagement;
import com.aicoachmastery.coreapi.engagement.ClientEngagementRepository;
import com.aicoachmastery.coreapi.engagement.DomainTrack;
import com.aicoachmastery.coreapi.engagement.EngagementService;
import com.aicoachmastery.coreapi.governance.GovernanceService;
import com.aicoachmastery.coreapi.orchestration.AiEngineClient.InsightResult;
import com.aicoachmastery.coreapi.orchestration.AiEngineClient.ReportResult;
import com.aicoachmastery.coreapi.orchestration.StageExecutionDtos.ExecuteStageRequest;
import com.aicoachmastery.coreapi.orchestration.StageExecutionDtos.ExecuteStageResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * StageExecutionService orchestration tests: governance gating, upstream
 * failure safety, artifact persistence and stage auto-advance.
 */
@ExtendWith(MockitoExtension.class)
class StageExecutionServiceTest {

    @Mock
    private EngagementService engagementService;
    @Mock
    private GovernanceService governanceService;
    @Mock
    private AiEngineClient aiEngineClient;
    @Mock
    private StageArtifactRepository artifactRepository;
    @Mock
    private ClientEngagementRepository engagementRepository;

    private StageExecutionService service;

    private ClientEngagement engagement;

    @BeforeEach
    void setUp() {
        service = new StageExecutionService(
                engagementService, governanceService, aiEngineClient,
                artifactRepository, engagementRepository, new ArtifactMapper());
        engagement = new ClientEngagement(
                UUID.randomUUID(), "Acme", "FinTech",
                DomainTrack.SDLC, AdvisorTier.TRANSFORMATION_RETAINER, OffsetDateTime.now());
    }

    private void stubHappyUpstream() {
        when(aiEngineClient.generateInsight(anyString()))
                .thenReturn(new InsightResult("mock", "Focus on adoption velocity."));
        when(aiEngineClient.generateReport(anyString(), anyString(), eq("pptx")))
                .thenReturn(new ReportResult("k.pptx", "/data/artifacts/k.pptx", "pptx", 1000));
        when(aiEngineClient.generateReport(anyString(), anyString(), eq("docx")))
                .thenReturn(new ReportResult("k.docx", "/data/artifacts/k.docx", "docx", 900));
    }

    // --- Happy path ------------------------------------------------------------

    @Test
    void execute_runsDiagnostics_persistsArtifact_andAdvancesStage() {
        when(engagementService.getEntity(engagement.getId())).thenReturn(engagement);
        when(governanceService.validateForExecution(engagement.getId())).thenReturn(List.of());
        stubHappyUpstream();

        ExecuteStageResponse response = service.execute(
                engagement.getId(), 1, new ExecuteStageRequest("{\"a\":1}", "kickoff"));

        assertThat(response.executedStage()).isEqualTo(1);
        assertThat(response.executedStageName()).isEqualTo("Discovery & Audit");
        assertThat(response.newCurrentStage()).isEqualTo(2);
        assertThat(response.llmProvider()).isEqualTo("mock");
        assertThat(response.artifact().pptxFileUrl()).endsWith(".pptx");
        assertThat(response.artifact().docxFileUrl()).endsWith(".docx");

        ArgumentCaptor<StageArtifact> captor = ArgumentCaptor.forClass(StageArtifact.class);
        verify(artifactRepository).save(captor.capture());
        assertThat(captor.getValue().getDiagnosticOutputJson()).contains("adoption velocity");
        verify(engagementRepository).save(engagement);
    }

    // --- Negative paths ---------------------------------------------------------

    @Test
    void execute_blockedByFailingGate_returnsConflictAndCallsNoUpstream() {
        when(engagementService.getEntity(engagement.getId())).thenReturn(engagement);
        when(governanceService.validateForExecution(engagement.getId()))
                .thenThrow(new BusinessRuleException(
                        "Stage execution blocked by failing governance gates: PII_REDACTION"));

        assertThatThrownBy(() -> service.execute(engagement.getId(), 1, null))
                .isInstanceOf(BusinessRuleException.class)
                .hasMessageContaining("PII_REDACTION");

        verify(aiEngineClient, never()).generateInsight(anyString());
        verify(artifactRepository, never()).save(any());
    }

    @Test
    void execute_upstreamFailure_mutatesNothing() {
        when(engagementService.getEntity(engagement.getId())).thenReturn(engagement);
        when(governanceService.validateForExecution(engagement.getId())).thenReturn(List.of());
        when(aiEngineClient.generateInsight(anyString()))
                .thenThrow(new UpstreamServiceException("ai-engine down"));

        assertThatThrownBy(() -> service.execute(engagement.getId(), 1, null))
                .isInstanceOf(UpstreamServiceException.class);

        assertThat(engagement.getCurrentStage()).isEqualTo(1); // unchanged
        verify(artifactRepository, never()).save(any());
        verify(engagementRepository, never()).save(any());
    }

    // --- Edge cases --------------------------------------------------------------

    @Test
    void execute_wrongStageRequested_isRejected() {
        // Edge: requested stage must equal current stage exactly.
        when(engagementService.getEntity(engagement.getId())).thenReturn(engagement);

        assertThatThrownBy(() -> service.execute(engagement.getId(), 3, null))
                .isInstanceOf(BusinessRuleException.class)
                .hasMessageContaining("does not match current stage");
    }

    @Test
    void execute_invalidStageNumber_isRejectedBeforeLookup() {
        // Edge: out-of-range stage fails fast, no repository interaction.
        assertThatThrownBy(() -> service.execute(engagement.getId(), 7, null))
                .isInstanceOf(BusinessRuleException.class)
                .hasMessageContaining("between 1 and 6");
        verify(engagementRepository, never()).save(any());
    }

    @Test
    void execute_atFinalStage_capsAtSix() {
        // Edge: executing stage 6 must not advance past the lifecycle end.
        engagement.moveToStage(6);
        when(engagementService.getEntity(engagement.getId())).thenReturn(engagement);
        when(governanceService.validateForExecution(engagement.getId())).thenReturn(List.of());
        stubHappyUpstream();

        ExecuteStageResponse response = service.execute(engagement.getId(), 6, null);

        assertThat(response.executedStage()).isEqualTo(6);
        assertThat(response.newCurrentStage()).isEqualTo(6); // capped
    }

    @Test
    void execute_nullRequestBody_isSupported() {
        // Edge: body is optional — no input payload, no notes.
        when(engagementService.getEntity(engagement.getId())).thenReturn(engagement);
        when(governanceService.validateForExecution(engagement.getId())).thenReturn(List.of());
        stubHappyUpstream();

        ExecuteStageResponse response = service.execute(engagement.getId(), 1, null);

        assertThat(response.artifact().inputPayloadJson()).isNull();
        assertThat(response.newCurrentStage()).isEqualTo(2);
    }
}
