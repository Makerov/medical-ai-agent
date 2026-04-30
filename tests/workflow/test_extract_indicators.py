from datetime import UTC, datetime

from app.schemas.case import CaseRecordKind, CaseRecordReference, CaseStatus
from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import DocumentProcessingResult, OCRTextExtractionResult
from app.services.case_service import CaseService
from app.workflow.nodes.extract_indicators import ExtractIndicatorsNode


def _build_document_processing_result(
    *,
    case_id: str,
    document: DocumentUploadMetadata,
    now: datetime,
    case_status: CaseStatus,
    extracted_text: str | None,
) -> DocumentProcessingResult:
    source_reference = CaseRecordReference(
        case_id=case_id,
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="telegram_document:unique_001",
        created_at=now,
    )
    extraction_reference = (
        CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.EXTRACTION,
            record_id="extraction:telegram_document:unique_001",
            created_at=now,
        )
        if extracted_text is not None
        else None
    )
    extraction = (
        OCRTextExtractionResult(
            source_document=document,
            extracted_text=extracted_text,
            confidence=0.91,
            extracted_at=now,
            provider_name="stub",
        )
        if extracted_text is not None
        else None
    )
    return DocumentProcessingResult(
        case_id=case_id,
        case_status=case_status,
        source_document=document,
        source_document_reference=source_reference,
        extraction_reference=extraction_reference,
        extraction=extraction,
    )


def test_extract_indicators_node_processes_successful_document_result() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_node_001")
    patient_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_node_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_001",
    )
    node = ExtractIndicatorsNode(case_service=case_service)
    processing_result = _build_document_processing_result(
        case_id=patient_case.case_id,
        document=document,
        now=now,
        case_status=CaseStatus.PROCESSING_DOCUMENTS,
        extracted_text="Hemoglobin: 13.5 g/dL",
    )

    indicator_record = node.extract_indicators(processing_result=processing_result)

    assert indicator_record is not None
    assert indicator_record.case_id == patient_case.case_id
    assert indicator_record.indicators[0].name == "Hemoglobin"
    assert case_service.get_case_core_records(patient_case.case_id).indicators == (
        indicator_record.indicator_reference,
    )


def test_extract_indicators_node_skips_partial_extraction_results() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_node_002")
    patient_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_node_002",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_002",
    )
    node = ExtractIndicatorsNode(case_service=case_service)
    processing_result = _build_document_processing_result(
        case_id=patient_case.case_id,
        document=document,
        now=now,
        case_status=CaseStatus.PARTIAL_EXTRACTION,
        extracted_text="Hemoglobin: 13.5 g/dL",
    )

    indicator_record = node.extract_indicators(processing_result=processing_result)

    assert indicator_record is None
    assert case_service.get_case_indicator_records(patient_case.case_id) == ()
