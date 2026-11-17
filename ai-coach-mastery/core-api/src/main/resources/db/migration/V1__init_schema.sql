-- ============================================================================
-- V1 — AI Head Coach core schema (6-stage lifecycle + governance + mentoring)
-- Schema 'core' is created by the local Postgres init script / Flyway
-- createSchemas. All enums are enforced with CHECK constraints so the DB
-- stays portable across managed Postgres offerings.
-- ============================================================================

-- Coaches (retained from bootstrap — used by the dashboard roster)
CREATE TABLE IF NOT EXISTS coaches (
    id          UUID PRIMARY KEY,
    name        VARCHAR(120)  NOT NULL,
    email       VARCHAR(255)  NOT NULL UNIQUE,
    specialty   VARCHAR(160)  NOT NULL,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- Client engagements — the aggregate root of the 6-stage lifecycle
CREATE TABLE IF NOT EXISTS client_engagements (
    id            UUID PRIMARY KEY,
    client_name   VARCHAR(160) NOT NULL,
    industry      VARCHAR(120) NOT NULL,
    domain_track  VARCHAR(16)  NOT NULL
                  CHECK (domain_track IN ('SDLC', 'PDLC', 'STARTUP', 'LEGACY')),
    current_stage INT          NOT NULL DEFAULT 1
                  CHECK (current_stage BETWEEN 1 AND 6),
    advisor_tier  VARCHAR(32)  NOT NULL
                  CHECK (advisor_tier IN
                         ('DIAGNOSTIC_SPRINT', 'TRANSFORMATION_RETAINER', 'FRACTIONAL_HEAD_COACH')),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Stage artifacts — outputs of each executed lifecycle stage
CREATE TABLE IF NOT EXISTS stage_artifacts (
    id                     UUID PRIMARY KEY,
    engagement_id          UUID         NOT NULL
                           REFERENCES client_engagements (id) ON DELETE CASCADE,
    stage_number           INT          NOT NULL CHECK (stage_number BETWEEN 1 AND 6),
    stage_name             VARCHAR(80)  NOT NULL,
    input_payload_json     TEXT,
    diagnostic_output_json TEXT,
    live_demo_state_json   TEXT,
    pptx_file_url          VARCHAR(512),
    docx_file_url          VARCHAR(512),
    generated_at           TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_stage_artifacts_engagement
    ON stage_artifacts (engagement_id, stage_number);

-- Governance gates — quality/safety checks gating stage execution
CREATE TABLE IF NOT EXISTS governance_gates (
    id            UUID PRIMARY KEY,
    engagement_id UUID         NOT NULL
                  REFERENCES client_engagements (id) ON DELETE CASCADE,
    gate_name     VARCHAR(32)  NOT NULL
                  CHECK (gate_name IN
                         ('PII_REDACTION', 'DETERMINISM_THRESHOLD', 'SHADOW_PARITY',
                          'HUMAN_IN_LOOP', 'FINOPS_CAP')),
    status        VARCHAR(8)   NOT NULL CHECK (status IN ('PASS', 'WARN', 'FAIL')),
    score         DOUBLE PRECISION,
    notes         VARCHAR(2000),
    CONSTRAINT uq_gate_per_engagement UNIQUE (engagement_id, gate_name)
);

CREATE INDEX IF NOT EXISTS idx_governance_gates_engagement
    ON governance_gates (engagement_id);

-- Mentoring progress — see one / co-build one / lead one per role track
CREATE TABLE IF NOT EXISTS mentoring_progress (
    id             UUID PRIMARY KEY,
    engagement_id  UUID         NOT NULL
                   REFERENCES client_engagements (id) ON DELETE CASCADE,
    role_track     VARCHAR(24)  NOT NULL
                   CHECK (role_track IN
                          ('C_SUITE', 'ARCHITECT', 'ENGINEER', 'PRODUCT_MANAGER')),
    module_name    VARCHAR(160) NOT NULL,
    phase          VARCHAR(16)  NOT NULL
                   CHECK (phase IN ('SEE_ONE', 'CO_BUILD_ONE', 'LEAD_ONE')),
    completion_pct DOUBLE PRECISION NOT NULL DEFAULT 0
                   CHECK (completion_pct BETWEEN 0 AND 100),
    CONSTRAINT uq_mentoring_module UNIQUE (engagement_id, role_track, module_name, phase)
);

CREATE INDEX IF NOT EXISTS idx_mentoring_progress_engagement
    ON mentoring_progress (engagement_id);
