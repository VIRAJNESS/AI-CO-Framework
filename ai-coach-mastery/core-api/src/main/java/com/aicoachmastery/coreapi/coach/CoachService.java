package com.aicoachmastery.coreapi.coach;

import com.aicoachmastery.coreapi.coach.CoachDtos.CoachResponse;
import com.aicoachmastery.coreapi.coach.CoachDtos.CreateCoachRequest;
import com.aicoachmastery.coreapi.common.DuplicateResourceException;
import com.aicoachmastery.coreapi.common.ResourceNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

/**
 * Application service for Coach use cases. Keeps the controller thin and the
 * domain rules (e.g., unique email) in one place.
 */
@Service
public class CoachService {

    private final CoachRepository repository;

    public CoachService(CoachRepository repository) {
        this.repository = repository;
    }

    @Transactional(readOnly = true)
    public List<CoachResponse> findAll() {
        return repository.findAll().stream()
                .map(CoachResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public CoachResponse findById(UUID id) {
        return repository.findById(id)
                .map(CoachResponse::from)
                .orElseThrow(() -> new ResourceNotFoundException("Coach not found: " + id));
    }

    @Transactional
    public CoachResponse create(CreateCoachRequest request) {
        // Business rule: email must be unique across coaches.
        if (repository.existsByEmail(request.email())) {
            throw new DuplicateResourceException("Coach email already registered: " + request.email());
        }
        Coach coach = new Coach(
                UUID.randomUUID(),
                request.name(),
                request.email(),
                request.specialty(),
                OffsetDateTime.now());
        return CoachResponse.from(repository.save(coach));
    }
}
