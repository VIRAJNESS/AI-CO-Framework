-- ============================================================================
-- AI Coach Mastery — Postgres bootstrap (runs once on first container start)
-- Creates pgvector extension and per-service schemas.
--   core : owned by Flyway (core-api / Spring Boot)
--   ai   : owned by SQLAlchemy (ai-engine / FastAPI)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS ai;

GRANT ALL ON SCHEMA core TO aicoach;
GRANT ALL ON SCHEMA ai TO aicoach;
