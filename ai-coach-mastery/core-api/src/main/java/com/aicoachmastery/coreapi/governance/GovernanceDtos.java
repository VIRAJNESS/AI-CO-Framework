package com.aicoachmastery.coreapi.governance;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.util.UUID;

/** Request/response DTOs for governance gate endpoints. */
public final class GovernanceDtos {

    private GovernanceDtos() {
        // holder — no instances
    }

    /** Upsert payload: records (or re-records) a gate evaluation result. */
    public record GateEvaluationRequest(
            @NotNull GateName gateName,
            @NotNull GateStatus status,
            Double score,
            @Size(max = 2000) String notes) {
    }

    public record GateResponse(
            UUID id,
            UUID engagementId,
            GateName gateName,
            GateStatus status,
            Double score,
            String notes) {
    }
}
