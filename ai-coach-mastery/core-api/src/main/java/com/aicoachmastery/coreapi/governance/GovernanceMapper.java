package com.aicoachmastery.coreapi.governance;

import com.aicoachmastery.coreapi.governance.GovernanceDtos.GateResponse;
import org.springframework.stereotype.Component;

/** Entity -> DTO mapping for governance gates. */
@Component
public class GovernanceMapper {

    public GateResponse toResponse(GovernanceGate entity) {
        return new GateResponse(
                entity.getId(),
                entity.getEngagementId(),
                entity.getGateName(),
                entity.getStatus(),
                entity.getScore(),
                entity.getNotes());
    }
}
