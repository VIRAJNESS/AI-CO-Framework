# =============================================================================
# AI Coach Mastery — Root Makefile
# Local-first orchestration. Zero cloud keys required (LLM_PROVIDER=mock,
# STORAGE_PROVIDER=local by default).
# =============================================================================

COMPOSE := docker compose -f infra/local/docker-compose.yml --env-file .env

.DEFAULT_GOAL := help

.PHONY: help up down logs ps seed smoke test test-core test-ai test-frontend build-all clean env

help: ## Show this help
	@echo "AI Coach Mastery - available targets:"
	@echo "  make up          Start full local stack (postgres, redis, minio, services)"
	@echo "  make down        Stop stack and remove containers (volumes preserved)"
	@echo "  make seed        Load demo seed data into Postgres"
	@echo "  make test        Run all test suites (core-api, ai-engine, frontend)"
	@echo "  make build-all   Build all Docker images"
	@echo "  make logs        Tail logs from all services"
	@echo "  make ps          Show stack status"
	@echo "  make clean       Down + remove volumes (DESTROYS local data)"

env: ## Create .env from .env.example if missing
	@if not exist .env copy .env.example .env >nul 2>&1 || cp -n .env.example .env 2>/dev/null || true

up: env ## Start the full local stack
	$(COMPOSE) up -d --build
	@echo "Frontend:  http://localhost:4200"
	@echo "Core API:  http://localhost:8080/actuator/health"
	@echo "AI Engine: http://localhost:8000/health"
	@echo "MinIO UI:  http://localhost:9001 (minioadmin/minioadmin)"

down: ## Stop the stack (keeps volumes)
	$(COMPOSE) down

clean: ## Stop the stack and delete volumes (destroys local data)
	$(COMPOSE) down -v --remove-orphans

logs: ## Tail logs
	$(COMPOSE) logs -f --tail=100

ps: ## Stack status
	$(COMPOSE) ps

seed: ## Seed coaches (SQL) + generate showcase deliverables (stack must be up)
	$(COMPOSE) exec -T postgres psql -U aicoach -d aicoach -f /seed/seed.sql
	$(COMPOSE) exec -T ai-engine python seed_showcase.py
	@echo "Seed complete: coaches + 4 showcase engagements' deliverables."
	@echo "(Engagement rows auto-seed on core-api first startup when DB is empty.)"

smoke: ## Run end-to-end smoke tests against the running stack
	python scripts/smoke_test.py

build-all: env ## Build all service Docker images
	$(COMPOSE) build

test: test-core test-ai test-frontend ## Run every test suite

test-core: ## Run core-api (Maven) tests in a container
	docker run --rm -v "$(CURDIR)/core-api:/app" -w /app maven:3.9-eclipse-temurin-21 mvn -q test

test-ai: ## Run ai-engine (pytest) tests in a container
	docker build -t ai-coach-mastery/ai-engine-test --target test ai-engine
	docker run --rm ai-coach-mastery/ai-engine-test

test-frontend: ## Run frontend (Karma headless) tests in a container
	docker build -t ai-coach-mastery/frontend-test --target test frontend
	docker run --rm ai-coach-mastery/frontend-test
