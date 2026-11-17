"""AI Coach Mastery — AI Engine (FastAPI).

Routes:
  GET  /health                     — liveness/readiness with provider info
  POST /api/v1/analysis/roi        — before/after ROI significance (SciPy)
  POST /api/v1/analysis/trend      — OLS trend fit (statsmodels)
  POST /api/v1/coach/insights      — LLM-backed coaching insight (mock by default)
  POST /api/v1/reports             — generate docx/pptx/pdf artifact via storage port
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.doc_factory import router as doc_factory_router
from app.engine import (
    stage1_pitch,
    stage2_audit,
    stage3_blueprint,
    stage4_livedemo,
    stage5_stats,
    stage6_roadmap,
)
from app.providers.llm import LLMProvider, get_llm_provider
from app.providers.storage import StorageProvider, get_storage_provider
from app.services import analysis, reports

app = FastAPI(
    title="AI Coach Mastery — AI Engine",
    version="0.1.0",
    description="Analytics, document generation and provider-agnostic LLM gateway.",
)

# CORS for the local Angular dev server; tighten via env in later steps.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Head Coach intelligence engine — one router per lifecycle stage.
for engine_router in (
    stage1_pitch.router,
    stage2_audit.router,
    stage3_blueprint.router,
    stage4_livedemo.router,
    stage5_stats.router,
    stage6_roadmap.router,
    doc_factory_router.router,
):
    app.include_router(engine_router, prefix="/api/v1/engine")


# --- Dependencies -------------------------------------------------------------

SettingsDep = Annotated[Settings, Depends(get_settings)]


def _llm(settings: SettingsDep) -> LLMProvider:
    return get_llm_provider(settings)


def _storage(settings: SettingsDep) -> StorageProvider:
    return get_storage_provider(settings)


# --- Schemas (Pydantic v2) -----------------------------------------------------


class RoiRequest(BaseModel):
    before: list[float] = Field(min_length=2, description="Pre-intervention metric samples")
    after: list[float] = Field(min_length=2, description="Post-intervention metric samples")


class TrendRequest(BaseModel):
    values: list[float] = Field(min_length=3, description="Ordered metric series")


class InsightRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    max_tokens: int = Field(default=512, ge=16, le=4096)


class ReportRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=20000)
    format: str = Field(default="pdf", pattern="^(docx|pptx|pdf)$")


# --- Routes -------------------------------------------------------------------


@app.get("/health", tags=["ops"])
def health(settings: SettingsDep) -> dict:
    """Health check: reports configured providers so ops can verify wiring."""
    return {
        "status": "UP",
        "service": settings.app_name,
        "version": settings.version,
        "llm_provider": settings.llm_provider.value,
        "storage_provider": settings.storage_provider.value,
    }


@app.post("/api/v1/analysis/roi", tags=["analysis"])
def analyze_roi(body: RoiRequest) -> dict:
    """Before/after statistical significance for coaching ROI evaluation."""
    try:
        return analysis.roi_significance(body.before, body.after)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/analysis/trend", tags=["analysis"])
def analyze_trend(body: TrendRequest) -> dict:
    """Linear trend fit over an ordered metric series."""
    try:
        return analysis.trend(body.values)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/coach/insights", tags=["coach"])
def coach_insights(
    body: InsightRequest,
    llm: Annotated[LLMProvider, Depends(_llm)],
) -> dict:
    """Generate a coaching insight via the configured LLM provider."""
    try:
        completion = llm.complete(body.prompt, max_tokens=body.max_tokens)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"provider": llm.name, "insight": completion}


@app.post("/api/v1/reports", tags=["reports"])
def create_report(
    body: ReportRequest,
    storage: Annotated[StorageProvider, Depends(_storage)],
) -> dict:
    """Generate a docx/pptx/pdf report and persist it via the storage port."""
    try:
        return reports.generate_report(storage, body.title, body.summary, body.format)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
