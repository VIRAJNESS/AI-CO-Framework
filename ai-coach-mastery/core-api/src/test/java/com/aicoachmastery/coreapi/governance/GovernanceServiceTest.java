package com.aicoachmastery.coreapi.governance;

import com.aicoachmastery.coreapi.common.BusinessRuleException;
import com.aicoachmastery.coreapi.governance.GovernanceDtos.GateEvaluationRequest;
import com.aicoachmastery.coreapi.governance.GovernanceDtos.GateResponse;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

/** GovernanceService tests: upsert semantics and execution gating. */
@ExtendWith(MockitoExtension.class)
class GovernanceServiceTest {

    @Mock
    private GovernanceGateRepository repository;

    @Spy
    private GovernanceMapper mapper = new GovernanceMapper();

    @InjectMocks
    private GovernanceService service;

    private final UUID engagementId = UUID.randomUUID();

    // --- Happy paths ---------------------------------------------------------

    @Test
    void recordEvaluation_createsNewGate() {
        when(repository.findByEngagementIdAndGateName(engagementId, GateName.PII_REDACTION))
                .thenReturn(Optional.empty());
        when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        GateResponse response = service.recordEvaluation(engagementId,
                new GateEvaluationRequest(GateName.PII_REDACTION, GateStatus.PASS, 0.99, "ok"));

        assertThat(response.gateName()).isEqualTo(GateName.PII_REDACTION);
        assertThat(response.status()).isEqualTo(GateStatus.PASS);
    }

    @Test
    void validateForExecution_passes_whenNoFailingGates() {
        when(repository.findByEngagementIdAndStatus(engagementId, GateStatus.FAIL))
                .thenReturn(List.of());
        when(repository.findByEngagementIdAndStatus(engagementId, GateStatus.WARN))
                .thenReturn(List.of());

        assertThat(service.validateForExecution(engagementId)).isEmpty();
    }

    // --- Negative path --------------------------------------------------------

    @Test
    void validateForExecution_blocks_whenGateFails() {
        when(repository.findByEngagementIdAndStatus(engagementId, GateStatus.FAIL))
                .thenReturn(List.of(new GovernanceGate(
                        UUID.randomUUID(), engagementId, GateName.FINOPS_CAP,
                        GateStatus.FAIL, 0.2, "budget exceeded")));

        assertThatThrownBy(() -> service.validateForExecution(engagementId))
                .isInstanceOf(BusinessRuleException.class)
                .hasMessageContaining("FINOPS_CAP");
    }

    // --- Edge cases -------------------------------------------------------------

    @Test
    void recordEvaluation_upsertsExistingGate_keepingIdentity() {
        // Edge: re-evaluating an existing gate must not create a second row.
        GovernanceGate existing = new GovernanceGate(
                UUID.randomUUID(), engagementId, GateName.DETERMINISM_THRESHOLD,
                GateStatus.WARN, 0.85, "initial");
        when(repository.findByEngagementIdAndGateName(engagementId, GateName.DETERMINISM_THRESHOLD))
                .thenReturn(Optional.of(existing));
        when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        GateResponse response = service.recordEvaluation(engagementId,
                new GateEvaluationRequest(
                        GateName.DETERMINISM_THRESHOLD, GateStatus.PASS, 0.96, "tuned"));

        assertThat(response.id()).isEqualTo(existing.getId()); // same row
        assertThat(response.status()).isEqualTo(GateStatus.PASS);
        assertThat(response.score()).isEqualTo(0.96);
    }

    @Test
    void validateForExecution_surfacesWarnings_withoutBlocking() {
        // Edge: WARN gates allow execution but must be reported.
        when(repository.findByEngagementIdAndStatus(engagementId, GateStatus.FAIL))
                .thenReturn(List.of());
        when(repository.findByEngagementIdAndStatus(engagementId, GateStatus.WARN))
                .thenReturn(List.of(new GovernanceGate(
                        UUID.randomUUID(), engagementId, GateName.SHADOW_PARITY,
                        GateStatus.WARN, 0.9, "parity drift")));

        List<GateResponse> warnings = service.validateForExecution(engagementId);

        assertThat(warnings).hasSize(1);
        assertThat(warnings.get(0).gateName()).isEqualTo(GateName.SHADOW_PARITY);
    }

    @Test
    void validateForExecution_listsAllFailingGatesInMessage() {
        // Edge: multiple failing gates must all be named for actionability.
        when(repository.findByEngagementIdAndStatus(engagementId, GateStatus.FAIL))
                .thenReturn(List.of(
                        new GovernanceGate(UUID.randomUUID(), engagementId,
                                GateName.PII_REDACTION, GateStatus.FAIL, null, null),
                        new GovernanceGate(UUID.randomUUID(), engagementId,
                                GateName.HUMAN_IN_LOOP, GateStatus.FAIL, null, null)));

        assertThatThrownBy(() -> service.validateForExecution(engagementId))
                .isInstanceOf(BusinessRuleException.class)
                .hasMessageContaining("HUMAN_IN_LOOP")
                .hasMessageContaining("PII_REDACTION");
    }

    @Test
    void recordEvaluation_acceptsNullScoreAndNotes() {
        // Edge: score/notes are optional (e.g., manual HUMAN_IN_LOOP sign-off).
        when(repository.findByEngagementIdAndGateName(engagementId, GateName.HUMAN_IN_LOOP))
                .thenReturn(Optional.empty());
        when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        GateResponse response = service.recordEvaluation(engagementId,
                new GateEvaluationRequest(GateName.HUMAN_IN_LOOP, GateStatus.PASS, null, null));

        assertThat(response.score()).isNull();
        assertThat(response.notes()).isNull();
    }
}
