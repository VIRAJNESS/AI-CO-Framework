package com.aicoachmastery.coreapi.artifact;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

/** Spring Data repository for stage artifacts. */
@Repository
public interface StageArtifactRepository extends JpaRepository<StageArtifact, UUID> {

    List<StageArtifact> findByEngagementIdOrderByStageNumberAscGeneratedAtDesc(UUID engagementId);
}
