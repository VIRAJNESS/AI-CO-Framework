package com.aicoachmastery.coreapi.coach;

import com.aicoachmastery.coreapi.coach.CoachDtos.CoachResponse;
import com.aicoachmastery.coreapi.coach.CoachDtos.CreateCoachRequest;
import com.aicoachmastery.coreapi.common.DuplicateResourceException;
import com.aicoachmastery.coreapi.common.ResourceNotFoundException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * Unit tests for CoachService: happy path, negative paths, and edge cases
 * (empty list, boundary-length fields, duplicate email race).
 */
@ExtendWith(MockitoExtension.class)
class CoachServiceTest {

    @Mock
    private CoachRepository repository;

    @InjectMocks
    private CoachService service;

    private Coach sampleCoach(UUID id) {
        return new Coach(id, "Ada Lovelace", "ada@aicoach.dev", "AI SDLC", OffsetDateTime.now());
    }

    // --- Happy paths ---------------------------------------------------------

    @Test
    void create_persistsAndReturnsResponse() {
        when(repository.existsByEmail("ada@aicoach.dev")).thenReturn(false);
        when(repository.save(any(Coach.class))).thenAnswer(inv -> inv.getArgument(0));

        CoachResponse response = service.create(
                new CreateCoachRequest("Ada Lovelace", "ada@aicoach.dev", "AI SDLC"));

        assertThat(response.id()).isNotNull();
        assertThat(response.email()).isEqualTo("ada@aicoach.dev");
        verify(repository).save(any(Coach.class));
    }

    @Test
    void findById_returnsCoach() {
        UUID id = UUID.randomUUID();
        when(repository.findById(id)).thenReturn(Optional.of(sampleCoach(id)));

        assertThat(service.findById(id).id()).isEqualTo(id);
    }

    // --- Negative paths ------------------------------------------------------

    @Test
    void findById_throwsNotFound_whenMissing() {
        UUID id = UUID.randomUUID();
        when(repository.findById(id)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.findById(id))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining(id.toString());
    }

    @Test
    void create_throwsConflict_whenEmailExists() {
        when(repository.existsByEmail("ada@aicoach.dev")).thenReturn(true);

        assertThatThrownBy(() -> service.create(
                new CreateCoachRequest("Ada", "ada@aicoach.dev", "AI SDLC")))
                .isInstanceOf(DuplicateResourceException.class);
        verify(repository, never()).save(any());
    }

    // --- Edge cases ----------------------------------------------------------

    @Test
    void findAll_returnsEmptyList_whenNoCoaches() {
        // Edge: empty repository must yield an empty list, never null.
        when(repository.findAll()).thenReturn(List.of());

        assertThat(service.findAll()).isEmpty();
    }

    @Test
    void create_acceptsBoundaryLengthName() {
        // Edge: name exactly at the 120-char column limit.
        String maxName = "N".repeat(120);
        when(repository.existsByEmail(any())).thenReturn(false);
        when(repository.save(any(Coach.class))).thenAnswer(inv -> inv.getArgument(0));

        CoachResponse response = service.create(
                new CreateCoachRequest(maxName, "edge@aicoach.dev", "Edge"));

        assertThat(response.name()).hasSize(120);
    }

    @Test
    void create_generatesUniqueIdsForEachCoach() {
        // Edge: consecutive creates must never reuse an ID.
        when(repository.existsByEmail(any())).thenReturn(false);
        when(repository.save(any(Coach.class))).thenAnswer(inv -> inv.getArgument(0));

        CoachResponse first = service.create(new CreateCoachRequest("A", "a@x.dev", "S"));
        CoachResponse second = service.create(new CreateCoachRequest("B", "b@x.dev", "S"));

        assertThat(first.id()).isNotEqualTo(second.id());
    }
}
