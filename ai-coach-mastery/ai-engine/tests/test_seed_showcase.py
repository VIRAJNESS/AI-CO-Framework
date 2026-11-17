"""Tests for the showcase artifact seeder — happy, negative and edge cases."""

from __future__ import annotations

import io
import zipfile

import pytest

from app.core.config import get_settings

import seed_showcase

ZIP_MAGIC = b"PK\x03\x04"


@pytest.fixture(autouse=True)
def local_mock(monkeypatch, tmp_path):
    get_settings.cache_clear()
    monkeypatch.setenv("STORAGE_PROVIDER", "local")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    yield tmp_path
    get_settings.cache_clear()


# --- Happy path -------------------------------------------------------------------


def test_seed_artifacts_creates_all_30_deliverables(local_mock):
    keys = seed_showcase.seed_artifacts()

    # 6+4+3+2 stages × 2 formats = 30 artifacts.
    assert len(keys) == 30
    # Keys follow the deterministic contract shared with Java's DataSeeder.
    assert "showcase/novatel/stage6.pptx" in keys
    assert "showcase/finpulse/stage4.docx" in keys
    assert "showcase/veloceai/stage3.pptx" in keys
    assert "showcase/omnicare/stage2.docx" in keys
    # Every stored file is a valid OPC (zip) package on disk.
    files = list(local_mock.rglob("stage*.*"))
    assert len(files) == 30
    assert all(f.read_bytes()[:4] == ZIP_MAGIC for f in files)


def test_novatel_statistical_proof_matches_headlines():
    results = seed_showcase.novatel_results()
    stats = results[5]
    # p < 0.001 and significance on the Welch test.
    assert stats["abTest"]["welchT"]["pValue"] < 0.001
    assert stats["abTest"]["significantAt005"] is True
    # Cohen's Kappa ≈ 0.86 as per the scenario brief.
    assert stats["judgeAgreement"]["cohensKappa"] == pytest.approx(0.86, abs=0.02)
    # Toil reduction ≈ 68%: means 42.3 -> 13.45.
    reduction = 1 - stats["abTest"]["meanTreatment"] / stats["abTest"]["meanControl"]
    assert reduction == pytest.approx(0.68, abs=0.02)
    # NEV positive for the CFO story.
    assert stats["economics"]["cfoVerdict"] == "VALUE_POSITIVE"


# --- Negative / guard paths -----------------------------------------------------------


def test_seed_fails_fast_on_unconfigured_cloud_storage(monkeypatch, tmp_path):
    get_settings.cache_clear()
    monkeypatch.setenv("STORAGE_PROVIDER", "gcs")
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    try:
        with pytest.raises(NotImplementedError):
            seed_showcase.seed_artifacts()
    finally:
        get_settings.cache_clear()


# --- Edge cases -------------------------------------------------------------------------


def test_stage_coverage_matches_each_clients_current_stage():
    # Edge: artifact stages must exactly mirror lifecycle positions (6/4/3/2).
    assert sorted(seed_showcase.novatel_results()) == [1, 2, 3, 4, 5, 6]
    assert sorted(seed_showcase.finpulse_results()) == [1, 2, 3, 4]
    assert sorted(seed_showcase.veloceai_results()) == [1, 2, 3]
    assert sorted(seed_showcase.omnicare_results()) == [1, 2]


def test_omnicare_audit_flags_data_ontology_red_flag():
    # Edge: the 2/5 Data & Ontology score must surface as a critical red flag.
    audit = seed_showcase.omnicare_results()[2]
    assert "DATA_ONTOLOGY_READINESS" in audit["criticalRedFlags"]
    assert audit["pillarScores"]["DATA_ONTOLOGY_READINESS"] == 2


def test_finpulse_demo_is_deterministic_and_complaint_routed():
    # Edge: mock-mode demo must be reproducible and routed as a complaint.
    first = seed_showcase.finpulse_results()[4]
    second = seed_showcase.finpulse_results()[4]
    assert first == second
    assert first["trace"][0]["detectedIntent"] == "CUSTOMER_COMPLAINT"
    assert first["frictionOutcome"] == {"dropoffBeforePct": 46,
                                        "dropoffAfterPct": 18}


def test_seeding_is_idempotent_overwrite(local_mock):
    # Edge: re-running overwrites the same keys — no duplicates on disk.
    seed_showcase.seed_artifacts()
    seed_showcase.seed_artifacts()
    files = list(local_mock.rglob("stage*.*"))
    assert len(files) == 30


def test_generated_pptx_contains_client_name(local_mock):
    # Edge: binary content sanity — deck embeds the client name.
    seed_showcase.seed_artifacts()
    deck = (local_mock / "showcase" / "veloceai" / "stage3.pptx").read_bytes()
    archive = zipfile.ZipFile(io.BytesIO(deck))
    slide_xml = b"".join(archive.read(n) for n in archive.namelist()
                         if n.startswith("ppt/slides/slide"))
    assert b"VeloceAI Series-B SaaS" in slide_xml
