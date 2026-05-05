from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import (
    CaseExtractionRecord,
    OCRTextExtractionResult,
    StructuredExtractionExampleSet,
)
from app.schemas.indicator import StructuredMedicalIndicator


def _build_document_reference() -> CaseRecordReference:
    return CaseRecordReference(
        case_id="case_operational_verification_ready",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="telegram_document:unique_demo_001",
        created_at=datetime(2026, 5, 1, 6, 0, tzinfo=UTC),
    )


def _build_extraction_reference() -> CaseRecordReference:
    return CaseRecordReference(
        case_id="case_operational_verification_ready",
        record_kind=CaseRecordKind.EXTRACTION,
        record_id="extraction:telegram_document:unique_demo_001",
        created_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
    )


def _build_indicator_reference() -> CaseRecordReference:
    return CaseRecordReference(
        case_id="case_operational_verification_ready",
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
        case_id="case_operational_verification_ready",
        name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        confidence=0.95,
        source_document_reference=_build_document_reference(),
        extracted_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
        provider_name="synthetic_operational_verification_fixture",
    )
    uncertain_indicator = StructuredMedicalIndicator(
        case_id="case_operational_verification_ready",
        name="Ferritin",
        value=42,
        unit=None,
        confidence=0.61,
        source_document_reference=_build_document_reference(),
        extracted_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
        provider_name="synthetic_operational_verification_fixture",
        is_uncertain=True,
        uncertainty_reason="missing_unit",
        missing_fields=("unit",),
    )

    example_set = StructuredExtractionExampleSet(
        case_id="case_operational_verification_ready",
        data_classification="synthetic_anonymized_verification",
        source_document=source_document,
        source_document_reference=_build_document_reference(),
        raw_extraction_reference=_build_extraction_reference(),
        indicator_reference=_build_indicator_reference(),
        indicators=(reliable_indicator,),
        uncertain_indicators=(uncertain_indicator,),
        extracted_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
        provider_name="synthetic_operational_verification_fixture",
        example_note=(
            "Synthetic operational verification extraction example derived from the "
            "prepared anonymized case."
        ),
    )

    payload = example_set.model_dump(mode="json")

    assert payload["case_id"] == "case_operational_verification_ready"
    assert payload["data_classification"] == "synthetic_anonymized_verification"
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
            case_id="case_operational_verification_ready",
            data_classification="synthetic_anonymized_verification",
            source_document=source_document,
            source_document_reference=_build_document_reference(),
            raw_extraction_reference=_build_extraction_reference(),
            indicator_reference=_build_indicator_reference(),
            indicators=(
                StructuredMedicalIndicator(
                    case_id="case_operational_verification_ready",
                    name="Glucose",
                    value=5.6,
                    unit=None,
                    confidence=0.95,
                    source_document_reference=_build_document_reference(),
                    extracted_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
                    provider_name="synthetic_operational_verification_fixture",
                ),
            ),
            uncertain_indicators=(),
            extracted_at=datetime(2026, 5, 1, 6, 1, tzinfo=UTC),
            provider_name="synthetic_operational_verification_fixture",
        )


def test_case_extraction_record_retains_provider_name_and_case_linkage() -> None:
    now = datetime(2026, 5, 1, 6, 0, tzinfo=UTC)
    source_document = DocumentUploadMetadata(
        file_id="demo_lab_panel_pdf",
        file_name="synthetic-lab-panel.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="demo_lab_panel_pdf_v1",
    )
    extraction_record = CaseExtractionRecord(
        case_id="case_operational_verification_ready",
        source_document=source_document,
        source_document_reference=_build_document_reference(),
        extraction_reference=_build_extraction_reference(),
        extracted_text="Hemoglobin: 13.5 g/dL",
        confidence=0.91,
        extracted_at=now,
        provider_name="synthetic_operational_verification_fixture",
    )

    assert extraction_record.provider_name == "synthetic_operational_verification_fixture"
    assert extraction_record.source_document_reference.case_id == extraction_record.case_id


def test_ocr_text_extraction_result_rejects_naive_timestamp() -> None:
    source_document = DocumentUploadMetadata(
        file_id="demo_lab_panel_pdf",
        file_name="synthetic-lab-panel.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="demo_lab_panel_pdf_v1",
    )

    with pytest.raises(ValidationError, match="timezone-aware"):
        OCRTextExtractionResult(
            source_document=source_document,
            extracted_text="Hemoglobin: 13.5 g/dL",
            confidence=0.91,
            extracted_at=datetime(2026, 5, 1, 6, 0),
            provider_name="synthetic_operational_verification_fixture",
        )
