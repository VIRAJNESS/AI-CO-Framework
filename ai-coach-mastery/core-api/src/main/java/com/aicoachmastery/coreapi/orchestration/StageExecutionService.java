package com.aicoachmastery.coreapi.orchestration;

import com.aicoachmastery.coreapi.artifact.ArtifactMapper;
import com.aicoachmastery.coreapi.artifact.StageArtifact;
import com.aicoachmastery.coreapi.artifact.StageArtifactRepository;
import com.aicoachmastery.coreapi.common.BusinessRuleException;
import com.aicoachmastery.coreapi.engagement.ClientEngagement;
import com.aicoachmastery.coreapi.engagement.ClientEngagementRepository;
import com.aicoachmastery.coreapi.engagement.EngagementService;
import com.aicoachmastery.coreapi.engagement.Stage;
import com.aicoachmastery.coreapi.governance.GovernanceDtos.GateResponse;
import com.aicoachmastery.coreapi.governance.GovernanceService;
import com.aicoachmastery.coreapi.orchestration.AiEngineClient.InsightResult;
import com.aicoachmastery.coreapi.orchestration.AiEngineClient.ReportResult;
import com.aicoachmastery.coreapi.orchestration.StageExecutionDtos.ExecuteStageRequest;
import com.aicoachmastery.coreapi.orchestration.StageExecutionDtos.ExecuteStageResponse;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

/**
 * Proxy orchestration of a lifecycle stage execution:
 *
 *  1. validate the requested stage matches the engagement's current stage;
 *  2. enforce governance gates (FAIL blocks, WARN is surfaced);
 *  3. call ai-engine for diagnostics + PPTX/DOCX deliverables (fail => 502,
 *     no state mutated — upstream calls happen before any persistence);
 *  4. persist the StageArtifact and auto-advance the engagement one stage;
 *  5. return the unified execution JSON.
 */
@Service
public class StageExecutionService {

    private final EngagementService engagementService;
    private final GovernanceService governanceService;
    private final AiEngineClient aiEngineClient;
    private final StageArtifactRepository artifactRepository;
    private final ClientEngagementRepository engagementRepository;
    private final ArtifactMapper artifactMapper;

    public StageExecutionService(EngagementService engagementService,
                                 GovernanceService governanceService,
                                 AiEngineClient aiEngineClient,
                                 StageArtifactRepository artifactRepository,
                                 ClientEngagementRepository engagementRepository,
                                 ArtifactMapper artifactMapper) {
        this.engagementService = engagementService;
        this.governanceService = governanceService;
        this.aiEngineClient = aiEngineClient;
        this.artifactRepository = artifactRepository;
        this.engagementRepository = engagementRepository;
        this.artifactMapper = artifactMapper;
    }

    @Transactional
    public ExecuteStageResponse execute(UUID engagementId, int stageNumber,
                                        ExecuteStageRequest request) {
        if (!Stage.isValid(stageNumber)) {
            throw new BusinessRuleException(
                    "Stage number must be between 1 and 6, got: " + stageNumber);
        }

        ClientEngagement engagement = engagementService.getEntity(engagementId);
        if (engagement.getCurrentStage() != stageNumber) {
            throw new BusinessRuleException(
                    "Requested stage " + stageNumber + " does not match current stage "
                    + engagement.getCurrentStage() + ". Execute the current stage.");
        }

        // Governance gating: throws on FAIL, returns WARN gates for visibility.
        List<GateResponse> warnings = governanceService.validateForExecution(engagementId);

        Stage stage = Stage.of(stageNumber);
        String prompt = buildDiagnosticPrompt(engagement, stage, request);

        // Upstream calls first — if any fails, nothing has been persisted.
        InsightResult insight = aiEngineClient.generateInsight(prompt);
        String deliverableTitle = engagement.getClientName() + " — " + stage.displayName();
        ReportResult pptx = aiEngineClient.generateReport(
                deliverableTitle, insight.insight(), "pptx");
        ReportResult docx = aiEngineClient.generateReport(
                deliverableTitle, insight.insight(), "docx");

        StageArtifact artifact = new StageArtifact(
                UUID.randomUUID(),
                engagementId,
                stageNumber,
                stage.displayName(),
                request == null ? null : request.inputPayloadJson(),
                toDiagnosticJson(insight),
                null,
                pptx.locator(),
                docx.locator(),
                OffsetDateTime.now());
        artifactRepository.save(artifact);

        engagement.advanceStage();
        engagementRepository.save(engagement);

        return new ExecuteStageResponse(
                engagementId,
                stageNumber,
                stage.displayName(),
                engagement.getCurrentStage(),
                insight.provider(),
                warnings,
                artifactMapper.toResponse(artifact));
    }

    /** Compose a deterministic diagnostic prompt from engagement context. */
    private String buildDiagnosticPrompt(ClientEngagement engagement, Stage stage,
                                         ExecuteStageRequest request) {
        StringBuilder prompt = new StringBuilder()
                .append("Run stage '").append(stage.displayName())
                .append("' diagnostics for client '").append(engagement.getClientName())
                .append("' (industry: ").append(engagement.getIndustry())
                .append(", track: ").append(engagement.getDomainTrack())
                .append(", tier: ").append(engagement.getAdvisorTier()).append(").");
        if (request != null && request.notes() != null && !request.notes().isBlank()) {
            prompt.append(" Additional context: ").append(request.notes());
        }
        return prompt.toString();
    }

    /** Minimal JSON envelope for the diagnostic output (no extra deps). */
    private String toDiagnosticJson(InsightResult insight) {
        return "{\"provider\":\"" + escapeJson(insight.provider())
                + "\",\"insight\":\"" + escapeJson(insight.insight()) + "\"}";
    }

    private String escapeJson(String value) {
        return value == null ? "" : value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }
}
