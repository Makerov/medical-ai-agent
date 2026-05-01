from datetime import UTC, datetime

import pytest

from app.schemas.demo_export import (
    DemoArtifactExportContract,
    DemoExportArtifactReference,
    DemoExportOverview,
)


def test_demo_export_contract_requires_case_linked_artifacts() -> None:
    overview = DemoExportOverview(
        case_id="case_demo_happy_path",
        title="Reviewer-ready demo artifact export",
        generated_at=datetime(2026, 5, 1, 6, 0, tzinfo=UTC),
        data_classification="synthetic_anonymized_demo",
        reviewer_notes="Synthetic demo export.",
    )

    with pytest.raises(ValueError, match="Demo export artifacts must remain case-scoped"):
        DemoArtifactExportContract(
            case_id="case_demo_happy_path",
            generated_at=datetime(2026, 5, 1, 6, 0, tzinfo=UTC),
            data_classification="synthetic_anonymized_demo",
            overview=overview,
            required_artifacts=(
                DemoExportArtifactReference(
                    label="structured_extraction_examples",
                    artifact_path="another_case/export/demo/structured-extraction-examples.json",
                    description="Structured extraction example payload.",
                ),
            ),
            export_path="case_demo_happy_path/demo/reviewer-export.json",
        )

