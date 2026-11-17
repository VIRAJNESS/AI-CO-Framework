package com.aicoachmastery.coreapi.engagement;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.OffsetDateTime;
import java.util.UUID;

/** Request/response DTOs for engagement endpoints (immutable records). */
public final class EngagementDtos {

    private EngagementDtos() {
        // holder — no instances
    }

    /** Create payload — new engagements always start at stage 1. */
    public record CreateEngagementRequest(
            @NotBlank @Size(max = 160) String clientName,
            @NotBlank @Size(max = 120) String industry,
            @NotNull DomainTrack domainTrack,
            @NotNull AdvisorTier advisorTier) {
    }

    /** Update payload — stage is deliberately excluded (use transitions). */
    public record UpdateEngagementRequest(
            @NotBlank @Size(max = 160) String clientName,
            @NotBlank @Size(max = 120) String industry,
            @NotNull DomainTrack domainTrack,
            @NotNull AdvisorTier advisorTier) {
    }

    /** Stage transition request — rules enforced in the service layer. */
    public record StageTransitionRequest(
            @Min(1) @Max(6) int targetStage) {
    }

    /** Full engagement representation. */
    public record EngagementResponse(
            UUID id,
            String clientName,
            String industry,
            DomainTrack domainTrack,
            int currentStage,
            String currentStageName,
            AdvisorTier advisorTier,
            OffsetDateTime createdAt) {
    }
}
