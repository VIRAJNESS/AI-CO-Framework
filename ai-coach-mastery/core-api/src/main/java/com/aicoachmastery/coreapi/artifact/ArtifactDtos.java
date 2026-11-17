package com.aicoachmastery.coreapi.artifact;

import java.time.OffsetDateTime;
import java.util.UUID;

/** Response DTOs for stage artifacts. */
public final class ArtifactDtos {

    private ArtifactDtos() {
        // holder — no instances
    }

    public record StageArtifactResponse(
            UUID id,
            UUID engagementId,
            int stageNumber,
            String stageName,
            String inputPayloadJson,
            String diagnosticOutputJson,
            String liveDemoStateJson,
            String pptxFileUrl,
            String docxFileUrl,
            OffsetDateTime generatedAt) {
    }
}
