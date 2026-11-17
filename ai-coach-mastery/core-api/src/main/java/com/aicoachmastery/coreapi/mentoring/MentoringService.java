package com.aicoachmastery.coreapi.mentoring;

import com.aicoachmastery.coreapi.mentoring.MentoringDtos.MentoringProgressRequest;
import com.aicoachmastery.coreapi.mentoring.MentoringDtos.MentoringProgressResponse;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

/** Mentoring use cases: record (upsert) and list module progress. */
@Service
public class MentoringService {

    private final MentoringProgressRepository repository;
    private final MentoringMapper mapper;

    public MentoringService(MentoringProgressRepository repository, MentoringMapper mapper) {
        this.repository = repository;
        this.mapper = mapper;
    }

    /** Upsert keyed by (engagement, roleTrack, moduleName, phase). */
    @Transactional
    public MentoringProgressResponse recordProgress(UUID engagementId,
                                                    MentoringProgressRequest request) {
        MentoringProgress progress = repository
                .findByEngagementIdAndRoleTrackAndModuleNameAndPhase(
                        engagementId, request.roleTrack(), request.moduleName(), request.phase())
                .map(existing -> {
                    existing.updateCompletion(request.completionPct());
                    return existing;
                })
                .orElseGet(() -> new MentoringProgress(
                        UUID.randomUUID(), engagementId, request.roleTrack(),
                        request.moduleName(), request.phase(), request.completionPct()));
        return mapper.toResponse(repository.save(progress));
    }

    @Transactional(readOnly = true)
    public List<MentoringProgressResponse> findByEngagement(UUID engagementId) {
        return repository.findByEngagementId(engagementId).stream()
                .map(mapper::toResponse)
                .toList();
    }
}
