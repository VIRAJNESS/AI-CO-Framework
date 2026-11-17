package com.aicoachmastery.coreapi.engagement;

import com.aicoachmastery.coreapi.engagement.EngagementDtos.EngagementResponse;
import org.springframework.stereotype.Component;

/** Entity <-> DTO mapping for engagements (manual, single-responsibility). */
@Component
public class EngagementMapper {

    public EngagementResponse toResponse(ClientEngagement entity) {
        return new EngagementResponse(
                entity.getId(),
                entity.getClientName(),
                entity.getIndustry(),
                entity.getDomainTrack(),
                entity.getCurrentStage(),
                Stage.of(entity.getCurrentStage()).displayName(),
                entity.getAdvisorTier(),
                entity.getCreatedAt());
    }
}
