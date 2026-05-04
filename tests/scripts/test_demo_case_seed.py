import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.settings import Settings
from scripts.seed_operational_verification_case import (
    OPERATIONAL_VERIFICATION_CASE_ID,
    seed_operational_verification_case,
)


def _build_settings(tmp_path: Path) -> Settings:
    return Settings(
        artifact_root_dir=tmp_path / "artifacts",
        doctor_telegram_id_allowlist=(123456,),
    )


def test_seed_demo_case_creates_stable_case_and_case_scoped_artifacts(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)

    result = seed_operational_verification_case(
        settings=settings,
        clock=lambda: datetime(2026, 5, 1, 6, 0, tzinfo=UTC),
    )

    assert result.case_id == OPERATIONAL_VERIFICATION_CASE_ID
    assert result.intake_payload.case_id == OPERATIONAL_VERIFICATION_CASE_ID
    assert result.safety_result.case_id == OPERATIONAL_VERIFICATION_CASE_ID
    assert result.safety_result.is_pass
    assert result.handoff_delivery.notification is not None
    assert result.handoff_delivery.notification.case_id == OPERATIONAL_VERIFICATION_CASE_ID
    assert result.handoff_delivery.notification.status_code.value == "ready_for_review"

    expected_relative_paths = {
        "intake_snapshot": Path(
            "case_operational_verification_ready/export/verification/intake-snapshot.json"
        ),
        "extracted_facts": Path(
            "case_operational_verification_ready/export/verification/extracted-facts.json"
        ),
        "safety_check_result": Path(
            "case_operational_verification_ready/safety/verification/safety-check-result.json"
        ),
        "safety_check_examples": Path(
            "case_operational_verification_ready/safety/verification/safety-check-examples.json"
        ),
        "handoff_payload": Path(
            "case_operational_verification_ready/export/verification/doctor-handoff.json"
        ),
        "source_references": Path(
            "case_operational_verification_ready/export/verification/source-references.json"
        ),
        "shared_status": Path(
            "case_operational_verification_ready/export/verification/shared-status.json"
        ),
        "processing_result": Path(
            "case_operational_verification_ready/export/verification/processing-result.json"
        ),
        "structured_extraction_examples": Path(
            "case_operational_verification_ready/export/verification/structured-extraction-examples.json"
        ),
        "rag_provenance_examples": Path(
            "case_operational_verification_ready/export/verification/rag-provenance-examples.json"
        ),
        "summary_draft": Path(
            "case_operational_verification_ready/summary/verification/summary-draft.json"
        ),
        "verification_export_contract": Path(
            "case_operational_verification_ready/verification/operational-verification-export.json"
        ),
    }
    assert set(result.artifacts) == set(expected_relative_paths)
    for key, path in result.artifacts.items():
        assert path == (settings.artifact_root_dir / expected_relative_paths[key]).resolve(
            strict=False
        )
        assert path.exists()

    shared_status_json = (
        settings.artifact_root_dir / expected_relative_paths["shared_status"]
    ).read_text(encoding="utf-8")
    assert '"case_id": "case_operational_verification_ready"' in shared_status_json

    structured_examples_json = (
        settings.artifact_root_dir
        / expected_relative_paths["structured_extraction_examples"]
    ).read_text(encoding="utf-8")
    assert '"data_classification": "synthetic_anonymized_verification"' in structured_examples_json
    assert '"uncertainty_reason": "missing_unit"' in structured_examples_json

    rag_examples_json = (
        settings.artifact_root_dir / expected_relative_paths["rag_provenance_examples"]
    ).read_text(encoding="utf-8")
    assert '"data_classification": "synthetic_anonymized_verification"' in rag_examples_json
    assert '"grounded": true' in rag_examples_json
    assert '"grounded": false' in rag_examples_json
    assert '"no_trustworthy_knowledge_entries_found"' in rag_examples_json

    safety_examples_json = (
        settings.artifact_root_dir / expected_relative_paths["safety_check_examples"]
    ).read_text(encoding="utf-8")
    assert '"decision": "pass"' in safety_examples_json
    assert '"decision": "blocked"' in safety_examples_json
    assert '"decision": "corrected"' in safety_examples_json
    assert '"data_classification": "synthetic_anonymized_verification"' in safety_examples_json

    reviewer_export_json = (
        settings.artifact_root_dir / expected_relative_paths["verification_export_contract"]
    ).read_text(encoding="utf-8")
    assert '"case_id": "case_operational_verification_ready"' in reviewer_export_json
    assert (
        '"reviewer_notes": "Synthetic, case-scoped operational verification bundle for '
        'maintainer review without live model calls."'
        in reviewer_export_json
    )
    assert '"label": "minimal_eval_suite"' in reviewer_export_json
    assert (
        '"artifact_path": "case_operational_verification_ready/verification/minimal-eval-suite.json"'
        in reviewer_export_json
    )


def test_seed_demo_case_is_deterministic_across_reruns(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)

    def clock() -> datetime:
        return datetime(2026, 5, 1, 6, 0, tzinfo=UTC)

    first = seed_operational_verification_case(settings=settings, clock=clock)
    second = seed_operational_verification_case(settings=settings, clock=clock)

    assert first.case_id == second.case_id == OPERATIONAL_VERIFICATION_CASE_ID
    assert (
        first.handoff_delivery.case_id
        == second.handoff_delivery.case_id
        == OPERATIONAL_VERIFICATION_CASE_ID
    )
    assert first.handoff_delivery.notification is not None
    assert second.handoff_delivery.notification is not None
    assert (
        first.handoff_delivery.notification.shared_status
        == second.handoff_delivery.notification.shared_status
    )
    assert first.safety_result == second.safety_result
    assert first.artifacts == second.artifacts
    assert (
        second.artifacts["verification_export_contract"]
        == settings.artifact_root_dir
        / "case_operational_verification_ready"
        / "verification"
        / "operational-verification-export.json"
    )

    rag_examples_path = (
        settings.artifact_root_dir
        / "case_operational_verification_ready"
        / "export"
        / "verification"
        / "rag-provenance-examples.json"
    )
    rag_examples_payload = json.loads(rag_examples_path.read_text(encoding="utf-8"))
    assert [example["example_id"] for example in rag_examples_payload["examples"]] == [
        "grounded_hemoglobin_provenance",
        "not_grounded_creatinine_provenance",
    ]
    assert [example["grounded"] for example in rag_examples_payload["examples"]] == [True, False]

    safety_examples_path = (
        settings.artifact_root_dir
        / "case_operational_verification_ready"
        / "safety"
        / "verification"
        / "safety-check-examples.json"
    )
    safety_examples_json = safety_examples_path.read_text(encoding="utf-8")
    assert safety_examples_json.count('"decision": "pass"') == 1
    assert safety_examples_json.count('"decision": "blocked"') == 1
    assert safety_examples_json.count('"decision": "corrected"') == 1


def test_seed_demo_case_leaves_case_ready_for_doctor(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)

    def clock() -> datetime:
        return datetime(2026, 5, 1, 6, 0, tzinfo=UTC)

    result = seed_operational_verification_case(
        settings=settings,
        clock=clock,
    )

    assert result.handoff_delivery.notification is not None
    assert result.handoff_delivery.notification.shared_status.value == "ready_for_doctor"
    rag_examples_path = (
        settings.artifact_root_dir
        / "case_operational_verification_ready"
        / "export"
        / "verification"
        / "rag-provenance-examples.json"
    )
    assert rag_examples_path.exists()
    safety_examples_path = (
        settings.artifact_root_dir
        / "case_operational_verification_ready"
        / "safety"
        / "verification"
        / "safety-check-examples.json"
    )
    assert safety_examples_path.exists()
    reviewer_export_path = (
        settings.artifact_root_dir
        / "case_operational_verification_ready"
        / "verification"
        / "operational-verification-export.json"
    )
    assert reviewer_export_path.exists()
