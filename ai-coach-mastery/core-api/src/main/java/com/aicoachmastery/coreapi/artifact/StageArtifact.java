package com.aicoachmastery.coreapi.artifact;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * Output of a single executed lifecycle stage: diagnostics JSON, optional live
 * demo state, and locators of the generated PPTX/DOCX deliverables.
 */
@Entity
@Table(name = "stage_artifacts")
public class StageArtifact {

    @Id
    private UUID id;

    @Column(name = "engagement_id", nullable = false)
    private UUID engagementId;

    @Column(name = "stage_number", nullable = false)
    private int stageNumber;

    @Column(name = "stage_name", nullable = false, length = 80)
    private String stageName;

    @Column(name = "input_payload_json", columnDefinition = "TEXT")
    private String inputPayloadJson;

    @Column(name = "diagnostic_output_json", columnDefinition = "TEXT")
    private String diagnosticOutputJson;

    @Column(name = "live_demo_state_json", columnDefinition = "TEXT")
    private String liveDemoStateJson;

    @Column(name = "pptx_file_url", length = 512)
    private String pptxFileUrl;

    @Column(name = "docx_file_url", length = 512)
    private String docxFileUrl;

    @Column(name = "generated_at", nullable = false)
    private OffsetDateTime generatedAt;

    protected StageArtifact() {
        // JPA
    }

    public StageArtifact(UUID id, UUID engagementId, int stageNumber, String stageName,
                         String inputPayloadJson, String diagnosticOutputJson,
                         String liveDemoStateJson, String pptxFileUrl, String docxFileUrl,
                         OffsetDateTime generatedAt) {
        this.id = id;
        this.engagementId = engagementId;
        this.stageNumber = stageNumber;
        this.stageName = stageName;
        this.inputPayloadJson = inputPayloadJson;
        this.diagnosticOutputJson = diagnosticOutputJson;
        this.liveDemoStateJson = liveDemoStateJson;
        this.pptxFileUrl = pptxFileUrl;
        this.docxFileUrl = docxFileUrl;
        this.generatedAt = generatedAt;
    }

    public UUID getId() {
        return id;
    }

    public UUID getEngagementId() {
        return engagementId;
    }

    public int getStageNumber() {
        return stageNumber;
    }

    public String getStageName() {
        return stageName;
    }

    public String getInputPayloadJson() {
        return inputPayloadJson;
    }

    public String getDiagnosticOutputJson() {
        return diagnosticOutputJson;
    }

    public String getLiveDemoStateJson() {
        return liveDemoStateJson;
    }

    public String getPptxFileUrl() {
        return pptxFileUrl;
    }

    public String getDocxFileUrl() {
        return docxFileUrl;
    }

    public OffsetDateTime getGeneratedAt() {
        return generatedAt;
    }
}
