package com.aicoachmastery.coreapi.common;

/**
 * Thrown when a downstream dependency (the ai-engine service) fails or is
 * unreachable. Mapped to HTTP 502 Bad Gateway.
 */
public class UpstreamServiceException extends RuntimeException {

    public UpstreamServiceException(String message, Throwable cause) {
        super(message, cause);
    }

    public UpstreamServiceException(String message) {
        super(message);
    }
}
