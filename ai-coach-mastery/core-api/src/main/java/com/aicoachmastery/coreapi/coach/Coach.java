package com.aicoachmastery.coreapi.coach;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * Coach aggregate root — a consultant delivering AI transformation coaching.
 * Maps to core.coaches (schema owned by Flyway migrations).
 */
@Entity
@Table(name = "coaches")
public class Coach {

    @Id
    private UUID id;

    @Column(nullable = false, length = 120)
    private String name;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false, length = 160)
    private String specialty;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    protected Coach() {
        // JPA requires a no-arg constructor
    }

    public Coach(UUID id, String name, String email, String specialty, OffsetDateTime createdAt) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.specialty = specialty;
        this.createdAt = createdAt;
    }

    public UUID getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getEmail() {
        return email;
    }

    public String getSpecialty() {
        return specialty;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }
}
