package com.aicoachmastery.coreapi.orchestration;

import com.aicoachmastery.coreapi.artifact.ArtifactDtos.StageArtifactResponse;
import com.aicoachmastery.coreapi.common.BusinessRuleException;
import com.aicoachmastery.coreapi.common.UpstreamServiceException;
import com.aicoachmastery.coreapi.orchestration.StageExecutionDtos.ExecuteStageResponse;
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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** Web-layer tests for the stage execution orchestration endpoint. */
@WebMvcTest(StageExecutionController.class)
class StageExecutionControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private StageExecutionService service;

    private static final UUID ID = UUID.fromString("aaaaaaaa-0000-0000-0000-000000000001");

    private ExecuteStageResponse sampleResponse() {
        StageArtifactResponse artifact = new StageArtifactResponse(
                UUID.randomUUID(), ID, 1, "Discovery & Audit",
                null, "{\"provider\":\"mock\"}", null,
                "/data/artifacts/report.pptx", "/data/artifacts/report.docx",
                OffsetDateTime.now());
        return new ExecuteStageResponse(ID, 1, "Discovery & Audit", 2, "mock",
                List.of(), artifact);
    }

    // --- Happy path -------------------------------------------------------------

    @Test
    void execute_returnsUnifiedJson() throws Exception {
        when(service.execute(eq(ID), eq(1), any())).thenReturn(sampleResponse());

        mockMvc.perform(post("/api/v1/engagements/" + ID + "/stages/1/execute")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"inputPayloadJson\":\"{}\",\"notes\":\"kickoff\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.executedStage").value(1))
                .andExpect(jsonPath("$.newCurrentStage").value(2))
                .andExpect(jsonPath("$.llmProvider").value("mock"))
                .andExpect(jsonPath("$.artifact.pptxFileUrl").value("/data/artifacts/report.pptx"))
                .andExpect(jsonPath("$.artifact.docxFileUrl").value("/data/artifacts/report.docx"));
    }

    // --- Negative paths -----------------------------------------------------------

    @Test
    void execute_governanceFailure_returns409() throws Exception {
        when(service.execute(eq(ID), eq(1), any()))
                .thenThrow(new BusinessRuleException("blocked by failing governance gates"));

        mockMvc.perform(post("/api/v1/engagements/" + ID + "/stages/1/execute")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isConflict());
    }

    @Test
    void execute_upstreamFailure_returns502() throws Exception {
        when(service.execute(eq(ID), eq(1), any()))
                .thenThrow(new UpstreamServiceException("ai-engine unreachable"));

        mockMvc.perform(post("/api/v1/engagements/" + ID + "/stages/1/execute")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isBadGateway())
                .andExpect(jsonPath("$.title").value("Upstream service failure"));
    }

    // --- Edge cases -----------------------------------------------------------------

    @Test
    void execute_withoutBody_isAccepted() throws Exception {
        // Edge: request body is optional for the execute endpoint.
        when(service.execute(eq(ID), eq(1), any())).thenReturn(sampleResponse());

        mockMvc.perform(post("/api/v1/engagements/" + ID + "/stages/1/execute"))
                .andExpect(status().isOk());
    }

    @Test
    void execute_malformedUuid_returns400() throws Exception {
        // Edge: non-UUID path segment rejected before service invocation.
        mockMvc.perform(post("/api/v1/engagements/not-a-uuid/stages/1/execute"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void execute_nonNumericStage_returns400() throws Exception {
        // Edge: stage path variable must be an int.
        mockMvc.perform(post("/api/v1/engagements/" + ID + "/stages/abc/execute"))
                .andExpect(status().isBadRequest());
    }
}
