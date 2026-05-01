from datetime import UTC, datetime
import json
from pathlib import Path

from app.core.settings import Settings
from scripts.seed_demo_case import DEMO_CASE_ID, seed_demo_case


def _build_settings(tmp_path: Path) -> Settings:
    return Settings(
        artifact_root_dir=tmp_path / "artifacts",
        doctor_telegram_id_allowlist=(123456,),
    )


def test_seed_demo_case_creates_stable_case_and_case_scoped_artifacts(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)

    result = seed_demo_case(
        settings=settings,
        clock=lambda: datetime(2026, 5, 1, 6, 0, tzinfo=UTC),
    )

    assert result.case_id == DEMO_CASE_ID
    assert result.intake_payload.case_id == DEMO_CASE_ID
    assert result.safety_result.case_id == DEMO_CASE_ID
    assert result.safety_result.is_pass
    assert result.handoff_delivery.notification is not None
    assert result.handoff_delivery.notification.case_id == DEMO_CASE_ID
    assert result.handoff_delivery.notification.status_code.value == "ready_for_review"

    expected_relative_paths = {
        "intake_snapshot": Path("case_demo_happy_path/export/demo/intake-snapshot.json"),
        "extracted_facts": Path("case_demo_happy_path/export/demo/extracted-facts.json"),
        "safety_check_result": Path("case_demo_happy_path/safety/demo/safety-check-result.json"),
        "safety_check_examples": Path("case_demo_happy_path/safety/demo/safety-check-examples.json"),
        "handoff_payload": Path("case_demo_happy_path/export/demo/doctor-handoff.json"),
        "source_references": Path("case_demo_happy_path/export/demo/source-references.json"),
        "shared_status": Path("case_demo_happy_path/export/demo/shared-status.json"),
        "processing_result": Path("case_demo_happy_path/export/demo/processing-result.json"),
        "structured_extraction_examples": Path(
            "case_demo_happy_path/export/demo/structured-extraction-examples.json"
        ),
        "rag_provenance_examples": Path("case_demo_happy_path/export/demo/rag-provenance-examples.json"),
        "summary_draft": Path("case_demo_happy_path/summary/demo/summary-draft.json"),
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
    assert '"case_id": "case_demo_happy_path"' in shared_status_json

    structured_examples_json = (
        settings.artifact_root_dir
        / expected_relative_paths["structured_extraction_examples"]
    ).read_text(encoding="utf-8")
    assert '"data_classification": "synthetic_anonymized_demo"' in structured_examples_json
    assert '"uncertainty_reason": "missing_unit"' in structured_examples_json

    rag_examples_json = (
        settings.artifact_root_dir / expected_relative_paths["rag_provenance_examples"]
    ).read_text(encoding="utf-8")
    assert '"data_classification": "synthetic_anonymized_demo"' in rag_examples_json
    assert '"grounded": true' in rag_examples_json
    assert '"grounded": false' in rag_examples_json
    assert '"no_trustworthy_knowledge_entries_found"' in rag_examples_json

    safety_examples_json = (
        settings.artifact_root_dir / expected_relative_paths["safety_check_examples"]
    ).read_text(encoding="utf-8")
    assert '"decision": "pass"' in safety_examples_json
    assert '"decision": "blocked"' in safety_examples_json
    assert '"decision": "corrected"' in safety_examples_json
    assert '"data_classification": "synthetic_anonymized_demo"' in safety_examples_json


def test_seed_demo_case_is_deterministic_across_reruns(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)

    def clock() -> datetime:
        return datetime(2026, 5, 1, 6, 0, tzinfo=UTC)

    first = seed_demo_case(settings=settings, clock=clock)
    second = seed_demo_case(settings=settings, clock=clock)

    assert first.case_id == second.case_id == DEMO_CASE_ID
    assert first.handoff_delivery.case_id == second.handoff_delivery.case_id == DEMO_CASE_ID
    assert first.handoff_delivery.notification is not None
    assert second.handoff_delivery.notification is not None
    assert (
        first.handoff_delivery.notification.shared_status
        == second.handoff_delivery.notification.shared_status
    )
    assert first.safety_result == second.safety_result
    assert first.artifacts == second.artifacts

    rag_examples_path = (
        settings.artifact_root_dir
        / "case_demo_happy_path"
        / "export"
        / "demo"
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
        / "case_demo_happy_path"
        / "safety"
        / "demo"
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

    result = seed_demo_case(
        settings=settings,
        clock=clock,
    )

    assert result.handoff_delivery.notification is not None
    assert result.handoff_delivery.notification.shared_status.value == "ready_for_doctor"
    rag_examples_path = (
        settings.artifact_root_dir
        / "case_demo_happy_path"
        / "export"
        / "demo"
        / "rag-provenance-examples.json"
    )
    assert rag_examples_path.exists()
    safety_examples_path = (
        settings.artifact_root_dir
        / "case_demo_happy_path"
        / "safety"
        / "demo"
        / "safety-check-examples.json"
    )
    assert safety_examples_path.exists()
