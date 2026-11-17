package com.aicoachmastery.coreapi.artifact;

import com.aicoachmastery.coreapi.artifact.ArtifactDtos.StageArtifactResponse;
import org.springframework.stereotype.Component;

/** Entity -> DTO mapping for stage artifacts. */
@Component
public class ArtifactMapper {

    public StageArtifactResponse toResponse(StageArtifact entity) {
        return new StageArtifactResponse(
                entity.getId(),
                entity.getEngagementId(),
                entity.getStageNumber(),
                entity.getStageName(),
                entity.getInputPayloadJson(),
                entity.getDiagnosticOutputJson(),
                entity.getLiveDemoStateJson(),
                entity.getPptxFileUrl(),
                entity.getDocxFileUrl(),
                entity.getGeneratedAt());
    }
}
