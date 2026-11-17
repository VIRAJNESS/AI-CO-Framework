"""Tests for the Document Generation Factory — happy, negative and edge cases."""

from __future__ import annotations

import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.doc_factory.charts import stage_chart
from app.doc_factory.docx_builder import generate_stage_docx
from app.doc_factory.pptx_builder import generate_stage_pptx
from app.main import app

client = TestClient(app)

RENDER = "/api/v1/engine/documents/render"

PNG_MAGIC = b"\x89PNG"
ZIP_MAGIC = b"PK\x03\x04"  # pptx/docx are OPC zip packages

ENGAGEMENT = {"clientName": "Acme Corp", "industry": "FinTech",
              "domainTrack": "SDLC"}


@pytest.fixture(autouse=True)
def local_storage(monkeypatch, tmp_path):
    get_settings.cache_clear()
    monkeypatch.setenv("STORAGE_PROVIDER", "local")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    yield tmp_path
    get_settings.cache_clear()


def _stage_result_for(stage: int) -> dict:
    """Produce a realistic stage_result by invoking the actual stage endpoints."""
    if stage == 1:
        return client.post("/api/v1/engine/stage1/pitch-simulator", json={
            "industry": "FinTech", "domainTrack": "SDLC",
            "engineeringHeadcount": 80, "monthlyTicketVolume": 3000,
            "currentCloudSpend": 40000}).json()
    if stage == 2:
        return client.post("/api/v1/engine/stage2/diagnostic-audit", json={
            "domainTrack": "SDLC",
            "pillarScores": {"STRATEGY_KPI_ALIGNMENT": 4,
                             "DATA_ONTOLOGY_READINESS": 3,
                             "CLOUD_AGENT_ARCHITECTURE": 2,
                             "RESPONSIBLE_AI_GUARDRAILS": 5,
                             "TALENT_PDLC_CULTURE": 3}}).json()
    if stage == 3:
        return client.post("/api/v1/engine/stage3/domain-blueprint",
                           json={"domainTrack": "LEGACY"}).json()
    if stage == 4:
        return client.post("/api/v1/engine/stage4/live-demo", json={
            "inputText": "Exception: NullPointerException at Service.java:1"}).json()
    if stage == 5:
        return client.post("/api/v1/engine/stage5/statistical-roi", json={
            "abTest": {"control": [10, 11, 9, 10], "treatment": [14, 15, 14, 16]},
            "economics": {"annualGrossSavings": 500000, "annualInferenceCost": 50000,
                          "annualOrchestrationCost": 30000,
                          "annualGovernanceCost": 20000}}).json()
    return client.post("/api/v1/engine/stage6/roadmap-mentor",
                       json={"domainTrack": "STARTUP"}).json()


# --- Happy paths: endpoint renders both formats for every stage -------------------


@pytest.mark.parametrize("stage", [1, 2, 3, 4, 5, 6])
@pytest.mark.parametrize("fmt", ["pptx", "docx"])
def test_render_endpoint_all_stages_both_formats(stage, fmt, local_storage):
    stage_result = _stage_result_for(stage)
    res = client.post(RENDER, json={
        "stageNum": stage, "format": fmt,
        "engagementData": ENGAGEMENT, "stageResult": stage_result})
    assert res.status_code == 200
    assert res.content[:4] == ZIP_MAGIC  # valid OPC package
    assert f".{fmt}" in res.headers["content-disposition"]
    key = res.headers["x-artifact-key"]
    assert key.startswith(f"deliverables/stage{stage}/")
    # Artifact persisted through the storage adapter.
    saved = list(local_storage.rglob(f"*.{fmt}"))
    assert len(saved) == 1
    assert saved[0].read_bytes()[:4] == ZIP_MAGIC


def test_pptx_has_seven_slides_and_valid_package():
    data = generate_stage_pptx(1, ENGAGEMENT, _stage_result_for(1))
    archive = zipfile.ZipFile(io.BytesIO(data))
    slides = [n for n in archive.namelist()
              if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
    assert len(slides) == 7  # 6-to-8 slide deck contract
    # Embedded chart PNG present inside the deck.
    media = [n for n in archive.namelist() if n.startswith("ppt/media/")]
    assert any(n.endswith(".png") for n in media)


def test_docx_contains_chart_and_document_xml():
    data = generate_stage_docx(2, ENGAGEMENT, _stage_result_for(2))
    archive = zipfile.ZipFile(io.BytesIO(data))
    assert "word/document.xml" in archive.namelist()
    media = [n for n in archive.namelist() if n.startswith("word/media/")]
    assert any(n.endswith(".png") for n in media)
    xml = archive.read("word/document.xml").decode("utf-8")
    assert "Acme Corp" in xml
    assert "Sign-Off Checklist" in xml


# --- Chart factory ------------------------------------------------------------------


@pytest.mark.parametrize("stage", [1, 2, 3, 4, 5, 6])
def test_stage_charts_produce_png(stage):
    png = stage_chart(stage, _stage_result_for(stage))
    assert png[:4] == PNG_MAGIC


def test_chart_placeholder_on_empty_result():
    # Edge: empty stage_result must yield a placeholder PNG, never raise.
    for stage in range(1, 7):
        assert stage_chart(stage, {})[:4] == PNG_MAGIC


# --- Negative paths --------------------------------------------------------------------


def test_render_rejects_invalid_stage():
    res = client.post(RENDER, json={"stageNum": 7, "format": "pptx",
                                    "engagementData": {}, "stageResult": {}})
    assert res.status_code == 422


def test_render_rejects_unknown_format():
    res = client.post(RENDER, json={"stageNum": 1, "format": "pdf",
                                    "engagementData": {}, "stageResult": {}})
    assert res.status_code == 422


# --- Edge cases ----------------------------------------------------------------------------


def test_render_edge_empty_payloads_still_produce_document(local_storage):
    # Edge: no engagement data, no stage result — defaults everywhere.
    res = client.post(RENDER, json={"stageNum": 3, "format": "docx"})
    assert res.status_code == 200
    assert res.content[:4] == ZIP_MAGIC
    assert 'filename="stage3-client.docx"' in res.headers["content-disposition"]


def test_render_edge_special_characters_in_client_name(local_storage):
    # Edge: client name with spaces/symbols must slugify into a safe filename.
    res = client.post(RENDER, json={
        "stageNum": 6, "format": "pptx",
        "engagementData": {"clientName": "Über & Söhne GmbH!!"},
        "stageResult": {}})
    assert res.status_code == 200
    disposition = res.headers["content-disposition"]
    assert "&" not in disposition and " " not in disposition.split("filename=")[1]


def test_render_edge_unconfigured_cloud_storage_returns_501(monkeypatch, tmp_path):
    # Edge: azure_blob stub must map to 501, not a 500 crash.
    get_settings.cache_clear()
    monkeypatch.setenv("STORAGE_PROVIDER", "azure_blob")
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    try:
        res = client.post(RENDER, json={"stageNum": 1, "format": "docx",
                                        "engagementData": {}, "stageResult": {}})
        assert res.status_code == 501
    finally:
        get_settings.cache_clear()


def test_pptx_governance_rows_from_stage_result():
    # Edge: governanceGates in stage_result override the default N/A matrix.
    result = {"governanceGates": [
        {"gateName": "PII_REDACTION", "status": "PASS", "notes": "verified"},
        {"gateName": "FINOPS_CAP", "status": "FAIL", "notes": "over budget"}]}
    data = generate_stage_pptx(4, ENGAGEMENT, result)
    archive = zipfile.ZipFile(io.BytesIO(data))
    slide_xml = b"".join(archive.read(n) for n in archive.namelist()
                         if n.startswith("ppt/slides/slide"))
    assert b"FINOPS_CAP" in slide_xml
    assert b"over budget" in slide_xml
