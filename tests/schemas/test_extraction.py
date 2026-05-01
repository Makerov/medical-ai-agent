from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import StructuredExtractionExampleSet
from app.schemas.indicator import StructuredMedicalIndicator


def _build_document_reference() -> CaseRecordReference:
    return CaseRecordReference(
        case_id="case_demo_happy_path",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="telegram_document:unique_demo_001",
        created_at=datetime(2026, 5, 1, 6, 0, tzinfo=UTC),
    )


def _build_extraction_reference() -> CaseRecordReference:
    return CaseRecordReference(
        case_id="case_demo_happy_path",
        record_kind=CaseRecordKind.EXTRACTION,
        record_id="extraction:telegram_document:unique_demo_001",
        created_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
    )


def _build_indicator_reference() -> CaseRecordReference:
    return CaseRecordReference(
        case_id="case_demo_happy_path",
        record_kind=CaseRecordKind.INDICATOR,
        record_id="structured_indicator:telegram_document:unique_demo_001",
        created_at=datetime(2026, 5, 1, 6, 2, tzinfo=UTC),
    )


def test_structured_extraction_example_set_exports_typed_shape() -> None:
    source_document = DocumentUploadMetadata(
        file_id="demo_lab_panel_pdf",
        file_name="synthetic-lab-panel.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="demo_lab_panel_pdf_v1",
    )
    reliable_indicator = StructuredMedicalIndicator(
        case_id="case_demo_happy_path",
        name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        confidence=0.95,
        source_document_reference=_build_document_reference(),
        extracted_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
        provider_name="synthetic_demo_fixture",
    )
    uncertain_indicator = StructuredMedicalIndicator(
        case_id="case_demo_happy_path",
        name="Ferritin",
        value=42,
        unit=None,
        confidence=0.61,
        source_document_reference=_build_document_reference(),
        extracted_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
        provider_name="synthetic_demo_fixture",
        is_uncertain=True,
        uncertainty_reason="missing_unit",
        missing_fields=("unit",),
    )

    example_set = StructuredExtractionExampleSet(
        case_id="case_demo_happy_path",
        data_classification="synthetic_anonymized_demo",
        source_document=source_document,
        source_document_reference=_build_document_reference(),
        raw_extraction_reference=_build_extraction_reference(),
        indicator_reference=_build_indicator_reference(),
        indicators=(reliable_indicator,),
        uncertain_indicators=(uncertain_indicator,),
        extracted_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
        provider_name="synthetic_demo_fixture",
        example_note="Synthetic demo extraction example derived from the stable seed case.",
    )

    payload = example_set.model_dump(mode="json")

    assert payload["case_id"] == "case_demo_happy_path"
    assert payload["data_classification"] == "synthetic_anonymized_demo"
    assert payload["source_document"]["file_id"] == "demo_lab_panel_pdf"
    assert payload["indicators"][0]["unit"] == "g/dL"
    assert payload["indicators"][0]["is_uncertain"] is False
    assert payload["uncertain_indicators"][0]["is_uncertain"] is True
    assert payload["uncertain_indicators"][0]["uncertainty_reason"] == "missing_unit"
    assert payload["uncertain_indicators"][0]["missing_fields"] == ["unit"]


def test_structured_extraction_example_set_rejects_invalid_reliable_subset() -> None:
    source_document = DocumentUploadMetadata(
        file_id="demo_lab_panel_pdf",
        file_name="synthetic-lab-panel.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="demo_lab_panel_pdf_v1",
    )

    with pytest.raises(ValidationError, match="Reliable indicators must include value and unit"):
        StructuredExtractionExampleSet(
            case_id="case_demo_happy_path",
            data_classification="synthetic_anonymized_demo",
            source_document=source_document,
            source_document_reference=_build_document_reference(),
            raw_extraction_reference=_build_extraction_reference(),
            indicator_reference=_build_indicator_reference(),
            indicators=(
                StructuredMedicalIndicator(
                    case_id="case_demo_happy_path",
                    name="Glucose",
                    value=5.6,
                    unit=None,
                    confidence=0.95,
                    source_document_reference=_build_document_reference(),
                    extracted_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
                    provider_name="synthetic_demo_fixture",
                ),
            ),
            uncertain_indicators=(),
            extracted_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
            provider_name="synthetic_demo_fixture",
        )
