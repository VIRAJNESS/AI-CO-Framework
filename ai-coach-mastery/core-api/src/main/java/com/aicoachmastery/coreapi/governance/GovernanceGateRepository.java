package com.aicoachmastery.coreapi.governance;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/** Spring Data repository for governance gates. */
@Repository
public interface GovernanceGateRepository extends JpaRepository<GovernanceGate, UUID> {

    List<GovernanceGate> findByEngagementId(UUID engagementId);

    Optional<GovernanceGate> findByEngagementIdAndGateName(UUID engagementId, GateName gateName);

    List<GovernanceGate> findByEngagementIdAndStatus(UUID engagementId, GateStatus status);
}
