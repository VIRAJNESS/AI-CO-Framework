"""Stage 3 — Domain Execution Blueprint.

Generates the tailored on-ground execution architecture for the selected
domain track. Each blueprint is a structured JSON of components with purpose,
agent roles, integration points and KPIs — ready to render as an architecture
board or feed into deliverable generation.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.engine.stage1_pitch import DomainTrack

router = APIRouter(prefix="/stage3", tags=["engine:stage3-blueprint"])


class BlueprintRequest(BaseModel):
    domain_track: DomainTrack = Field(alias="domainTrack")
    client_name: str = Field(alias="clientName", default="", max_length=160)

    model_config = {"populate_by_name": True}


_BLUEPRINTS: dict[DomainTrack, dict] = {
    DomainTrack.SDLC: {
        "theme": "Autonomous software delivery",
        "components": [
            {
                "name": "Claude/LLM SDK Workbench",
                "purpose": "Developer-facing agent workbench with prompt library, "
                           "evals and repo-aware context windows.",
                "agents": ["context-retriever", "code-synthesizer"],
                "integrations": ["Git provider", "IDE", "prompt registry"],
                "kpis": ["assisted-PR share", "prompt reuse rate"],
            },
            {
                "name": "Automated PR Review & Test Generation Agents",
                "purpose": "Agents review diffs for defects/policy and synthesize "
                           "missing unit/integration tests before human review.",
                "agents": ["pr-reviewer", "test-generator", "coverage-auditor"],
                "integrations": ["CI pipeline", "code host webhooks"],
                "kpis": ["review turnaround", "escaped-defect rate", "coverage delta"],
            },
            {
                "name": "AIOps Self-Healing Pipeline",
                "purpose": "Detects pipeline/runtime failures, diagnoses root cause "
                           "and executes approved remediation playbooks.",
                "agents": ["anomaly-detector", "root-cause-analyst", "remediator"],
                "integrations": ["observability stack", "incident tooling"],
                "kpis": ["MTTR", "auto-remediation rate", "alert precision"],
            },
        ],
    },
    DomainTrack.PDLC: {
        "theme": "Customer-signal-driven product development",
        "components": [
            {
                "name": "Customer Telemetry & Rage-Click Synthesis",
                "purpose": "Fuses product analytics, session replays and rage-click "
                           "signals into ranked friction themes.",
                "agents": ["telemetry-ingestor", "friction-synthesizer"],
                "integrations": ["product analytics", "session replay", "CRM"],
                "kpis": ["friction themes/week", "insight-to-backlog conversion"],
            },
            {
                "name": "Intent-Driven Digital Deflection",
                "purpose": "Routes inbound intents to self-serve resolution before "
                           "they become tickets, with graceful human handoff.",
                "agents": ["intent-router", "resolution-agent", "handoff-escalator"],
                "integrations": ["help center", "support desk", "knowledge base"],
                "kpis": ["deflection rate", "CSAT on deflected contacts"],
            },
            {
                "name": "Rapid Hypothesis Prototyping",
                "purpose": "Turns a PRD hypothesis into a testable prototype plus "
                           "experiment design within days.",
                "agents": ["prd-decomposer", "prototype-builder", "experiment-designer"],
                "integrations": ["design system", "feature flags", "experimentation"],
                "kpis": ["hypothesis cycle time", "experiment win rate"],
            },
        ],
    },
    DomainTrack.STARTUP: {
        "theme": "Lean agentic operating system",
        "components": [
            {
                "name": "Lean Agentic Pod Topology",
                "purpose": "2-pizza pods where each engineer operates a small fleet "
                           "of worker agents with shared evaluator standards.",
                "agents": ["pod-orchestrator", "worker-fleet", "shared-evaluator"],
                "integrations": ["task tracker", "chat ops"],
                "kpis": ["output per engineer", "agent utilisation"],
            },
            {
                "name": "Reusable RAG/Ontology Core",
                "purpose": "One canonical retrieval and ontology layer every feature "
                           "builds on — no per-team embedding silos.",
                "agents": ["ingestion-agent", "ontology-curator"],
                "integrations": ["vector store (pgvector)", "object storage"],
                "kpis": ["retrieval precision", "corpus freshness SLA"],
            },
            {
                "name": "Token FinOps & Unit-Economics Guardrails",
                "purpose": "Per-feature token budgets, live burn dashboards and "
                           "hard caps wired to the FINOPS_CAP governance gate.",
                "agents": ["budget-sentinel", "cost-attributor"],
                "integrations": ["LLM gateway", "billing exports"],
                "kpis": ["cost per solved task", "budget breach count"],
            },
        ],
    },
    DomainTrack.LEGACY: {
        "theme": "Safe, provable modernization",
        "components": [
            {
                "name": "Automated Codebase Archaeology",
                "purpose": "Agents map dead code, hidden coupling, business rules "
                           "and data lineage across the legacy estate.",
                "agents": ["code-cartographer", "rule-extractor", "lineage-tracer"],
                "integrations": ["VCS history", "DB schemas", "job schedulers"],
                "kpis": ["estate coverage %", "extracted-rule accuracy"],
            },
            {
                "name": "Semantic Equivalence Parity Harness",
                "purpose": "Shadow-runs modernized paths against legacy behaviour "
                           "and scores semantic parity before cutover.",
                "agents": ["traffic-replayer", "parity-scorer"],
                "integrations": ["shadow environment", "diff store"],
                "kpis": ["parity score", "cutover rollback rate"],
            },
            {
                "name": "Strangler-Fig API Wrapper Agents",
                "purpose": "Generates and maintains API facades over legacy modules "
                           "so new services can strangle old paths incrementally.",
                "agents": ["facade-generator", "contract-tester"],
                "integrations": ["API gateway", "service mesh"],
                "kpis": ["strangled-endpoint share", "facade defect rate"],
            },
        ],
    },
}


def build_blueprint(req: BlueprintRequest) -> dict:
    """Return the execution architecture for the selected track."""
    blueprint = _BLUEPRINTS[req.domain_track]
    return {
        "clientName": req.client_name or None,
        "domainTrack": req.domain_track.value,
        "theme": blueprint["theme"],
        "components": blueprint["components"],
        "governanceGates": [
            "PII_REDACTION", "DETERMINISM_THRESHOLD", "SHADOW_PARITY",
            "HUMAN_IN_LOOP", "FINOPS_CAP",
        ],
        "sharedFoundations": [
            "12-factor provider switches (LLM_PROVIDER / STORAGE_PROVIDER)",
            "pgvector retrieval layer",
            "artifact store for generated deliverables",
            "evaluator + shadow-diff scoring loop",
        ],
    }


@router.post("/domain-blueprint")
def domain_blueprint(req: BlueprintRequest) -> dict:
    """Tailored on-ground execution architecture for the chosen track."""
    return build_blueprint(req)
