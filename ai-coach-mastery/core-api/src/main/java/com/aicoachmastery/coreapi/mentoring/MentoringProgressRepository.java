package com.aicoachmastery.coreapi.mentoring;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/** Spring Data repository for mentoring progress records. */
@Repository
public interface MentoringProgressRepository extends JpaRepository<MentoringProgress, UUID> {

    List<MentoringProgress> findByEngagementId(UUID engagementId);

    Optional<MentoringProgress> findByEngagementIdAndRoleTrackAndModuleNameAndPhase(
            UUID engagementId, RoleTrack roleTrack, String moduleName, MentoringPhase phase);
}
