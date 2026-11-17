package com.aicoachmastery.coreapi.engagement;

import com.aicoachmastery.coreapi.common.BusinessRuleException;
import com.aicoachmastery.coreapi.common.ResourceNotFoundException;
import com.aicoachmastery.coreapi.engagement.EngagementDtos.CreateEngagementRequest;
import com.aicoachmastery.coreapi.engagement.EngagementDtos.EngagementResponse;
import com.aicoachmastery.coreapi.engagement.EngagementDtos.UpdateEngagementRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

/**
 * Engagement use cases: CRUD plus the stage-transition governance rule set.
 *
 * Transition rules:
 *  - forward moves advance exactly one stage at a time (no skipping);
 *  - backward moves (rework) are allowed to any earlier stage;
 *  - target must be within 1..6 (validated at DTO and entity level too).
 */
@Service
public class EngagementService {

    private final ClientEngagementRepository repository;
    private final EngagementMapper mapper;

    public EngagementService(ClientEngagementRepository repository, EngagementMapper mapper) {
        this.repository = repository;
        this.mapper = mapper;
    }

    @Transactional
    public EngagementResponse create(CreateEngagementRequest request) {
        ClientEngagement engagement = new ClientEngagement(
                UUID.randomUUID(),
                request.clientName(),
                request.industry(),
                request.domainTrack(),
                request.advisorTier(),
                OffsetDateTime.now());
        return mapper.toResponse(repository.save(engagement));
    }

    @Transactional(readOnly = true)
    public List<EngagementResponse> findAll() {
        return repository.findAll().stream().map(mapper::toResponse).toList();
    }

    @Transactional(readOnly = true)
    public EngagementResponse findById(UUID id) {
        return mapper.toResponse(getEntity(id));
    }

    @Transactional
    public EngagementResponse update(UUID id, UpdateEngagementRequest request) {
        ClientEngagement engagement = getEntity(id);
        engagement.updateDetails(
                request.clientName(), request.industry(),
                request.domainTrack(), request.advisorTier());
        return mapper.toResponse(repository.save(engagement));
    }

    @Transactional
    public void delete(UUID id) {
        if (!repository.existsById(id)) {
            throw new ResourceNotFoundException("Engagement not found: " + id);
        }
        repository.deleteById(id);
    }

    /** Apply the transition rules and persist the stage move. */
    @Transactional
    public EngagementResponse transitionStage(UUID id, int targetStage) {
        ClientEngagement engagement = getEntity(id);
        int current = engagement.getCurrentStage();

        if (targetStage == current) {
            throw new BusinessRuleException(
                    "Engagement is already at stage " + current);
        }
        if (targetStage > current + 1) {
            throw new BusinessRuleException(
                    "Cannot skip stages: current=" + current + ", requested=" + targetStage
                    + ". Forward transitions advance exactly one stage.");
        }
        engagement.moveToStage(targetStage);
        return mapper.toResponse(repository.save(engagement));
    }

    /** Internal accessor used by sibling services (orchestration). */
    @Transactional(readOnly = true)
    public ClientEngagement getEntity(UUID id) {
        return repository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Engagement not found: " + id));
    }
}
