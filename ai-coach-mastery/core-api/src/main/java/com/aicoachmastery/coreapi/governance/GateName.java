package com.aicoachmastery.coreapi.governance;

/** Governance gates every stage execution is validated against. */
public enum GateName {
    PII_REDACTION,
    DETERMINISM_THRESHOLD,
    SHADOW_PARITY,
    HUMAN_IN_LOOP,
    FINOPS_CAP
}
