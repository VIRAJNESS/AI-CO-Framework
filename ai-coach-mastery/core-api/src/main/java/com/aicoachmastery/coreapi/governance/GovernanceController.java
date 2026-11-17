package com.aicoachmastery.coreapi.governance;

import com.aicoachmastery.coreapi.engagement.EngagementService;
import com.aicoachmastery.coreapi.governance.GovernanceDtos.GateEvaluationRequest;
import com.aicoachmastery.coreapi.governance.GovernanceDtos.GateResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

/** Governance gate evaluations per engagement. */
@RestController
@RequestMapping("/api/v1/engagements/{id}/gates")
@Tag(name = "Governance Gates", description = "Record and inspect governance gate results")
public class GovernanceController {

    private final GovernanceService governanceService;
    private final EngagementService engagementService;

    public GovernanceController(GovernanceService governanceService,
                                EngagementService engagementService) {
        this.governanceService = governanceService;
        this.engagementService = engagementService;
    }

    @GetMapping
    @Operation(summary = "List governance gate results for an engagement")
    public List<GateResponse> list(@PathVariable UUID id) {
        engagementService.getEntity(id); // 404 if missing
        return governanceService.findByEngagement(id);
    }

    @PostMapping
    @Operation(summary = "Record (or re-record) a gate evaluation result")
    public GateResponse record(@PathVariable UUID id,
                               @Valid @RequestBody GateEvaluationRequest request) {
        engagementService.getEntity(id); // 404 if missing
        return governanceService.recordEvaluation(id, request);
    }
}
