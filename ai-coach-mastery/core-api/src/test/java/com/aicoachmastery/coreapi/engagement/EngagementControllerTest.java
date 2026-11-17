package com.aicoachmastery.coreapi.engagement;

import com.aicoachmastery.coreapi.common.BusinessRuleException;
import com.aicoachmastery.coreapi.common.ResourceNotFoundException;
import com.aicoachmastery.coreapi.engagement.EngagementDtos.EngagementResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** Web-layer tests for the engagement endpoints. */
@WebMvcTest(EngagementController.class)
class EngagementControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private EngagementService service;

    private static final UUID ID = UUID.fromString("aaaaaaaa-0000-0000-0000-000000000001");

    private EngagementResponse sample(int stage) {
        return new EngagementResponse(ID, "Acme", "FinTech", DomainTrack.SDLC,
                stage, "Discovery & Audit", AdvisorTier.DIAGNOSTIC_SPRINT, OffsetDateTime.now());
    }

    // --- Happy paths ---------------------------------------------------------

    @Test
    void createEngagement_returns201() throws Exception {
        when(service.create(any())).thenReturn(sample(1));

        mockMvc.perform(post("/api/v1/engagements")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"clientName":"Acme","industry":"FinTech",
                                 "domainTrack":"SDLC","advisorTier":"DIAGNOSTIC_SPRINT"}
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.currentStage").value(1));
    }

    @Test
    void listEngagements_returns200() throws Exception {
        when(service.findAll()).thenReturn(List.of(sample(1)));

        mockMvc.perform(get("/api/v1/engagements"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].clientName").value("Acme"));
    }

    @Test
    void transition_returnsUpdatedStage() throws Exception {
        when(service.transitionStage(eq(ID), eq(2))).thenReturn(sample(2));

        mockMvc.perform(post("/api/v1/engagements/" + ID + "/stage-transitions")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"targetStage\":2}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.currentStage").value(2));
    }

    // --- Negative paths ------------------------------------------------------

    @Test
    void getEngagement_returns404_whenMissing() throws Exception {
        when(service.findById(ID)).thenThrow(new ResourceNotFoundException("missing"));

        mockMvc.perform(get("/api/v1/engagements/" + ID))
                .andExpect(status().isNotFound());
    }

    @Test
    void transition_skippingStages_returns409() throws Exception {
        when(service.transitionStage(eq(ID), eq(5)))
                .thenThrow(new BusinessRuleException("Cannot skip stages"));

        mockMvc.perform(post("/api/v1/engagements/" + ID + "/stage-transitions")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"targetStage\":5}"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.title").value("Business rule violation"));
    }

    // --- Edge cases ----------------------------------------------------------

    @Test
    void createEngagement_returns400_onUnknownEnum() throws Exception {
        // Edge: invalid enum literal must fail request parsing, not reach service.
        mockMvc.perform(post("/api/v1/engagements")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"clientName":"Acme","industry":"FinTech",
                                 "domainTrack":"NOT_A_TRACK","advisorTier":"DIAGNOSTIC_SPRINT"}
                                """))
                .andExpect(status().isBadRequest());
    }

    @Test
    void transition_returns400_onStageOutOfRange() throws Exception {
        // Edge: bean validation bounds (1..6) rejected at the web layer.
        mockMvc.perform(post("/api/v1/engagements/" + ID + "/stage-transitions")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"targetStage\":7}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void createEngagement_returns400_onBlankClientName() throws Exception {
        // Edge: whitespace-only client name fails @NotBlank.
        mockMvc.perform(post("/api/v1/engagements")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"clientName":"   ","industry":"FinTech",
                                 "domainTrack":"SDLC","advisorTier":"DIAGNOSTIC_SPRINT"}
                                """))
                .andExpect(status().isBadRequest());
    }

    @Test
    void deleteEngagement_returns204() throws Exception {
        mockMvc.perform(delete("/api/v1/engagements/" + ID))
                .andExpect(status().isNoContent());
    }
}
