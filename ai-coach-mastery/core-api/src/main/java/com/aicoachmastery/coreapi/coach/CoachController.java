package com.aicoachmastery.coreapi.coach;

import com.aicoachmastery.coreapi.coach.CoachDtos.CoachResponse;
import com.aicoachmastery.coreapi.coach.CoachDtos.CreateCoachRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.util.List;
import java.util.UUID;

/** REST API for coaches. Versioned under /api/v1. */
@RestController
@RequestMapping("/api/v1/coaches")
public class CoachController {

    private final CoachService service;

    public CoachController(CoachService service) {
        this.service = service;
    }

    @GetMapping
    public List<CoachResponse> list() {
        return service.findAll();
    }

    @GetMapping("/{id}")
    public CoachResponse get(@PathVariable UUID id) {
        return service.findById(id);
    }

    @PostMapping
    public ResponseEntity<CoachResponse> create(@Valid @RequestBody CreateCoachRequest request) {
        CoachResponse created = service.create(request);
        return ResponseEntity
                .created(URI.create("/api/v1/coaches/" + created.id()))
                .body(created);
    }
}
