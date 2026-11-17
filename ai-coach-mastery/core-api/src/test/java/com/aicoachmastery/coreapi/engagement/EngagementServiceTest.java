package com.aicoachmastery.coreapi.engagement;

import com.aicoachmastery.coreapi.common.BusinessRuleException;
import com.aicoachmastery.coreapi.common.ResourceNotFoundException;
import com.aicoachmastery.coreapi.engagement.EngagementDtos.CreateEngagementRequest;
import com.aicoachmastery.coreapi.engagement.EngagementDtos.EngagementResponse;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.OffsetDateTime;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

/**
 * EngagementService unit tests: creation defaults, transition rules
 * (happy, negative, edge cases).
 */
@ExtendWith(MockitoExtension.class)
class EngagementServiceTest {

    @Mock
    private ClientEngagementRepository repository;

    @Spy
    private EngagementMapper mapper = new EngagementMapper();

    @InjectMocks
    private EngagementService service;

    private ClientEngagement engagementAtStage(int stage) {
        ClientEngagement engagement = new ClientEngagement(
                UUID.randomUUID(), "Acme", "FinTech",
                DomainTrack.SDLC, AdvisorTier.DIAGNOSTIC_SPRINT, OffsetDateTime.now());
        engagement.moveToStage(stage);
        return engagement;
    }

    // --- Happy paths ---------------------------------------------------------

    @Test
    void create_startsAtStageOne() {
        when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        EngagementResponse response = service.create(new CreateEngagementRequest(
                "Acme", "FinTech", DomainTrack.SDLC, AdvisorTier.DIAGNOSTIC_SPRINT));

        assertThat(response.currentStage()).isEqualTo(1);
        assertThat(response.currentStageName()).isEqualTo("Discovery & Audit");
    }

    @Test
    void transition_forwardOneStage_succeeds() {
        ClientEngagement engagement = engagementAtStage(2);
        when(repository.findById(engagement.getId())).thenReturn(Optional.of(engagement));
        when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        EngagementResponse response = service.transitionStage(engagement.getId(), 3);

        assertThat(response.currentStage()).isEqualTo(3);
        assertThat(response.currentStageName()).isEqualTo("Pilot Design");
    }

    @Test
    void transition_backwardForRework_succeeds() {
        ClientEngagement engagement = engagementAtStage(4);
        when(repository.findById(engagement.getId())).thenReturn(Optional.of(engagement));
        when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        EngagementResponse response = service.transitionStage(engagement.getId(), 2);

        assertThat(response.currentStage()).isEqualTo(2);
    }

    // --- Negative paths ------------------------------------------------------

    @Test
    void transition_skippingStages_isRejected() {
        ClientEngagement engagement = engagementAtStage(1);
        when(repository.findById(engagement.getId())).thenReturn(Optional.of(engagement));

        assertThatThrownBy(() -> service.transitionStage(engagement.getId(), 4))
                .isInstanceOf(BusinessRuleException.class)
                .hasMessageContaining("skip");
    }

    @Test
    void transition_unknownEngagement_throws404() {
        UUID missing = UUID.randomUUID();
        when(repository.findById(missing)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.transitionStage(missing, 2))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    // --- Edge cases ----------------------------------------------------------

    @Test
    void transition_toSameStage_isRejected() {
        // Edge: no-op transitions are explicit conflicts, not silent successes.
        ClientEngagement engagement = engagementAtStage(3);
        when(repository.findById(engagement.getId())).thenReturn(Optional.of(engagement));

        assertThatThrownBy(() -> service.transitionStage(engagement.getId(), 3))
                .isInstanceOf(BusinessRuleException.class)
                .hasMessageContaining("already at stage");
    }

    @Test
    void transition_fromStage5To6_reachesFinalStage() {
        // Edge: upper boundary — final stage must be reachable.
        ClientEngagement engagement = engagementAtStage(5);
        when(repository.findById(engagement.getId())).thenReturn(Optional.of(engagement));
        when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        EngagementResponse response = service.transitionStage(engagement.getId(), 6);

        assertThat(response.currentStage()).isEqualTo(6);
        assertThat(response.currentStageName()).isEqualTo("Scale & Handoff");
    }

    @Test
    void transition_backToStage1FromStage6_isAllowed() {
        // Edge: maximal backward rework span (6 -> 1) is valid.
        ClientEngagement engagement = engagementAtStage(6);
        when(repository.findById(engagement.getId())).thenReturn(Optional.of(engagement));
        when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        EngagementResponse response = service.transitionStage(engagement.getId(), 1);

        assertThat(response.currentStage()).isEqualTo(1);
    }

    @Test
    void entityRejectsOutOfRangeStage() {
        // Edge: entity-level invariant guards even if DTO validation is bypassed.
        ClientEngagement engagement = engagementAtStage(1);

        assertThatThrownBy(() -> engagement.moveToStage(7))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> engagement.moveToStage(0))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
