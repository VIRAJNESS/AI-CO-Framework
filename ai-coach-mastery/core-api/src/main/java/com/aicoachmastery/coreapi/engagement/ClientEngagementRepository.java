package com.aicoachmastery.coreapi.engagement;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

/** Spring Data repository for client engagements. */
@Repository
public interface ClientEngagementRepository extends JpaRepository<ClientEngagement, UUID> {
}
