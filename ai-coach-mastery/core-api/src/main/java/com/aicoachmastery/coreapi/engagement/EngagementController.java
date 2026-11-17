package com.aicoachmastery.coreapi.engagement;

import com.aicoachmastery.coreapi.engagement.EngagementDtos.CreateEngagementRequest;
import com.aicoachmastery.coreapi.engagement.EngagementDtos.EngagementResponse;
import com.aicoachmastery.coreapi.engagement.EngagementDtos.StageTransitionRequest;
import com.aicoachmastery.coreapi.engagement.EngagementDtos.UpdateEngagementRequest;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.util.List;
import java.util.UUID;

/** CRUD + stage transitions for client engagements. */
@RestController
@RequestMapping("/api/v1/engagements")
@Tag(name = "Engagements", description = "Client engagement lifecycle management")
public class EngagementController {

    private final EngagementService service;

    public EngagementController(EngagementService service) {
        this.service = service;
    }

    @PostMapping
    @Operation(summary = "Create an engagement (starts at stage 1)")
    public ResponseEntity<EngagementResponse> create(
            @Valid @RequestBody CreateEngagementRequest request) {
        EngagementResponse created = service.create(request);
        return ResponseEntity
                .created(URI.create("/api/v1/engagements/" + created.id()))
                .body(created);
    }

    @GetMapping
    @Operation(summary = "List all engagements")
    public List<EngagementResponse> list() {
        return service.findAll();
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get one engagement")
    public EngagementResponse get(@PathVariable UUID id) {
        return service.findById(id);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update engagement details (stage excluded — use transitions)")
    public EngagementResponse update(@PathVariable UUID id,
                                     @Valid @RequestBody UpdateEngagementRequest request) {
        return service.update(id, request);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete an engagement and all dependent records")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        service.delete(id);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/{id}/stage-transitions")
    @Operation(summary = "Transition lifecycle stage (forward one step or backward for rework)")
    public EngagementResponse transition(@PathVariable UUID id,
                                         @Valid @RequestBody StageTransitionRequest request) {
        return service.transitionStage(id, request.targetStage());
    }
}
