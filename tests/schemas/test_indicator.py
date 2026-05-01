from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.document import DocumentUploadMetadata
from app.schemas.indicator import (
    CaseIndicatorExtractionRecord,
    StructuredMedicalIndicator,
)


def test_structured_medical_indicator_validates_and_normalizes_text_fields() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    source_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=now,
    )

    indicator = StructuredMedicalIndicator(
        case_id="case_001",
        name=" Hemoglobin ",
        value=13.5,
        unit=" g/dL ",
        confidence=0.81,
        source_document_reference=source_reference,
        extracted_at=now,
        provider_name="stub",
    )

    assert indicator.name == "Hemoglobin"
    assert indicator.unit == "g/dL"
    assert indicator.value == 13.5
    assert indicator.source_document_reference == source_reference


def test_structured_medical_indicator_requires_complete_fields_for_reliable_fact() -> None:
    source_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
    )

    with pytest.raises(ValidationError, match="Reliable indicators must include value and unit"):
        StructuredMedicalIndicator(
            case_id="case_001",
            name="Hemoglobin",
            value=13.5,
            unit=None,
            confidence=0.81,
            source_document_reference=source_reference,
            extracted_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        )


def test_structured_medical_indicator_allows_explicit_uncertainty_metadata() -> None:
    source_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
    )

    indicator = StructuredMedicalIndicator(
        case_id="case_001",
        name="Hemoglobin",
        value=13.5,
        unit=None,
        confidence=0.74,
        source_document_reference=source_reference,
        extracted_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        is_uncertain=True,
        uncertainty_reason="missing_unit",
        missing_fields=("unit",),
    )

    assert indicator.is_uncertain is True
    assert indicator.uncertainty_reason == "missing_unit"
    assert indicator.missing_fields == ("unit",)


def test_structured_medical_indicator_rejects_uncertain_fact_without_reason() -> None:
    source_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
    )

    with pytest.raises(ValidationError, match="uncertainty reason"):
        StructuredMedicalIndicator(
            case_id="case_001",
            name="Hemoglobin",
            value=13.5,
            unit=None,
            confidence=0.74,
            source_document_reference=source_reference,
            extracted_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
            is_uncertain=True,
        )


def test_structured_medical_indicator_rejects_mismatched_case_reference() -> None:
    source_reference = CaseRecordReference(
        case_id="case_002",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_002",
        created_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
    )

    with pytest.raises(ValidationError, match="same case"):
        StructuredMedicalIndicator(
            case_id="case_001",
            name="Hemoglobin",
            value=13.5,
            unit="g/dL",
            confidence=0.81,
            source_document_reference=source_reference,
            extracted_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        )


def test_structured_medical_indicator_rejects_naive_timestamp() -> None:
    source_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
    )

    with pytest.raises(ValidationError, match="timezone-aware"):
        StructuredMedicalIndicator(
            case_id="case_001",
            name="Hemoglobin",
            value=13.5,
            unit="g/dL",
            confidence=0.81,
            source_document_reference=source_reference,
            extracted_at=datetime(2026, 4, 28, 6, 0),
        )


def test_case_indicator_extraction_record_validates_linkage_and_bucket_kind() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    source_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=now,
    )
    raw_extraction_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.EXTRACTION,
        record_id="extraction_001",
        created_at=now,
    )
    indicator_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.INDICATOR,
        record_id="structured_indicator:document_001",
        created_at=now,
    )
    document = DocumentUploadMetadata(
        file_id="file_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_001",
    )
    indicator = StructuredMedicalIndicator(
        case_id="case_001",
        name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        confidence=0.81,
        source_document_reference=source_reference,
        extracted_at=now,
    )

    record = CaseIndicatorExtractionRecord(
        case_id="case_001",
        source_document=document,
        source_document_reference=source_reference,
        raw_extraction_reference=raw_extraction_reference,
        indicator_reference=indicator_reference,
        indicators=(indicator,),
        extracted_at=now,
        provider_name="stub",
    )

    assert record.indicators == (indicator,)
    assert record.indicator_reference == indicator_reference


def test_case_indicator_extraction_record_separates_reliable_and_uncertain_subsets() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    source_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=now,
    )
    raw_extraction_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.EXTRACTION,
        record_id="extraction_001",
        created_at=now,
    )
    indicator_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.INDICATOR,
        record_id="structured_indicator:document_001",
        created_at=now,
    )
    document = DocumentUploadMetadata(
        file_id="file_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_001",
    )
    reliable_indicator = StructuredMedicalIndicator(
        case_id="case_001",
        name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        confidence=0.91,
        source_document_reference=source_reference,
        extracted_at=now,
    )
    uncertain_indicator = StructuredMedicalIndicator(
        case_id="case_001",
        name="Glucose",
        value=5.6,
        unit=None,
        confidence=0.91,
        source_document_reference=source_reference,
        extracted_at=now,
        is_uncertain=True,
        uncertainty_reason="missing_unit",
        missing_fields=("unit",),
    )

    record = CaseIndicatorExtractionRecord(
        case_id="case_001",
        source_document=document,
        source_document_reference=source_reference,
        raw_extraction_reference=raw_extraction_reference,
        indicator_reference=indicator_reference,
        indicators=(reliable_indicator,),
        uncertain_indicators=(uncertain_indicator,),
        extracted_at=now,
        provider_name="stub",
    )

    assert record.indicators == (reliable_indicator,)
    assert record.uncertain_indicators == (uncertain_indicator,)


def test_case_indicator_extraction_record_rejects_uncertain_indicator_in_reliable_subset() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    source_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=now,
    )
    raw_extraction_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.EXTRACTION,
        record_id="extraction_001",
        created_at=now,
    )
    indicator_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.INDICATOR,
        record_id="structured_indicator:document_001",
        created_at=now,
    )
    document = DocumentUploadMetadata(
        file_id="file_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_001",
    )
    uncertain_indicator = StructuredMedicalIndicator(
        case_id="case_001",
        name="Glucose",
        value=5.6,
        unit=None,
        confidence=0.91,
        source_document_reference=source_reference,
        extracted_at=now,
        is_uncertain=True,
        uncertainty_reason="missing_unit",
        missing_fields=("unit",),
    )

    with pytest.raises(ValidationError, match="Reliable indicators must not be marked uncertain"):
        CaseIndicatorExtractionRecord(
            case_id="case_001",
            source_document=document,
            source_document_reference=source_reference,
            raw_extraction_reference=raw_extraction_reference,
            indicator_reference=indicator_reference,
            indicators=(uncertain_indicator,),
            extracted_at=now,
        )


def test_case_indicator_extraction_record_rejects_wrong_reference_kind() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    source_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=now,
    )
    raw_extraction_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="extraction_001",
        created_at=now,
    )
    indicator_reference = CaseRecordReference(
        case_id="case_001",
        record_kind=CaseRecordKind.INDICATOR,
        record_id="structured_indicator:document_001",
        created_at=now,
    )
    document = DocumentUploadMetadata(
        file_id="file_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_001",
    )

    with pytest.raises(ValidationError, match="extraction reference"):
        CaseIndicatorExtractionRecord(
            case_id="case_001",
            source_document=document,
            source_document_reference=source_reference,
            raw_extraction_reference=raw_extraction_reference,
            indicator_reference=indicator_reference,
            indicators=(),
            extracted_at=now,
        )
