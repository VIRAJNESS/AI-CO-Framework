package com.aicoachmastery.coreapi.governance;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.util.UUID;

/**
 * A single governance gate evaluation for an engagement. One row per
 * (engagement, gateName) — re-evaluations update status/score/notes in place.
 */
@Entity
@Table(name = "governance_gates")
public class GovernanceGate {

    @Id
    private UUID id;

    @Column(name = "engagement_id", nullable = false)
    private UUID engagementId;

    @Enumerated(EnumType.STRING)
    @Column(name = "gate_name", nullable = false, length = 32)
    private GateName gateName;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 8)
    private GateStatus status;

    @Column
    private Double score;

    @Column(length = 2000)
    private String notes;

    protected GovernanceGate() {
        // JPA
    }

    public GovernanceGate(UUID id, UUID engagementId, GateName gateName,
                          GateStatus status, Double score, String notes) {
        this.id = id;
        this.engagementId = engagementId;
        this.gateName = gateName;
        this.status = status;
        this.score = score;
        this.notes = notes;
    }

    /** Re-evaluate the gate — updates result fields, identity stays stable. */
    public void evaluate(GateStatus status, Double score, String notes) {
        this.status = status;
        this.score = score;
        this.notes = notes;
    }

    public UUID getId() {
        return id;
    }

    public UUID getEngagementId() {
        return engagementId;
    }

    public GateName getGateName() {
        return gateName;
    }

    public GateStatus getStatus() {
        return status;
    }

    public Double getScore() {
        return score;
    }

    public String getNotes() {
        return notes;
    }
}
