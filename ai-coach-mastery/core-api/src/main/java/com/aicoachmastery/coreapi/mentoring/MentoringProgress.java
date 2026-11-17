package com.aicoachmastery.coreapi.mentoring;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.util.UUID;

/**
 * Progress of one mentoring module for a role track within an engagement.
 * Unique per (engagement, roleTrack, moduleName, phase).
 */
@Entity
@Table(name = "mentoring_progress")
public class MentoringProgress {

    @Id
    private UUID id;

    @Column(name = "engagement_id", nullable = false)
    private UUID engagementId;

    @Enumerated(EnumType.STRING)
    @Column(name = "role_track", nullable = false, length = 24)
    private RoleTrack roleTrack;

    @Column(name = "module_name", nullable = false, length = 160)
    private String moduleName;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 16)
    private MentoringPhase phase;

    @Column(name = "completion_pct", nullable = false)
    private double completionPct;

    protected MentoringProgress() {
        // JPA
    }

    public MentoringProgress(UUID id, UUID engagementId, RoleTrack roleTrack,
                             String moduleName, MentoringPhase phase, double completionPct) {
        this.id = id;
        this.engagementId = engagementId;
        this.roleTrack = roleTrack;
        this.moduleName = moduleName;
        this.phase = phase;
        updateCompletion(completionPct);
    }

    /** Update completion percentage, enforcing the 0..100 invariant. */
    public void updateCompletion(double completionPct) {
        if (completionPct < 0 || completionPct > 100) {
            throw new IllegalArgumentException(
                    "completionPct must be between 0 and 100, got: " + completionPct);
        }
        this.completionPct = completionPct;
    }

    public UUID getId() {
        return id;
    }

    public UUID getEngagementId() {
        return engagementId;
    }

    public RoleTrack getRoleTrack() {
        return roleTrack;
    }

    public String getModuleName() {
        return moduleName;
    }

    public MentoringPhase getPhase() {
        return phase;
    }

    public double getCompletionPct() {
        return completionPct;
    }
}
