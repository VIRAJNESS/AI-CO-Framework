package com.aicoachmastery.coreapi.mentoring;

import com.aicoachmastery.coreapi.engagement.EngagementService;
import com.aicoachmastery.coreapi.mentoring.MentoringDtos.MentoringProgressRequest;
import com.aicoachmastery.coreapi.mentoring.MentoringDtos.MentoringProgressResponse;
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

/** Mentoring progress (see one / co-build one / lead one) per engagement. */
@RestController
@RequestMapping("/api/v1/engagements/{id}/mentoring")
@Tag(name = "Mentoring Progress", description = "Role-track mentoring module progress")
public class MentoringController {

    private final MentoringService mentoringService;
    private final EngagementService engagementService;

    public MentoringController(MentoringService mentoringService,
                               EngagementService engagementService) {
        this.mentoringService = mentoringService;
        this.engagementService = engagementService;
    }

    @GetMapping
    @Operation(summary = "List mentoring progress for an engagement")
    public List<MentoringProgressResponse> list(@PathVariable UUID id) {
        engagementService.getEntity(id); // 404 if missing
        return mentoringService.findByEngagement(id);
    }

    @PostMapping
    @Operation(summary = "Record (or update) mentoring module progress")
    public MentoringProgressResponse record(@PathVariable UUID id,
                                            @Valid @RequestBody MentoringProgressRequest request) {
        engagementService.getEntity(id); // 404 if missing
        return mentoringService.recordProgress(id, request);
    }
}
