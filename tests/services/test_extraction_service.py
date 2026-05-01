from datetime import UTC, datetime

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import CaseExtractionRecord
from app.services.case_service import CaseService
from app.services.extraction_service import ExtractionService


def _build_extraction_record(
    *,
    case_id: str,
    now: datetime,
    extracted_text: str,
) -> CaseExtractionRecord:
    document = DocumentUploadMetadata(
        file_id="file_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_001",
    )
    source_reference = CaseRecordReference(
        case_id=case_id,
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="telegram_document:unique_001",
        created_at=now,
    )
    extraction_reference = CaseRecordReference(
        case_id=case_id,
        record_kind=CaseRecordKind.EXTRACTION,
        record_id="extraction:telegram_document:unique_001",
        created_at=now,
    )
    return CaseExtractionRecord(
        case_id=case_id,
        source_document=document,
        source_document_reference=source_reference,
        extraction_reference=extraction_reference,
        extracted_text=extracted_text,
        confidence=0.91,
        extracted_at=now,
        provider_name="stub",
    )


def test_extract_indicators_creates_typed_records_and_attaches_case_bucket() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_indicator_001")
    patient_case = case_service.create_case()
    extraction_record = _build_extraction_record(
        case_id=patient_case.case_id,
        now=now,
        extracted_text="Hemoglobin: 13.5 g/dL\nGlucose: 5.6 mmol/L",
    )
    service = ExtractionService(case_service=case_service)

    indicator_record = service.extract_indicators(
        case_id=patient_case.case_id,
        extraction_record=extraction_record,
    )

    assert indicator_record is not None
    assert indicator_record.case_id == patient_case.case_id
    assert indicator_record.indicator_reference.record_kind == CaseRecordKind.INDICATOR
    assert indicator_record.indicators[0].name == "Hemoglobin"
    assert indicator_record.indicators[0].value == 13.5
    assert indicator_record.indicators[0].unit == "g/dL"
    assert indicator_record.indicators[0].source_document_reference == (
        extraction_record.source_document_reference
    )
    assert indicator_record.indicators[1].name == "Glucose"
    assert indicator_record.uncertain_indicators == ()
    assert case_service.get_case_indicator_records(patient_case.case_id) == (indicator_record,)
    assert case_service.get_case_core_records(patient_case.case_id).indicators == (
        indicator_record.indicator_reference,
    )


def test_extract_indicators_splits_reliable_and_uncertain_candidates() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_indicator_002")
    patient_case = case_service.create_case()
    extraction_record = _build_extraction_record(
        case_id=patient_case.case_id,
        now=now,
        extracted_text="Hemoglobin: 13.5 g/dL\nGlucose: 5.6",
    )
    service = ExtractionService(case_service=case_service)

    indicator_record = service.extract_indicators(
        case_id=patient_case.case_id,
        extraction_record=extraction_record,
    )

    assert indicator_record is not None
    assert indicator_record.indicators[0].name == "Hemoglobin"
    assert indicator_record.uncertain_indicators[0].name == "Glucose"
    assert indicator_record.uncertain_indicators[0].is_uncertain is True
    assert indicator_record.uncertain_indicators[0].uncertainty_reason == "missing_unit"
    assert case_service.get_case_indicator_records(patient_case.case_id) == (indicator_record,)


def test_extract_indicators_preserves_uncertain_only_candidates() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_indicator_003")
    patient_case = case_service.create_case()
    extraction_record = _build_extraction_record(
        case_id=patient_case.case_id,
        now=now,
        extracted_text="Hemoglobin: 13.5\nGlucose: 5.6",
    )
    service = ExtractionService(case_service=case_service)

    indicator_record = service.extract_indicators(
        case_id=patient_case.case_id,
        extraction_record=extraction_record,
    )

    assert indicator_record is not None
    assert indicator_record.indicators == ()
    assert len(indicator_record.uncertain_indicators) == 2
    assert case_service.get_case_indicator_records(patient_case.case_id) == (indicator_record,)
    assert case_service.get_case_core_records(patient_case.case_id).indicators == (
        indicator_record.indicator_reference,
    )


def test_extract_indicators_is_idempotent_for_repeated_execution() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_indicator_004")
    patient_case = case_service.create_case()
    extraction_record = _build_extraction_record(
        case_id=patient_case.case_id,
        now=now,
        extracted_text="Hemoglobin: 13.5 g/dL\nGlucose: 5.6",
    )
    service = ExtractionService(case_service=case_service)

    first_result = service.extract_indicators(
        case_id=patient_case.case_id,
        extraction_record=extraction_record,
    )
    second_result = service.extract_indicators(
        case_id=patient_case.case_id,
        extraction_record=extraction_record,
    )

    assert first_result == second_result
    assert len(case_service.get_case_indicator_records(patient_case.case_id)) == 1
    assert len(case_service.get_case_core_records(patient_case.case_id).indicators) == 1
    assert first_result is not None
    assert len(first_result.uncertain_indicators) == 1
