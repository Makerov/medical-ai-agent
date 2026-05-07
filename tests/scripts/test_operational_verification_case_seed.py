from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.settings import Settings
from scripts.seed_operational_verification_case import (
    OPERATIONAL_VERIFICATION_CASE_ID,
    OPERATIONAL_VERIFICATION_FIXTURE_PATH,
    load_operational_verification_fixture,
    seed_operational_verification_case,
)


def _build_settings(tmp_path: Path) -> Settings:
    return Settings(
        artifact_root_dir=tmp_path / "artifacts",
        knowledge_base_seed_dir=tmp_path / "knowledge-base",
        doctor_telegram_id_allowlist=(123456,),
    )


def _fixed_clock() -> datetime:
    return datetime(2026, 5, 1, 6, 0, tzinfo=UTC)


def test_operational_verification_fixture_is_canonical_and_synthetic() -> None:
    fixture = load_operational_verification_fixture()

    assert OPERATIONAL_VERIFICATION_FIXTURE_PATH.as_posix() == (
        "data/verification_cases/prepared_operational_case.json"
    )
    assert fixture["case_id"] == OPERATIONAL_VERIFICATION_CASE_ID
    assert fixture["data_classification"] == "synthetic_anonymized_verification"
    assert fixture["document_note"] == (
        "Synthetic/anonymized operational verification content only. No real patient "
        "documents are required."
    )


def test_seed_operational_verification_case_writes_case_linked_artifacts(
    tmp_path: Path,
) -> None:
    settings = _build_settings(tmp_path)

    result = seed_operational_verification_case(
        settings=settings,
        clock=_fixed_clock,
    )

    assert result.case_id == OPERATIONAL_VERIFICATION_CASE_ID
    assert result.intake_payload.case_id == OPERATIONAL_VERIFICATION_CASE_ID
    assert result.safety_result.case_id == OPERATIONAL_VERIFICATION_CASE_ID
    assert result.safety_result.is_pass is True
    assert result.handoff_delivery.notification is not None
    assert result.handoff_delivery.notification.case_id == OPERATIONAL_VERIFICATION_CASE_ID
    assert result.handoff_delivery.notification.status_code.value == "ready_for_review"

    expected_keys = {
        "intake_snapshot",
        "extracted_facts",
        "safety_check_result",
        "safety_check_examples",
        "handoff_payload",
        "source_references",
        "shared_status",
        "processing_result",
        "structured_extraction_examples",
        "summary_draft",
        "rag_provenance_examples",
        "verification_export_contract",
    }
    assert set(result.artifacts) == expected_keys
    assert all("demo" not in path.as_posix() for path in result.artifacts.values())
    assert all(path.exists() for path in result.artifacts.values())

    export_contract = json.loads(
        result.artifacts["verification_export_contract"].read_text(encoding="utf-8")
    )
    assert export_contract["case_id"] == OPERATIONAL_VERIFICATION_CASE_ID
    assert export_contract["synthetic_by_default"] is True
    assert export_contract["overview"]["case_id"] == OPERATIONAL_VERIFICATION_CASE_ID
    assert export_contract["overview"]["synthetic_by_default"] is True
    assert "No real patient documents required." in export_contract["overview"][
        "non_goals"
    ]
    assert [item["label"] for item in export_contract["required_artifacts"]] == [
        "structured_extraction_examples",
        "rag_provenance_examples",
        "safety_check_result",
        "minimal_eval_suite",
    ]

    verification_files = sorted(
        path.relative_to(settings.artifact_root_dir)
        for path in (settings.artifact_root_dir / OPERATIONAL_VERIFICATION_CASE_ID).rglob("*.json")
    )
    assert len(verification_files) == len(result.artifacts)
    assert len(verification_files) == len(set(verification_files))


def test_seed_operational_verification_case_is_deterministic_across_reruns(
    tmp_path: Path,
) -> None:
    settings = _build_settings(tmp_path)

    first = seed_operational_verification_case(
        settings=settings,
        clock=_fixed_clock,
    )
    second = seed_operational_verification_case(
        settings=settings,
        clock=_fixed_clock,
        reset_artifacts=False,
    )

    assert first.case_id == second.case_id == OPERATIONAL_VERIFICATION_CASE_ID
    assert first.artifacts == second.artifacts
    assert first.safety_result == second.safety_result
    assert first.handoff_delivery.notification is not None
    assert second.handoff_delivery.notification is not None
    assert first.handoff_delivery.notification == second.handoff_delivery.notification
    assert first.handoff_delivery.audit_event_id is not None
    assert second.handoff_delivery.audit_event_id is not None

    case_root = settings.artifact_root_dir / OPERATIONAL_VERIFICATION_CASE_ID
    verification_files = sorted(
        path.relative_to(settings.artifact_root_dir)
        for path in case_root.rglob("*.json")
    )
    assert len(verification_files) == len(second.artifacts)
    assert len(verification_files) == len(set(verification_files))

    export_contract = json.loads(
        (case_root / "verification" / "operational-verification-export.json").read_text(
            encoding="utf-8"
        )
    )
    assert export_contract["case_id"] == OPERATIONAL_VERIFICATION_CASE_ID
    assert export_contract["overview"]["title"] == "Operational verification artifact export"
    assert export_contract["overview"]["reviewer_notes"].startswith(
        "Synthetic, case-scoped operational verification bundle"
    )
