from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path
from typing import Any

from app.schemas.demo_export import (
    DemoArtifactExportContract,
    DemoExportArtifactReference,
    DemoExportOverview,
)
from scripts.seed_operational_verification_case import (
    SeededOperationalVerificationCaseResult,
    seed_operational_verification_case,
)

DEMO_CASE_FIXTURE_PATH = Path("data/demo_cases/seed_demo_case.json")
DEMO_CASE_ID = "case_demo_happy_path"
SeededDemoCaseResult = SeededOperationalVerificationCaseResult


def load_demo_case_fixture(path: Path = DEMO_CASE_FIXTURE_PATH):
    if not path.exists():
        msg = f"Demo case fixture does not exist: {path}"
        raise FileNotFoundError(msg)
    return json.loads(path.read_text(encoding="utf-8"))


def seed_demo_case(
    *,
    fixture_path: Path = DEMO_CASE_FIXTURE_PATH,
    **kwargs: Any,
) -> SeededDemoCaseResult:
    result = seed_operational_verification_case(
        fixture_path=fixture_path,
        **kwargs,
    )
    artifact_root = _resolve_artifact_root(result=result)
    legacy_artifacts = _write_legacy_demo_artifacts(
        result=result,
        artifact_root=artifact_root,
    )
    return SeededDemoCaseResult(
        case_id=result.case_id,
        intake_payload=result.intake_payload,
        document=result.document,
        extraction_text=result.extraction_text,
        safety_result=result.safety_result,
        handoff_delivery=result.handoff_delivery,
        artifacts=legacy_artifacts,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Deprecated compatibility wrapper. "
            "Use scripts/seed_operational_verification_case.py instead."
        )
    )
    parser.add_argument("--fixture", default=str(DEMO_CASE_FIXTURE_PATH))
    parser.add_argument("--no-reset", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    warnings.warn(
        "scripts/seed_demo_case.py is deprecated; use "
        "scripts/seed_operational_verification_case.py instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    parser = build_parser()
    args = parser.parse_args(argv)
    result = seed_demo_case(
        fixture_path=Path(args.fixture),
        reset_artifacts=not args.no_reset,
    )
    print(f"Seeded demo compatibility case {result.case_id}")
    print(f"Artifacts written under {Path('data/artifacts') / result.case_id}")
    return 0


def _resolve_artifact_root(*, result: SeededOperationalVerificationCaseResult) -> Path:
    example_path = next(iter(result.artifacts.values()))
    return example_path.parents[3]


def _write_legacy_demo_artifacts(
    *,
    result: SeededOperationalVerificationCaseResult,
    artifact_root: Path,
) -> dict[str, Path]:
    legacy_paths = {
        "intake_snapshot": ("export/demo/intake-snapshot.json", "intake_snapshot"),
        "extracted_facts": ("export/demo/extracted-facts.json", "extracted_facts"),
        "safety_check_result": ("safety/demo/safety-check-result.json", "safety_check_result"),
        "safety_check_examples": (
            "safety/demo/safety-check-examples.json",
            "safety_check_examples",
        ),
        "handoff_payload": ("export/demo/doctor-handoff.json", "handoff_payload"),
        "source_references": ("export/demo/source-references.json", "source_references"),
        "shared_status": ("export/demo/shared-status.json", "shared_status"),
        "processing_result": ("export/demo/processing-result.json", "processing_result"),
        "structured_extraction_examples": (
            "export/demo/structured-extraction-examples.json",
            "structured_extraction_examples",
        ),
        "rag_provenance_examples": (
            "export/demo/rag-provenance-examples.json",
            "rag_provenance_examples",
        ),
        "summary_draft": ("summary/demo/summary-draft.json", "summary_draft"),
    }
    legacy_artifacts: dict[str, Path] = {}
    for artifact_name, (legacy_suffix, source_key) in legacy_paths.items():
        target_path = artifact_root / result.case_id / legacy_suffix
        target_path.parent.mkdir(parents=True, exist_ok=True)
        source_path = result.artifacts[source_key]
        target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
        legacy_artifacts[artifact_name] = target_path.resolve(strict=False)

    legacy_export_path = artifact_root / result.case_id / "demo" / "reviewer-export.json"
    legacy_export_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_export = _build_legacy_demo_export_contract(
        case_id=result.case_id,
        artifact_root=artifact_root,
        legacy_artifacts=legacy_artifacts,
        generated_at=_read_generated_at(result.artifacts["verification_export_contract"]),
    )
    legacy_export_path.write_text(
        json.dumps(
            legacy_export.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    legacy_artifacts["demo_export_contract"] = legacy_export_path.resolve(strict=False)
    return legacy_artifacts


def _read_generated_at(export_contract_path: Path):
    payload = json.loads(export_contract_path.read_text(encoding="utf-8"))
    return DemoArtifactExportContract.model_validate(payload).generated_at


def _build_legacy_demo_export_contract(
    *,
    case_id: str,
    artifact_root: Path,
    legacy_artifacts: dict[str, Path],
    generated_at,
) -> DemoArtifactExportContract:
    def rel(key: str) -> str:
        return legacy_artifacts[key].relative_to(artifact_root).as_posix()

    overview = DemoExportOverview(
        case_id=case_id,
        title="Stable demo artifact export",
        generated_at=generated_at,
        data_classification="synthetic_anonymized_demo",
        reviewer_notes="Synthetic, case-scoped export bundle for reviewer walkthrough without live model calls.",
        non_goals=(
            "No autonomous diagnosis or treatment guidance.",
            "No real patient documents required.",
            "No production deployment claim.",
        ),
    )
    required_artifacts = (
        DemoExportArtifactReference(
            label="structured_extraction_examples",
            artifact_path=rel("structured_extraction_examples"),
            description="Structured extraction example payloads derived from the stable demo case.",
        ),
        DemoExportArtifactReference(
            label="rag_provenance_examples",
            artifact_path=rel("rag_provenance_examples"),
            description="Grounded and not-grounded provenance examples with summary linkage.",
        ),
        DemoExportArtifactReference(
            label="safety_check_result",
            artifact_path=rel("safety_check_result"),
            description="Typed safety decision for the doctor-facing summary draft.",
        ),
        DemoExportArtifactReference(
            label="minimal_eval_suite",
            artifact_path=f"{case_id}/demo/minimal-eval-suite.json",
            description="Minimal eval summary showing extraction, groundedness, and safety checks.",
        ),
    )
    optional_artifacts = (
        DemoExportArtifactReference(
            label="shared_status",
            artifact_path=rel("shared_status"),
            description="Reviewer-readable case overview and current status snapshot.",
            optional=True,
        ),
        DemoExportArtifactReference(
            label="summary_draft",
            artifact_path=rel("summary_draft"),
            description="Grounded summary draft used by the handoff path.",
            optional=True,
        ),
    )
    derived_artifacts = (
        DemoExportArtifactReference(
            label="intake_snapshot",
            artifact_path=rel("intake_snapshot"),
            description="Synthetic intake snapshot derived from the stable demo case.",
        ),
        DemoExportArtifactReference(
            label="doctor_handoff",
            artifact_path=rel("handoff_payload"),
            description="Case-linked handoff payload with the same stable case identifier.",
        ),
    )
    return DemoArtifactExportContract(
        case_id=case_id,
        generated_at=generated_at,
        data_classification="synthetic_anonymized_demo",
        overview=overview,
        required_artifacts=required_artifacts,
        optional_artifacts=optional_artifacts,
        derived_artifacts=derived_artifacts,
        export_path=f"{case_id}/demo/reviewer-export.json",
    )


if __name__ == "__main__":
    raise SystemExit(main())
