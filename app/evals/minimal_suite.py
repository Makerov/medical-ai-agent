from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.core.settings import Settings, get_settings
from app.schemas.eval import EvalCheckResult, EvalSuiteSummary


@dataclass(frozen=True)
class MinimalEvalSuiteResult:
    summary: EvalSuiteSummary
    artifact_path: Path


class MinimalEvalSuite:
    def __init__(self, *, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def run(self, *, case_id: str) -> MinimalEvalSuiteResult:
        artifact_root = Path(self._settings.artifact_root_dir)
        demo_dir = artifact_root / case_id / "demo"
        artifact_path = demo_dir / "minimal-eval-suite.json"
        results = (
            self._build_extraction_check(case_id=case_id),
            self._build_groundedness_check(case_id=case_id),
            self._build_safety_check(case_id=case_id),
        )
        summary = EvalSuiteSummary(
            case_id=case_id,
            generated_at=datetime.now(UTC),
            data_classification="synthetic_anonymized_demo",
            results=results,
            artifact_path=str(artifact_path.relative_to(artifact_root)),
        )
        self._write_json(artifact_path, summary.model_dump(mode="json"))
        return MinimalEvalSuiteResult(summary=summary, artifact_path=artifact_path)

    def _build_extraction_check(self, *, case_id: str) -> EvalCheckResult:
        path = f"{case_id}/export/demo/structured-extraction-examples.json"
        payload = self._read_artifact(path)
        indicators = payload["indicators"]
        missing = [
            field
            for field in ("name", "value", "unit", "confidence", "source_document_reference")
            if field not in indicators[0]
        ]
        if missing:
            return EvalCheckResult(
                category="extraction",
                fixture_id="structured_extraction_examples",
                case_id=case_id,
                outcome="fail",
                score=0.0,
                threshold_signal="missing_required_fields",
                failure_reason=f"Structured extraction example is missing required fields: {', '.join(missing)}",
                source_artifact=path,
            )
        return EvalCheckResult(
            category="extraction",
            fixture_id="structured_extraction_examples",
            case_id=case_id,
            outcome="pass",
            score=1.0,
            threshold_signal="required_fields_present",
            source_artifact=path,
        )

    def _build_groundedness_check(self, *, case_id: str) -> EvalCheckResult:
        path = f"{case_id}/export/demo/rag-provenance-examples.json"
        payload = self._read_artifact(path)
        examples = payload["examples"]
        grounded = next(example for example in examples if example["grounded"] is True)
        summary_reference = grounded.get("summary_reference")
        if summary_reference is None:
            return EvalCheckResult(
                category="groundedness",
                fixture_id=grounded["example_id"],
                case_id=case_id,
                outcome="fail",
                score=0.0,
                threshold_signal="missing_summary_link",
                failure_reason="Grounded provenance example is missing summary linkage",
                source_artifact=path,
            )
        return EvalCheckResult(
            category="groundedness",
            fixture_id=grounded["example_id"],
            case_id=case_id,
            outcome="pass",
            score=1.0,
            threshold_signal="traceable_source_link",
            source_artifact=path,
        )

    def _build_safety_check(self, *, case_id: str) -> EvalCheckResult:
        path = f"{case_id}/safety/demo/safety-check-examples.json"
        payload = self._read_artifact(path)
        blocked = next(example for example in payload["examples"] if example["decision"] == "blocked")
        issues = blocked.get("issues", [])
        if not issues:
            return EvalCheckResult(
                category="safety",
                fixture_id=f"{case_id}:blocked_example",
                case_id=case_id,
                outcome="fail",
                score=0.0,
                threshold_signal="missing_safety_block",
                failure_reason="Blocked safety example does not expose issues",
                source_artifact=path,
            )
        return EvalCheckResult(
            category="safety",
            fixture_id=f"{case_id}:blocked_example",
            case_id=case_id,
            outcome="pass",
            score=1.0,
            threshold_signal="unsafe_output_blocked",
            source_artifact=path,
        )

    def _read_artifact(self, relative_path: str) -> dict[str, object]:
        artifact_path = Path(self._settings.artifact_root_dir) / relative_path
        return json.loads(artifact_path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
