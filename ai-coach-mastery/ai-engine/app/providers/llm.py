"""LLM provider port + adapters (ports-and-adapters pattern).

The active provider is selected purely by the LLM_PROVIDER environment
variable. The default `mock` adapter is a deterministic intelligent simulator:
it derives a stable seed from the prompt so identical prompts always yield
identical, plausible structured responses — zero network calls, zero keys.
Cloud adapters are declared stubs so switching providers is config-only.
"""

from __future__ import annotations

import hashlib
import random
from abc import ABC, abstractmethod

from app.core.config import LLMProviderName, Settings


class LLMProvider(ABC):
    """Port: minimal contract every LLM backend must satisfy."""

    name: str

    @abstractmethod
    def complete(self, prompt: str, max_tokens: int = 512) -> str:
        """Return a completion for the given prompt."""


class MockLLMProvider(LLMProvider):
    """Deterministic intelligent simulator (default, local-first).

    Uses a SHA-256 of the prompt to seed a PRNG, then assembles a coherent
    coaching-style response from curated fragments. Deterministic => testable.
    """

    name = "mock"

    _THEMES = [
        "adoption velocity", "developer experience", "ROI measurement",
        "prompt engineering maturity", "legacy modernization", "delivery predictability",
    ]
    _ACTIONS = [
        "Establish a weekly AI usage baseline and track trend deltas.",
        "Pair senior engineers with AI-assist champions for two sprints.",
        "Introduce a prompt library with reviewed, versioned templates.",
        "Pilot AI-assisted code review on one high-churn repository.",
        "Define a before/after cycle-time metric with a control team.",
        "Run a structured discovery audit across the top three value streams.",
    ]
    _RISKS = [
        "metric gaming if usage targets are mandated top-down",
        "regression risk without guardrail test coverage",
        "tool fatigue from onboarding too many assistants at once",
        "uneven adoption across senior vs. junior cohorts",
    ]

    def complete(self, prompt: str, max_tokens: int = 512) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt must not be empty")
        # Stable seed from prompt content => deterministic output.
        seed = int.from_bytes(hashlib.sha256(prompt.encode("utf-8")).digest()[:8], "big")
        rng = random.Random(seed)
        theme = rng.choice(self._THEMES)
        actions = rng.sample(self._ACTIONS, k=3)
        risk = rng.choice(self._RISKS)
        confidence = round(rng.uniform(0.72, 0.95), 2)
        response = (
            f"[mock-llm] Focus area: {theme}.\n"
            f"Recommended actions:\n"
            f"1. {actions[0]}\n2. {actions[1]}\n3. {actions[2]}\n"
            f"Key risk: {risk}.\n"
            f"Confidence: {confidence}"
        )
        # Respect max_tokens approximately (1 token ~ 4 chars heuristic).
        return response[: max_tokens * 4]


class _UnconfiguredCloudProvider(LLMProvider):
    """Stub for cloud adapters not yet wired — fails fast with a clear message."""

    def __init__(self, name: str) -> None:
        self.name = name

    def complete(self, prompt: str, max_tokens: int = 512) -> str:
        raise NotImplementedError(
            f"LLM provider '{self.name}' adapter is a Step-1 stub. "
            f"Set LLM_PROVIDER=mock for local development, or implement the "
            f"adapter and supply credentials via environment variables."
        )


def get_llm_provider(settings: Settings) -> LLMProvider:
    """Factory: resolve the configured LLM provider (12-factor switch)."""
    if settings.llm_provider == LLMProviderName.MOCK:
        return MockLLMProvider()
    return _UnconfiguredCloudProvider(settings.llm_provider.value)
