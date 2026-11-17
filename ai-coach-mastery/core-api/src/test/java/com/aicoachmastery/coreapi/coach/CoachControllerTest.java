package com.aicoachmastery.coreapi.coach;

import com.aicoachmastery.coreapi.coach.CoachDtos.CoachResponse;
import com.aicoachmastery.coreapi.common.ResourceNotFoundException;
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
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Web-layer tests: routing, serialization, validation and error mapping.
 */
@WebMvcTest(CoachController.class)
class CoachControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private CoachService service;

    private static final UUID ID = UUID.fromString("11111111-1111-1111-1111-111111111111");

    private CoachResponse sample() {
        return new CoachResponse(ID, "Ada Lovelace", "ada@aicoach.dev", "AI SDLC", OffsetDateTime.now());
    }

    // --- Happy paths ---------------------------------------------------------

    @Test
    void listCoaches_returns200WithBody() throws Exception {
        when(service.findAll()).thenReturn(List.of(sample()));

        mockMvc.perform(get("/api/v1/coaches"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].email").value("ada@aicoach.dev"));
    }

    @Test
    void createCoach_returns201WithLocation() throws Exception {
        when(service.create(any())).thenReturn(sample());

        mockMvc.perform(post("/api/v1/coaches")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"name":"Ada Lovelace","email":"ada@aicoach.dev","specialty":"AI SDLC"}
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(ID.toString()));
    }

    // --- Negative paths ------------------------------------------------------

    @Test
    void getCoach_returns404_whenMissing() throws Exception {
        when(service.findById(ID)).thenThrow(new ResourceNotFoundException("Coach not found: " + ID));

        mockMvc.perform(get("/api/v1/coaches/" + ID))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.title").value("Resource not found"));
    }

    @Test
    void createCoach_returns400_onInvalidEmail() throws Exception {
        mockMvc.perform(post("/api/v1/coaches")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"name":"Ada","email":"not-an-email","specialty":"AI"}
                                """))
                .andExpect(status().isBadRequest());
    }

    // --- Edge cases ----------------------------------------------------------

    @Test
    void createCoach_returns400_onBlankName() throws Exception {
        // Edge: whitespace-only name must fail @NotBlank.
        mockMvc.perform(post("/api/v1/coaches")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"name":"   ","email":"x@y.dev","specialty":"AI"}
                                """))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getCoach_returns400_onMalformedUuid() throws Exception {
        // Edge: non-UUID path variable should not reach the service layer.
        mockMvc.perform(get("/api/v1/coaches/not-a-uuid"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void createCoach_returns400_onEmptyBody() throws Exception {
        // Edge: empty JSON object misses all required fields.
        mockMvc.perform(post("/api/v1/coaches")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isBadRequest());
    }
}
