package com.aicoachmastery.coreapi.common;

/** Thrown when creating a resource that violates a uniqueness rule. Mapped to HTTP 409. */
public class DuplicateResourceException extends RuntimeException {

    public DuplicateResourceException(String message) {
        super(message);
    }
}
