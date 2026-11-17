package com.aicoachmastery.coreapi.orchestration;

import com.aicoachmastery.coreapi.artifact.ArtifactDtos.StageArtifactResponse;
import com.aicoachmastery.coreapi.governance.GovernanceDtos.GateResponse;
import jakarta.validation.constraints.Size;

import java.util.List;
import java.util.UUID;

/** DTOs for the stage-execution orchestration endpoint. */
public final class StageExecutionDtos {

    private StageExecutionDtos() {
        // holder — no instances
    }

    /** Optional caller-supplied context forwarded to the diagnostics engine. */
    public record ExecuteStageRequest(
            @Size(max = 20000) String inputPayloadJson,
            @Size(max = 8000) String notes) {
    }

    /** Unified JSON returned after a successful stage execution. */
    public record ExecuteStageResponse(
            UUID engagementId,
            int executedStage,
            String executedStageName,
            int newCurrentStage,
            String llmProvider,
            List<GateResponse> governanceWarnings,
            StageArtifactResponse artifact) {
    }
}
