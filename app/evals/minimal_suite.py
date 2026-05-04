from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
        output_dir = self._resolve_output_dir(case_id=case_id)
        artifact_path = output_dir / "minimal-eval-suite.json"
        results = (
            self._build_extraction_check(case_id=case_id),
            self._build_groundedness_check(case_id=case_id),
            self._build_safety_check(case_id=case_id),
        )
        summary = EvalSuiteSummary(
            case_id=case_id,
            generated_at=datetime.now(UTC),
            data_classification="synthetic_anonymized_verification",
            results=results,
            artifact_path=str(artifact_path.relative_to(artifact_root)),
        )
        self._write_json(artifact_path, summary.model_dump(mode="json"))
        return MinimalEvalSuiteResult(summary=summary, artifact_path=artifact_path)

    def _build_extraction_check(self, *, case_id: str) -> EvalCheckResult:
        path = self._resolve_input_path(
            case_id=case_id,
            verification_path="export/verification/structured-extraction-examples.json",
            legacy_demo_path="export/demo/structured-extraction-examples.json",
        )
        payload = self._read_artifact(path)
        if payload is None:
            return EvalCheckResult(
                category="extraction",
                fixture_id="structured_extraction_examples",
                case_id=case_id,
                outcome="fail",
                score=0.0,
                threshold_signal="missing_source_artifact",
                failure_reason="Structured extraction artifact could not be found",
                source_artifact=path,
            )
        indicators = self._extract_indicators(payload)
        if not indicators:
            return EvalCheckResult(
                category="extraction",
                fixture_id="structured_extraction_examples",
                case_id=case_id,
                outcome="fail",
                score=0.0,
                threshold_signal="missing_required_fields",
                failure_reason="Structured extraction example did not include any indicators",
                source_artifact=path,
            )
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
                failure_reason=(
                    "Structured extraction example is missing required fields: "
                    f"{', '.join(missing)}"
                ),
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

    @staticmethod
    def _extract_indicators(payload: object) -> list[dict[str, object]]:
        if isinstance(payload, list):
            indicators: list[dict[str, object]] = []
            for entry in payload:
                if not isinstance(entry, dict):
                    continue
                raw_indicators = entry.get("indicators")
                if not isinstance(raw_indicators, list):
                    continue
                indicators.extend(
                    indicator for indicator in raw_indicators if isinstance(indicator, dict)
                )
            return indicators
        if isinstance(payload, dict):
            raw_indicators = payload.get("indicators")
            if isinstance(raw_indicators, list):
                return [indicator for indicator in raw_indicators if isinstance(indicator, dict)]
        return []

    def _build_groundedness_check(self, *, case_id: str) -> EvalCheckResult:
        path = self._resolve_input_path(
            case_id=case_id,
            verification_path="export/verification/rag-provenance-examples.json",
            legacy_demo_path="export/demo/rag-provenance-examples.json",
        )
        payload = self._read_artifact(path)
        if payload is None:
            return EvalCheckResult(
                category="groundedness",
                fixture_id="grounded_provenance_examples",
                case_id=case_id,
                outcome="fail",
                score=0.0,
                threshold_signal="missing_source_artifact",
                failure_reason="RAG provenance artifact could not be found",
                source_artifact=path,
            )
        examples = payload.get("examples")
        if not isinstance(examples, list):
            return EvalCheckResult(
                category="groundedness",
                fixture_id="grounded_provenance_examples",
                case_id=case_id,
                outcome="fail",
                score=0.0,
                threshold_signal="missing_required_fields",
                failure_reason="RAG provenance artifact is missing the examples list",
                source_artifact=path,
            )
        grounded = next(
            (
                example
                for example in examples
                if isinstance(example, dict) and example.get("grounded") is True
            ),
            None,
        )
        if grounded is None:
            return EvalCheckResult(
                category="groundedness",
                fixture_id="grounded_provenance_examples",
                case_id=case_id,
                outcome="fail",
                score=0.0,
                threshold_signal="missing_grounded_example",
                failure_reason="RAG provenance examples did not include a grounded example",
                source_artifact=path,
            )
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
        path = self._resolve_input_path(
            case_id=case_id,
            verification_path="safety/verification/safety-check-examples.json",
            legacy_demo_path="safety/demo/safety-check-examples.json",
        )
        payload = self._read_artifact(path)
        if payload is None:
            return EvalCheckResult(
                category="safety",
                fixture_id=f"{case_id}:blocked_example",
                case_id=case_id,
                outcome="fail",
                score=0.0,
                threshold_signal="missing_source_artifact",
                failure_reason="Safety example artifact could not be found",
                source_artifact=path,
            )
        examples = payload.get("examples")
        if not isinstance(examples, list):
            return EvalCheckResult(
                category="safety",
                fixture_id=f"{case_id}:blocked_example",
                case_id=case_id,
                outcome="fail",
                score=0.0,
                threshold_signal="missing_required_fields",
                failure_reason="Safety example artifact is missing the examples list",
                source_artifact=path,
            )
        blocked = next(
            (
                example
                for example in examples
                if isinstance(example, dict) and example.get("decision") == "blocked"
            ),
            None,
        )
        if blocked is None:
            return EvalCheckResult(
                category="safety",
                fixture_id=f"{case_id}:blocked_example",
                case_id=case_id,
                outcome="fail",
                score=0.0,
                threshold_signal="missing_safety_block",
                failure_reason="Safety examples did not include a blocked decision",
                source_artifact=path,
            )
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

    def _read_artifact(self, relative_path: str) -> dict[str, Any] | None:
        artifact_path = Path(self._settings.artifact_root_dir) / relative_path
        if not artifact_path.exists():
            return None
        return json.loads(artifact_path.read_text(encoding="utf-8"))

    def _resolve_input_path(
        self,
        *,
        case_id: str,
        verification_path: str,
        legacy_demo_path: str,
    ) -> str:
        artifact_root = Path(self._settings.artifact_root_dir)
        verification_candidate = artifact_root / case_id / verification_path
        if verification_candidate.exists():
            return f"{case_id}/{verification_path}"
        legacy_candidate = artifact_root / case_id / legacy_demo_path
        if legacy_candidate.exists():
            return f"{case_id}/{legacy_demo_path}"
        return f"{case_id}/{verification_path}"

    def _resolve_output_dir(self, *, case_id: str) -> Path:
        artifact_root = Path(self._settings.artifact_root_dir)
        verification_dir = artifact_root / case_id / "verification"
        if verification_dir.exists():
            return verification_dir
        legacy_demo_dir = artifact_root / case_id / "demo"
        if legacy_demo_dir.exists():
            return legacy_demo_dir
        return verification_dir

    @staticmethod
    def _write_json(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
