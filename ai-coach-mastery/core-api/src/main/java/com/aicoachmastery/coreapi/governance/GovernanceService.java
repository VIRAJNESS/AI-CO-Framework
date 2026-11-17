package com.aicoachmastery.coreapi.governance;

import com.aicoachmastery.coreapi.common.BusinessRuleException;
import com.aicoachmastery.coreapi.governance.GovernanceDtos.GateEvaluationRequest;
import com.aicoachmastery.coreapi.governance.GovernanceDtos.GateResponse;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

/**
 * Governance gate use cases: record evaluations and enforce the execution
 * gate rule — a stage may only execute when no gate is in FAIL state.
 */
@Service
public class GovernanceService {

    private final GovernanceGateRepository repository;
    private final GovernanceMapper mapper;

    public GovernanceService(GovernanceGateRepository repository, GovernanceMapper mapper) {
        this.repository = repository;
        this.mapper = mapper;
    }

    /** Upsert: one row per (engagement, gateName); re-evaluation updates it. */
    @Transactional
    public GateResponse recordEvaluation(UUID engagementId, GateEvaluationRequest request) {
        GovernanceGate gate = repository
                .findByEngagementIdAndGateName(engagementId, request.gateName())
                .map(existing -> {
                    existing.evaluate(request.status(), request.score(), request.notes());
                    return existing;
                })
                .orElseGet(() -> new GovernanceGate(
                        UUID.randomUUID(), engagementId, request.gateName(),
                        request.status(), request.score(), request.notes()));
        return mapper.toResponse(repository.save(gate));
    }

    @Transactional(readOnly = true)
    public List<GateResponse> findByEngagement(UUID engagementId) {
        return repository.findByEngagementId(engagementId).stream()
                .map(mapper::toResponse)
                .toList();
    }

    /**
     * Enforce gating before stage execution.
     *
     * @return gates in WARN state (surfaced in the execution response)
     * @throws BusinessRuleException if any gate is FAILing
     */
    @Transactional(readOnly = true)
    public List<GateResponse> validateForExecution(UUID engagementId) {
        List<GovernanceGate> failing =
                repository.findByEngagementIdAndStatus(engagementId, GateStatus.FAIL);
        if (!failing.isEmpty()) {
            String names = failing.stream()
                    .map(gate -> gate.getGateName().name())
                    .sorted()
                    .reduce((a, b) -> a + ", " + b)
                    .orElse("");
            throw new BusinessRuleException(
                    "Stage execution blocked by failing governance gates: " + names);
        }
        return repository.findByEngagementIdAndStatus(engagementId, GateStatus.WARN).stream()
                .map(mapper::toResponse)
                .toList();
    }
}
