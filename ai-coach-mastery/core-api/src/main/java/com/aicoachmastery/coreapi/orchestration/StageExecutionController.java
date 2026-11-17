package com.aicoachmastery.coreapi.orchestration;

import com.aicoachmastery.coreapi.orchestration.StageExecutionDtos.ExecuteStageRequest;
import com.aicoachmastery.coreapi.orchestration.StageExecutionDtos.ExecuteStageResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

/**
 * Proxy orchestration endpoint: validates governance gates, delegates
 * diagnostics + PPTX/DOCX generation to the Python ai-engine, persists the
 * resulting artifact and returns the unified execution JSON.
 */
@RestController
@RequestMapping("/api/v1/engagements/{id}/stages")
@Tag(name = "Stage Execution", description = "Governed execution of lifecycle stages")
public class StageExecutionController {

    private final StageExecutionService service;

    public StageExecutionController(StageExecutionService service) {
        this.service = service;
    }

    @PostMapping("/{stageNum}/execute")
    @Operation(summary = "Execute a lifecycle stage",
            description = "Validates governance gates (FAIL blocks with 409), calls the "
                    + "ai-engine for diagnostics and deliverable generation, persists the "
                    + "stage artifact, auto-advances the engagement, and returns unified JSON. "
                    + "Upstream failures return 502 without mutating state.")
    public ExecuteStageResponse execute(@PathVariable UUID id,
                                        @PathVariable int stageNum,
                                        @Valid @RequestBody(required = false)
                                        ExecuteStageRequest request) {
        return service.execute(id, stageNum, request);
    }
}
