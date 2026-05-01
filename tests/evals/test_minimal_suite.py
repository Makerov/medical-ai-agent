from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.settings import Settings
from app.evals.minimal_suite import MinimalEvalSuite


def _write_demo_artifacts(root: Path, case_id: str) -> None:
    demo_dir = root / case_id / "export" / "demo"
    (root / case_id / "safety" / "demo").mkdir(parents=True, exist_ok=True)
    demo_dir.mkdir(parents=True, exist_ok=True)
    (demo_dir / "structured-extraction-examples.json").write_text(
        json.dumps(
            {
                "case_id": case_id,
                "data_classification": "synthetic_anonymized_demo",
                "indicators": [
                    {
                        "name": "Hemoglobin",
                        "value": 13.2,
                        "unit": "g/dL",
                        "confidence": 0.98,
                        "source_document_reference": {"record_id": "doc-1"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (demo_dir / "rag-provenance-examples.json").write_text(
        json.dumps(
            {
                "case_id": case_id,
                "data_classification": "synthetic_anonymized_demo",
                "examples": [
                    {
                        "example_id": "grounded_hemoglobin_provenance",
                        "grounded": True,
                        "summary_reference": {"case_id": case_id, "record_id": "summary-1"},
                    },
                    {
                        "example_id": "not_grounded_creatinine_provenance",
                        "grounded": False,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / case_id / "safety" / "demo" / "safety-check-examples.json").write_text(
        json.dumps(
            {
                "case_id": case_id,
                "data_classification": "synthetic_anonymized_demo",
                "examples": [
                    {"decision": "pass", "issues": []},
                    {"decision": "blocked", "issues": [{"category": "diagnosis_language"}]},
                    {"decision": "corrected", "issues": []},
                ],
            }
        ),
        encoding="utf-8",
    )


def test_minimal_eval_suite_writes_case_linked_synthetic_results(tmp_path: Path) -> None:
    case_id = "case_demo_happy_path"
    _write_demo_artifacts(tmp_path, case_id)
    settings = Settings(artifact_root_dir=tmp_path, doctor_telegram_id_allowlist=(123456,))

    result = MinimalEvalSuite(settings=settings).run(case_id=case_id)

    assert result.summary.case_id == case_id
    assert result.summary.data_classification == "synthetic_anonymized_demo"
    assert result.summary.synthetic_by_default is True
    assert result.artifact_path == tmp_path / case_id / "demo" / "minimal-eval-suite.json"
    assert result.artifact_path.exists()

    payload = json.loads(result.artifact_path.read_text(encoding="utf-8"))
    assert payload["case_id"] == case_id
    assert [item["category"] for item in payload["results"]] == [
        "extraction",
        "groundedness",
        "safety",
    ]
    assert payload["results"][0]["threshold_signal"] == "required_fields_present"
    assert payload["results"][1]["fixture_id"] == "grounded_hemoglobin_provenance"
    assert payload["results"][2]["failure_reason"] is None


def test_minimal_eval_suite_reruns_with_stable_artifact_shape(tmp_path: Path, monkeypatch) -> None:
    case_id = "case_demo_happy_path"
    _write_demo_artifacts(tmp_path, case_id)
    settings = Settings(artifact_root_dir=tmp_path, doctor_telegram_id_allowlist=(123456,))

    class FrozenDateTime:
        @staticmethod
        def now(tz=None):
            return datetime(2026, 5, 1, 6, 0, tzinfo=UTC)

    import app.evals.minimal_suite as minimal_suite_module

    monkeypatch.setattr(minimal_suite_module, "datetime", FrozenDateTime)

    first = MinimalEvalSuite(settings=settings).run(case_id=case_id)
    second = MinimalEvalSuite(settings=settings).run(case_id=case_id)

    assert first.artifact_path == second.artifact_path
    assert first.summary.case_id == second.summary.case_id == case_id
    assert [result.fixture_id for result in first.summary.results] == [
        result.fixture_id for result in second.summary.results
    ]
    assert [result.category for result in first.summary.results] == [
        result.category for result in second.summary.results
    ]
