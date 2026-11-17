package com.aicoachmastery.coreapi.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** OpenAPI metadata — Swagger UI is served at /swagger-ui.html (springdoc). */
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI apiInfo() {
        return new OpenAPI().info(new Info()
                .title("AI Coach Mastery — Core API")
                .version("0.1.0")
                .description("AI Head Coach 6-stage lifecycle: engagements, stage artifacts, "
                        + "governance gates, mentoring progress, and governed stage execution "
                        + "orchestrated against the ai-engine service."));
    }
}
