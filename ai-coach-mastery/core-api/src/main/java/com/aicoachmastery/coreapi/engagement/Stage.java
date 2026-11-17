package com.aicoachmastery.coreapi.engagement;

/**
 * The AI Head Coach 6-stage lifecycle. Stage numbers are stable identifiers
 * (persisted); display names are the canonical coaching vocabulary.
 */
public enum Stage {
    DISCOVERY_AUDIT(1, "Discovery & Audit"),
    DIAGNOSTIC_BASELINE(2, "Diagnostic & Baseline"),
    PILOT_DESIGN(3, "Pilot Design"),
    EXECUTION_COACHING(4, "Execution & Coaching"),
    MEASUREMENT_ROI(5, "Measurement & ROI"),
    SCALE_HANDOFF(6, "Scale & Handoff");

    public static final int MIN = 1;
    public static final int MAX = 6;

    private final int number;
    private final String displayName;

    Stage(int number, String displayName) {
        this.number = number;
        this.displayName = displayName;
    }

    public int number() {
        return number;
    }

    public String displayName() {
        return displayName;
    }

    /** Resolve a stage by its 1..6 number. */
    public static Stage of(int number) {
        for (Stage stage : values()) {
            if (stage.number == number) {
                return stage;
            }
        }
        throw new IllegalArgumentException("Stage number must be between 1 and 6, got: " + number);
    }

    public static boolean isValid(int number) {
        return number >= MIN && number <= MAX;
    }
}
