package com.aicoachmastery.coreapi;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * AI Coach Mastery — Core domain API entry point.
 * Cloud-agnostic by design: all environment-specific configuration is injected
 * via 12-factor environment variables (see application.yml).
 */
@SpringBootApplication
public class CoreApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(CoreApiApplication.class, args);
    }
}
