package com.aicoachmastery.coreapi.engagement;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * Aggregate root of the AI Head Coach lifecycle. Holds the client identity,
 * the chosen delivery track/tier and the current lifecycle stage (1..6).
 * Stage mutation goes through {@link #moveToStage(int)} so invariants hold.
 */
@Entity
@Table(name = "client_engagements")
public class ClientEngagement {

    @Id
    private UUID id;

    @Column(name = "client_name", nullable = false, length = 160)
    private String clientName;

    @Column(nullable = false, length = 120)
    private String industry;

    @Enumerated(EnumType.STRING)
    @Column(name = "domain_track", nullable = false, length = 16)
    private DomainTrack domainTrack;

    @Column(name = "current_stage", nullable = false)
    private int currentStage;

    @Enumerated(EnumType.STRING)
    @Column(name = "advisor_tier", nullable = false, length = 32)
    private AdvisorTier advisorTier;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    protected ClientEngagement() {
        // JPA
    }

    public ClientEngagement(UUID id, String clientName, String industry,
                            DomainTrack domainTrack, AdvisorTier advisorTier,
                            OffsetDateTime createdAt) {
        this.id = id;
        this.clientName = clientName;
        this.industry = industry;
        this.domainTrack = domainTrack;
        this.advisorTier = advisorTier;
        this.currentStage = Stage.MIN;
        this.createdAt = createdAt;
    }

    /** Guarded stage mutation — valid range enforced here as a final invariant. */
    public void moveToStage(int targetStage) {
        if (!Stage.isValid(targetStage)) {
            throw new IllegalArgumentException(
                    "Target stage must be between 1 and 6, got: " + targetStage);
        }
        this.currentStage = targetStage;
    }

    /** Advance one stage, capped at the final stage (6). */
    public void advanceStage() {
        if (currentStage < Stage.MAX) {
            currentStage++;
        }
    }

    public void updateDetails(String clientName, String industry,
                              DomainTrack domainTrack, AdvisorTier advisorTier) {
        this.clientName = clientName;
        this.industry = industry;
        this.domainTrack = domainTrack;
        this.advisorTier = advisorTier;
    }

    public UUID getId() {
        return id;
    }

    public String getClientName() {
        return clientName;
    }

    public String getIndustry() {
        return industry;
    }

    public DomainTrack getDomainTrack() {
        return domainTrack;
    }

    public int getCurrentStage() {
        return currentStage;
    }

    public AdvisorTier getAdvisorTier() {
        return advisorTier;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }
}
