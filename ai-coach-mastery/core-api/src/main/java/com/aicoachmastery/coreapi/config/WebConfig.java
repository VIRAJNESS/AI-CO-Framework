package com.aicoachmastery.coreapi.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * CORS configuration for local development — the Angular dev server runs on a
 * different origin (4200). Allowed origins are env-driven (12-factor) so prod
 * can lock this down without code changes.
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Value("${app.cors-allowed-origins:http://localhost:4200}")
    private String allowedOrigins;

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins(allowedOrigins.split(","))
                .allowedMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS");
    }
}
