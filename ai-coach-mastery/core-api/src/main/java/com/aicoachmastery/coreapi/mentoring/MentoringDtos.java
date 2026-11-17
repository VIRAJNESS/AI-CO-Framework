package com.aicoachmastery.coreapi.mentoring;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.util.UUID;

/** Request/response DTOs for mentoring progress endpoints. */
public final class MentoringDtos {

    private MentoringDtos() {
        // holder — no instances
    }

    /** Upsert payload: records progress for a (roleTrack, module, phase). */
    public record MentoringProgressRequest(
            @NotNull RoleTrack roleTrack,
            @NotBlank @Size(max = 160) String moduleName,
            @NotNull MentoringPhase phase,
            @DecimalMin("0.0") @DecimalMax("100.0") double completionPct) {
    }

    public record MentoringProgressResponse(
            UUID id,
            UUID engagementId,
            RoleTrack roleTrack,
            String moduleName,
            MentoringPhase phase,
            double completionPct) {
    }
}
