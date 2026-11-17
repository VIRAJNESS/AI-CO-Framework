package com.aicoachmastery.coreapi.orchestration;

import com.aicoachmastery.coreapi.common.UpstreamServiceException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.Map;

/**
 * HTTP client for the Python ai-engine service. The base URL is 12-factor
 * configurable (AI_ENGINE_URL). All failures surface as
 * {@link UpstreamServiceException} so the orchestration layer maps them to 502
 * without mutating engagement state.
 */
@Component
public class AiEngineClient {

    private final RestClient restClient;

    public AiEngineClient(@Value("${app.ai-engine-url}") String baseUrl,
                          RestClient.Builder builder) {
        this.restClient = builder.baseUrl(baseUrl).build();
    }

    /** Result of an insight (diagnostic) call: provider used + insight text. */
    public record InsightResult(String provider, String insight) {
    }

    /** Result of a report generation call: storage key + locator. */
    public record ReportResult(String key, String locator, String format, long sizeBytes) {
    }

    /** Run the deterministic diagnostic/simulation for a stage prompt. */
    public InsightResult generateInsight(String prompt) {
        try {
            Map<String, Object> body = restClient.post()
                    .uri("/api/v1/coach/insights")
                    .body(Map.of("prompt", prompt))
                    .retrieve()
                    .body(Map.class);
            if (body == null || !body.containsKey("insight")) {
                throw new UpstreamServiceException("ai-engine returned an empty insight response");
            }
            return new InsightResult(
                    String.valueOf(body.get("provider")),
                    String.valueOf(body.get("insight")));
        } catch (RestClientException ex) {
            throw new UpstreamServiceException(
                    "ai-engine insight call failed: " + ex.getMessage(), ex);
        }
    }

    /** Generate a deliverable (pptx/docx/pdf) and return its storage locator. */
    public ReportResult generateReport(String title, String summary, String format) {
        try {
            Map<String, Object> body = restClient.post()
                    .uri("/api/v1/reports")
                    .body(Map.of("title", title, "summary", summary, "format", format))
                    .retrieve()
                    .body(Map.class);
            if (body == null || !body.containsKey("locator")) {
                throw new UpstreamServiceException("ai-engine returned an empty report response");
            }
            return new ReportResult(
                    String.valueOf(body.get("key")),
                    String.valueOf(body.get("locator")),
                    String.valueOf(body.get("format")),
                    ((Number) body.getOrDefault("size_bytes", 0)).longValue());
        } catch (RestClientException ex) {
            throw new UpstreamServiceException(
                    "ai-engine report generation failed: " + ex.getMessage(), ex);
        }
    }
}
