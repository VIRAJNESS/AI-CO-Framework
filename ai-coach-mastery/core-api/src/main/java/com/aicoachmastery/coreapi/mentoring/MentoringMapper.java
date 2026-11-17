package com.aicoachmastery.coreapi.mentoring;

import com.aicoachmastery.coreapi.mentoring.MentoringDtos.MentoringProgressResponse;
import org.springframework.stereotype.Component;

/** Entity -> DTO mapping for mentoring progress. */
@Component
public class MentoringMapper {

    public MentoringProgressResponse toResponse(MentoringProgress entity) {
        return new MentoringProgressResponse(
                entity.getId(),
                entity.getEngagementId(),
                entity.getRoleTrack(),
                entity.getModuleName(),
                entity.getPhase(),
                entity.getCompletionPct());
    }
}
