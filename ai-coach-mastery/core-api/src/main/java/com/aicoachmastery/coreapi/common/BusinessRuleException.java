package com.aicoachmastery.coreapi.common;

/**
 * Thrown when an operation violates a domain rule (e.g., skipping lifecycle
 * stages or executing a stage with failing governance gates). Mapped to 409.
 */
public class BusinessRuleException extends RuntimeException {

    public BusinessRuleException(String message) {
        super(message);
    }
}
