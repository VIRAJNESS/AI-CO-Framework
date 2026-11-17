#!/usr/bin/env python3
"""End-to-end smoke tests for the running AI Coach Mastery stack.

Stdlib-only (urllib) — no pip installs needed. Works against both the Docker
compose stack and the Docker-free fallback (start-local.*).

Checks:
  1. GET /api/v1/engagements returns the 4 seeded showcase clients.
  2. Stage 2 Diagnostic returns maturity-radar JSON; governance gates exist.
  3. Stage 4 Live Demo returns the 4-step agentic trace.
  4. documents/render returns valid non-empty PPTX + DOCX for stages 1..6.

Usage:
  python scripts/smoke_test.py
  CORE_URL=http://localhost:8080 AI_URL=http://localhost:8000 python scripts/smoke_test.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

CORE = os.environ.get("CORE_URL", "http://localhost:8080").rstrip("/")
AI = os.environ.get("AI_URL", "http://localhost:8000").rstrip("/")
ZIP_MAGIC = b"PK\x03\x04"

PASSED: list[str] = []
FAILED: list[str] = []


def _request(method: str, url: str, body: dict | None = None,
             timeout: int = 60) -> tuple[int, bytes]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        PASSED.append(name)
        print(f"  PASS  {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL  {name}  {detail}")


def wait_for(url: str, name: str, attempts: int = 30) -> bool:
    """Poll a health URL until it answers 200 (max ~60s)."""
    for _ in range(attempts):
        try:
            status, _ = _request("GET", url, timeout=5)
            if status == 200:
                print(f"  UP    {name}")
                return True
        except Exception:
            pass
        time.sleep(2)
    print(f"  DOWN  {name} ({url})")
    return False


def main() -> int:
    print(f"Smoke tests — core: {CORE}  ai: {AI}\n")

    print("[0] Service health")
    core_up = wait_for(f"{CORE}/actuator/health", "core-api")
    ai_up = wait_for(f"{AI}/health", "ai-engine")
    if not (core_up and ai_up):
        print("\nServices not reachable — start the stack first "
              "(make up OR start-local.ps1 / start-local.sh).")
        return 1

    # --- 1. Seeded showcase engagements ---------------------------------------
    print("\n[1] Seeded showcase clients")
    status, body = _request("GET", f"{CORE}/api/v1/engagements")
    engagements = json.loads(body) if status == 200 else []
    names = sorted(e["clientName"] for e in engagements)
    expected = ["FinPulse Digital Banking", "NovaTel Global Telecom",
                "OmniCare Core Insurance", "VeloceAI Series-B SaaS"]
    check("GET /api/v1/engagements returns 200", status == 200, f"status={status}")
    check("All 4 showcase clients seeded", names == expected,
          f"got {names}")
    stages = {e["clientName"]: e["currentStage"] for e in engagements}
    check("Lifecycle positions correct (6/4/3/2)",
          stages.get("NovaTel Global Telecom") == 6
          and stages.get("FinPulse Digital Banking") == 4
          and stages.get("VeloceAI Series-B SaaS") == 3
          and stages.get("OmniCare Core Insurance") == 2,
          f"got {stages}")

    # --- 2. Stage 2 diagnostic + governance gates -------------------------------
    print("\n[2] Stage 2 Diagnostic + Governance Gates")
    status, body = _request("POST", f"{AI}/api/v1/engine/stage2/diagnostic-audit", {
        "domainTrack": "LEGACY",
        "pillarScores": {
            "STRATEGY_KPI_ALIGNMENT": 3, "DATA_ONTOLOGY_READINESS": 2,
            "CLOUD_AGENT_ARCHITECTURE": 2, "RESPONSIBLE_AI_GUARDRAILS": 3,
            "TALENT_PDLC_CULTURE": 2}})
    audit = json.loads(body) if status == 200 else {}
    check("Diagnostic audit returns 200", status == 200, f"status={status}")
    check("Maturity radar JSON has 5 pillar scores",
          len(audit.get("pillarScores", {})) == 5)
    check("Maturity index computed",
          isinstance(audit.get("maturityIndex"), (int, float)))
    check("Red-flag blockers detected",
          "DATA_ONTOLOGY_READINESS" in audit.get("criticalRedFlags", []))

    omnicare = next((e for e in engagements
                     if e["clientName"] == "OmniCare Core Insurance"), None)
    if omnicare:
        status, body = _request(
            "GET", f"{CORE}/api/v1/engagements/{omnicare['id']}/gates")
        gates = json.loads(body) if status == 200 else []
        check("Governance gates present for showcase client",
              status == 200 and len(gates) >= 3, f"status={status} n={len(gates)}")
    else:
        check("Governance gates present for showcase client", False, "no OmniCare")

    # --- 3. Stage 4 live demo trace ------------------------------------------------
    print("\n[3] Stage 4 Live Demo trace")
    status, body = _request("POST", f"{AI}/api/v1/engine/stage4/live-demo", {
        "inputText": "Exception: NullPointerException at Service.java:42, "
                     "error 500 after timeout"})
    demo = json.loads(body) if status == 200 else {}
    steps = [s.get("step") for s in demo.get("trace", [])]
    check("Live demo returns 200", status == 200, f"status={status}")
    check("4-step agentic trace returned", steps == [1, 2, 3, 4], f"steps={steps}")
    check("Final verdict present",
          demo.get("finalVerdict") in ("APPROVE", "HUMAN_REVIEW"))

    # --- 4. PPTX + DOCX downloads for every stage ------------------------------------
    print("\n[4] Document downloads (stages 1-6 x pptx/docx)")
    for stage in range(1, 7):
        for fmt in ("pptx", "docx"):
            status, data = _request(
                "POST", f"{AI}/api/v1/engine/documents/render",
                {"stageNum": stage, "format": fmt,
                 "engagementData": {"clientName": "Smoke Test Co",
                                    "industry": "QA", "domainTrack": "SDLC"},
                 "stageResult": {}})
            ok = (status == 200 and len(data) > 5000
                  and data[:4] == ZIP_MAGIC)
            check(f"Stage {stage} {fmt.upper()} download valid", ok,
                  f"status={status} bytes={len(data)}")

    # --- Summary -----------------------------------------------------------------------
    print(f"\n==== {len(PASSED)} passed, {len(FAILED)} failed ====")
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
