package com.aicoachmastery.coreapi.artifact;

import com.aicoachmastery.coreapi.artifact.ArtifactDtos.StageArtifactResponse;
import com.aicoachmastery.coreapi.engagement.EngagementService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

/** Read access to generated stage artifacts of an engagement. */
@RestController
@RequestMapping("/api/v1/engagements/{id}/artifacts")
@Tag(name = "Stage Artifacts", description = "Generated diagnostics and deliverables per stage")
public class StageArtifactController {

    private final StageArtifactRepository repository;
    private final ArtifactMapper mapper;
    private final EngagementService engagementService;

    public StageArtifactController(StageArtifactRepository repository,
                                   ArtifactMapper mapper,
                                   EngagementService engagementService) {
        this.repository = repository;
        this.mapper = mapper;
        this.engagementService = engagementService;
    }

    @GetMapping
    @Operation(summary = "List stage artifacts for an engagement (ordered by stage)")
    public List<StageArtifactResponse> list(@PathVariable UUID id) {
        engagementService.getEntity(id); // 404 if missing
        return repository.findByEngagementIdOrderByStageNumberAscGeneratedAtDesc(id).stream()
                .map(mapper::toResponse)
                .toList();
    }
}
