"""AI engine test suite — happy paths, negative paths and edge cases."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, StorageProviderName, get_settings
from app.main import app
from app.providers.llm import MockLLMProvider
from app.services import analysis

client = TestClient(app)


@pytest.fixture(autouse=True)
def local_storage_tmp(tmp_path, monkeypatch):
    """Force local storage into a temp dir so tests never touch real paths."""
    get_settings.cache_clear()
    monkeypatch.setenv("STORAGE_PROVIDER", "local")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    yield
    get_settings.cache_clear()


# --- Health (happy path) -------------------------------------------------------


def test_health_reports_up_and_providers():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "UP"
    assert body["llm_provider"] == "mock"
    assert body["storage_provider"] == "local"


# --- ROI analysis ---------------------------------------------------------------


def test_roi_happy_path_detects_significant_uplift():
    response = client.post(
        "/api/v1/analysis/roi",
        json={"before": [10, 11, 9, 10, 10.5], "after": [15, 16, 14.5, 15.5, 16.2]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["significant_at_0_05"] is True
    assert body["cohens_d"] > 0


def test_roi_rejects_single_observation():
    # Negative: samples below the minimum size fail Pydantic validation (422).
    response = client.post("/api/v1/analysis/roi", json={"before": [1], "after": [2, 3]})
    assert response.status_code == 422


def test_roi_edge_identical_samples_not_significant():
    # Edge: zero variance between groups => no significance, d == 0.
    response = client.post(
        "/api/v1/analysis/roi", json={"before": [5, 5, 5], "after": [5, 5, 5]}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["significant_at_0_05"] is False
    assert body["cohens_d"] == 0.0


def test_roi_edge_zero_mean_before_returns_null_uplift():
    # Edge: mean(before) == 0 would divide by zero; API must return null uplift.
    response = client.post(
        "/api/v1/analysis/roi", json={"before": [-1, 1, -1, 1], "after": [2, 3, 2, 3]}
    )
    assert response.status_code == 200
    assert response.json()["uplift_pct"] is None


# --- Trend ----------------------------------------------------------------------


def test_trend_happy_path_upward():
    response = client.post("/api/v1/analysis/trend", json={"values": [1, 2, 3, 4, 5]})
    assert response.status_code == 200
    body = response.json()
    assert body["direction"] == "up"
    assert body["r_squared"] == pytest.approx(1.0)


def test_trend_rejects_two_points():
    response = client.post("/api/v1/analysis/trend", json={"values": [1, 2]})
    assert response.status_code == 422


# --- Mock LLM (deterministic simulator) ------------------------------------------


def test_insights_deterministic_for_same_prompt():
    payload = {"prompt": "How do we improve AI adoption in the payments team?"}
    first = client.post("/api/v1/coach/insights", json=payload).json()
    second = client.post("/api/v1/coach/insights", json=payload).json()
    assert first == second  # determinism is the mock's core contract
    assert first["provider"] == "mock"
    assert "Recommended actions" in first["insight"]


def test_insights_differ_for_different_prompts():
    a = client.post("/api/v1/coach/insights", json={"prompt": "prompt A"}).json()
    b = client.post("/api/v1/coach/insights", json={"prompt": "prompt B zz"}).json()
    assert a["insight"] != b["insight"]


def test_insights_rejects_empty_prompt():
    response = client.post("/api/v1/coach/insights", json={"prompt": ""})
    assert response.status_code == 422


def test_mock_llm_rejects_whitespace_prompt_directly():
    # Edge: whitespace-only prompt passes length validation but must still fail.
    with pytest.raises(ValueError):
        MockLLMProvider().complete("   ")


# --- Reports + storage port -------------------------------------------------------


@pytest.mark.parametrize("fmt", ["pdf", "docx", "pptx"])
def test_report_generation_all_formats(fmt):
    response = client.post(
        "/api/v1/reports",
        json={"title": "Q3 Engagement Review", "summary": "Strong uplift.", "format": fmt},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["format"] == fmt
    assert body["size_bytes"] > 0


def test_report_rejects_unknown_format():
    response = client.post(
        "/api/v1/reports", json={"title": "X", "summary": "Y", "format": "xlsx"}
    )
    assert response.status_code == 422


def test_report_edge_rejects_whitespace_title():
    # Edge: title of spaces passes min_length but must fail business validation.
    response = client.post(
        "/api/v1/reports", json={"title": "   ", "summary": "s", "format": "pdf"}
    )
    assert response.status_code == 422


# --- Storage provider unit behavior ----------------------------------------------


def test_local_storage_roundtrip_and_traversal_guard(tmp_path):
    from app.providers.storage import LocalStorageProvider

    storage = LocalStorageProvider(str(tmp_path))
    storage.put("a/b/report.txt", b"hello")
    assert storage.get("a/b/report.txt") == b"hello"

    # Edge: path traversal must be blocked.
    with pytest.raises(ValueError):
        storage.put("../escape.txt", b"nope")

    # Negative: missing key raises FileNotFoundError.
    with pytest.raises(FileNotFoundError):
        storage.get("missing/key.bin")


def test_unconfigured_cloud_storage_fails_fast(tmp_path):
    from app.providers.storage import get_storage_provider

    settings = Settings(
        storage_provider=StorageProviderName.AZURE_BLOB,
        local_storage_path=str(tmp_path),
    )
    provider = get_storage_provider(settings)
    with pytest.raises(NotImplementedError):
        provider.put("k", b"v")


# --- Pure analysis function edge case ---------------------------------------------


def test_analysis_raises_for_undersized_samples():
    with pytest.raises(ValueError):
        analysis.roi_significance([1.0], [2.0, 3.0])
