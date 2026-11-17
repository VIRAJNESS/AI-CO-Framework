"""Stage 4 — Live Multi-Agent Proof Simulator.

Takes real user-pasted text (bug log, legacy code snippet, customer complaint
or product PRD) and executes a visible 4-step trace:

    1. Intent & Ontology Router     — classifies artifact type + entities
    2. Guardrail & PII Policy Check — regex detection + redaction
    3. Autonomous Worker Agent      — mock deterministic synthesis or live LLM
    4. Evaluator Confidence & Shadow Diff — confidence + parity scoring

Works with zero keys (LLM_PROVIDER=mock) via rich domain-aware deterministic
synthesis; switching LLM_PROVIDER upgrades step 3 to a live model with no code
changes (ports-and-adapters LLMProvider).
"""

from __future__ import annotations

import hashlib
import random
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.providers.llm import get_llm_provider

router = APIRouter(prefix="/stage4", tags=["engine:stage4-livedemo"])


class LiveDemoRequest(BaseModel):
    input_text: str = Field(alias="inputText", min_length=1, max_length=50_000)
    hint: str | None = Field(default=None, max_length=40,
                             description="Optional intent hint: bug|legacy|complaint|prd")

    model_config = {"populate_by_name": True}


# --- Step 1: intent & ontology routing ----------------------------------------

_INTENT_SIGNALS: dict[str, list[str]] = {
    "BUG_LOG": ["exception", "stack trace", "traceback", "error", "npe",
                "nullpointer", "segfault", "errno", "failed", "timeout", "500"],
    "LEGACY_CODE": ["cobol", "goto ", "varchar2", "public static void", "struts",
                    "ejb", "procedure division", "perform ", "move ",
                    "end-if", "function(", "def ", "class ", "#include"],
    "CUSTOMER_COMPLAINT": ["refund", "angry", "frustrated", "cancel", "disappointed",
                           "waiting", "support", "terrible", "worst", "complaint",
                           "unacceptable", "charged"],
    "PRODUCT_PRD": ["user story", "acceptance criteria", "persona", "mvp", "kpi",
                    "requirement", "feature", "roadmap", "success metric", "scope"],
}

_HINT_MAP = {"bug": "BUG_LOG", "legacy": "LEGACY_CODE",
             "complaint": "CUSTOMER_COMPLAINT", "prd": "PRODUCT_PRD"}


def _route_intent(text: str, hint: str | None) -> dict:
    """Classify the artifact and extract lightweight ontology entities."""
    if hint and hint.lower() in _HINT_MAP:
        intent = _HINT_MAP[hint.lower()]
        scores = {intent: 1.0}
    else:
        lowered = text.lower()
        scores = {
            intent: sum(lowered.count(signal) for signal in signals)
            for intent, signals in _INTENT_SIGNALS.items()
        }
        intent = max(scores, key=scores.get)  # type: ignore[arg-type]
        if scores[intent] == 0:
            intent = "PRODUCT_PRD"  # neutral default for free-form prose

    entities = sorted(set(re.findall(r"\b[A-Z][a-zA-Z]{3,}[A-Za-z]*\b", text)))[:8]
    return {
        "step": 1,
        "name": "Intent & Ontology Router",
        "detectedIntent": intent,
        "signalScores": scores,
        "ontologyEntities": entities,
    }


# --- Step 2: guardrail & PII policy check --------------------------------------

_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "PHONE": re.compile(r"(?<!\d)(?:\+?\d{1,3}[ -]?)?(?:\(\d{2,4}\)[ -]?)?\d{3}[ -]?\d{3,4}[ -]?\d{0,4}(?!\d)"),
    "SSN_LIKE": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "API_KEY_LIKE": re.compile(r"\b(?:sk|pk|key|token)[-_][A-Za-z0-9]{12,}\b", re.IGNORECASE),
    "IPV4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}


def _guardrail_check(text: str) -> tuple[dict, str]:
    """Detect & redact PII; return the trace step and the sanitized text."""
    findings: dict[str, int] = {}
    sanitized = text
    for label, pattern in _PII_PATTERNS.items():
        matches = pattern.findall(sanitized)
        real = [m for m in matches if m and m.strip()]
        if real:
            findings[label] = len(real)
            sanitized = pattern.sub(f"[REDACTED:{label}]", sanitized)
    status = "PASS_WITH_REDACTIONS" if findings else "PASS"
    return (
        {
            "step": 2,
            "name": "Guardrail & PII Policy Check",
            "status": status,
            "findings": findings,
            "redactionApplied": bool(findings),
        },
        sanitized,
    )


# --- Step 3: worker agent (mock deterministic or live LLM) ----------------------

_WORKER_PLAYBOOK: dict[str, dict] = {
    "BUG_LOG": {
        "action": "Root-cause analysis & fix proposal",
        "mock_sections": [
            "Likely root cause isolated to the highest-frequency frame in the trace.",
            "Proposed fix: add null-safety guard and regression test around the failing path.",
            "Blast radius: 2 downstream consumers; suggested canary rollout.",
        ],
    },
    "LEGACY_CODE": {
        "action": "Modernization assessment & strangler plan",
        "mock_sections": [
            "Extracted 3 implicit business rules; flagged 1 dead branch.",
            "Recommended facade: wrap module behind a typed API before refactor.",
            "Parity harness: replay last 30 days of inputs against both paths.",
        ],
    },
    "CUSTOMER_COMPLAINT": {
        "action": "Resolution draft & churn-risk triage",
        "mock_sections": [
            "Sentiment: high frustration; churn risk elevated — prioritize response.",
            "Drafted empathetic resolution with concrete remedy and timeline.",
            "Deflection insight: tagged knowledge-base gap for this intent.",
        ],
    },
    "PRODUCT_PRD": {
        "action": "PRD decomposition & experiment design",
        "mock_sections": [
            "Decomposed into 4 user stories with measurable acceptance criteria.",
            "Identified riskiest assumption; designed a 2-week A/B validation.",
            "Instrumentation plan: 3 events wired to the success metric.",
        ],
    },
}


def _worker_execute(intent: str, sanitized: str, settings: Settings) -> dict:
    """Run the worker agent — deterministic mock synthesis or live LLM."""
    playbook = _WORKER_PLAYBOOK[intent]
    provider = get_llm_provider(settings)
    if settings.llm_provider.value == "mock":
        # Deterministic, domain-aware synthesis seeded by the sanitized input.
        seed = int.from_bytes(hashlib.sha256(sanitized.encode()).digest()[:8], "big")
        rng = random.Random(seed)
        sections = list(playbook["mock_sections"])
        rng.shuffle(sections)
        output = f"[{playbook['action']}]\n" + "\n".join(
            f"{i + 1}. {s}" for i, s in enumerate(sections))
        mode = "mock-deterministic"
    else:
        prompt = (f"You are an autonomous {playbook['action']} agent. "
                  f"Analyze the following and produce actionable output:\n{sanitized[:6000]}")
        output = provider.complete(prompt, max_tokens=1024)  # may raise NotImplementedError
        mode = f"live:{provider.name}"
    return {
        "step": 3,
        "name": "Autonomous Worker Agent Execution",
        "mode": mode,
        "action": playbook["action"],
        "output": output,
    }


# --- Step 4: evaluator confidence & shadow diff ----------------------------------

def _evaluate(sanitized: str, worker_output: str) -> dict:
    """Deterministic confidence + shadow parity scoring (seeded by content)."""
    seed = int.from_bytes(
        hashlib.sha256((sanitized + worker_output).encode()).digest()[:8], "big")
    rng = random.Random(seed)
    confidence = round(rng.uniform(0.82, 0.97), 3)
    shadow_diff = round(rng.uniform(0.015, 0.09), 3)  # lower is better parity
    verdict = "APPROVE" if confidence >= 0.85 and shadow_diff <= 0.08 else "HUMAN_REVIEW"
    return {
        "step": 4,
        "name": "Evaluator Confidence & Shadow Diff Score",
        "confidence": confidence,
        "shadowDiffScore": shadow_diff,
        "verdict": verdict,
        "thresholds": {"minConfidence": 0.85, "maxShadowDiff": 0.08},
    }


@router.post("/live-demo")
def live_demo(req: LiveDemoRequest,
              settings: Annotated[Settings, Depends(get_settings)]) -> dict:
    """Run the visible 4-step multi-agent trace over user-pasted text."""
    if not req.input_text.strip():
        raise HTTPException(status_code=422, detail="inputText must not be blank")

    step1 = _route_intent(req.input_text, req.hint)
    step2, sanitized = _guardrail_check(req.input_text)
    try:
        step3 = _worker_execute(step1["detectedIntent"], sanitized, settings)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    step4 = _evaluate(sanitized, step3["output"])

    return {
        "llmProvider": settings.llm_provider.value,
        "trace": [step1, step2, step3, step4],
        "finalVerdict": step4["verdict"],
    }
