from datetime import UTC, datetime
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
        "handoff_payload": Path("case_demo_happy_path/export/demo/doctor-handoff.json"),
        "source_references": Path("case_demo_happy_path/export/demo/source-references.json"),
        "shared_status": Path("case_demo_happy_path/export/demo/shared-status.json"),
        "processing_result": Path("case_demo_happy_path/export/demo/processing-result.json"),
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
