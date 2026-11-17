package com.aicoachmastery.coreapi.coach;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.time.OffsetDateTime;
import java.util.UUID;

/** Request/response DTOs for the Coach API (records keep them immutable). */
public final class CoachDtos {

    private CoachDtos() {
        // utility holder — no instances
    }

    /** Inbound payload for creating a coach. Bean Validation enforced at the controller. */
    public record CreateCoachRequest(
            @NotBlank @Size(max = 120) String name,
            @NotBlank @Email @Size(max = 255) String email,
            @NotBlank @Size(max = 160) String specialty) {
    }

    /** Outbound representation of a coach. */
    public record CoachResponse(
            UUID id,
            String name,
            String email,
            String specialty,
            OffsetDateTime createdAt) {

        static CoachResponse from(Coach coach) {
            return new CoachResponse(
                    coach.getId(),
                    coach.getName(),
                    coach.getEmail(),
                    coach.getSpecialty(),
                    coach.getCreatedAt());
        }
    }
}
