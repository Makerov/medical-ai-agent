from datetime import UTC, datetime

from app.core.settings import Settings
from app.integrations.ocr_client import OCRClient
from app.schemas.case import CaseRecordKind, CaseRecordReference, CaseStatus
from app.schemas.document import DocumentUploadMetadata
from app.services.case_service import CaseService
from app.services.document_service import DocumentService
from app.workflow.nodes.parse_document import ParseDocumentNode


def _build_processed_case(
    *,
    case_service: CaseService,
    case_id: str,
    document: DocumentUploadMetadata,
    now: datetime,
) -> CaseRecordReference:
    case_service.transition_case(case_id, CaseStatus.AWAITING_CONSENT)
    case_service.transition_case(case_id, CaseStatus.COLLECTING_INTAKE)
    document_reference = DocumentService.build_document_reference(
        case_id=case_id,
        document_metadata=document,
        created_at=now,
    )
    case_service.attach_case_record_reference(document_reference)
    case_service.transition_case(case_id, CaseStatus.DOCUMENTS_UPLOADED)
    return document_reference


def test_parse_document_transitions_case_and_attaches_extraction_reference() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_parse_001")
    patient_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_parse_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_parse_001",
    )
    document_reference = _build_processed_case(
        case_service=case_service,
        case_id=patient_case.case_id,
        document=document,
        now=now,
    )

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw document bytes",
        document_parser=lambda _bytes, _document: ("  raw extracted text  ", 0.84),
        clock=lambda: now,
        provider_name="stub",
    )
    node = ParseDocumentNode(case_service=case_service, ocr_client=client)

    result = node.parse_document(case_id=patient_case.case_id, document=document)

    assert result.case_id == patient_case.case_id
    assert result.case_status == CaseStatus.PROCESSING_DOCUMENTS
    assert result.was_duplicate is False
    assert result.source_document_reference == document_reference
    assert result.extraction is not None
    assert result.extraction.extracted_text == "raw extracted text"
    assert result.extraction.confidence == 0.84
    assert result.extraction.provider_name == "stub"
    assert result.extraction_reference is not None
    assert result.extraction_reference.case_id == patient_case.case_id
    assert result.extraction_reference.record_kind == CaseRecordKind.EXTRACTION
    assert result.extraction_reference.record_id == (
        f"extraction:{document_reference.record_id}"
    )
    assert case_service.get_case_core_records(patient_case.case_id).extractions == (
        result.extraction_reference,
    )
    assert (
        case_service.get_case_core_records(patient_case.case_id).patient_case.status
        == CaseStatus.PROCESSING_DOCUMENTS
    )


def test_parse_document_routes_low_confidence_extraction_to_partial_extraction() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_parse_001_low")
    patient_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_parse_001_low",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_parse_001_low",
    )
    _build_processed_case(
        case_service=case_service,
        case_id=patient_case.case_id,
        document=document,
        now=now,
    )

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw document bytes",
        document_parser=lambda _bytes, _document: ("enough text for partial state", 0.41),
        clock=lambda: now,
        provider_name="stub",
    )
    node = ParseDocumentNode(
        case_service=case_service,
        ocr_client=client,
        settings=Settings(
            document_extraction_min_confidence=0.75,
            document_extraction_min_text_length=16,
        ),
    )

    result = node.parse_document(case_id=patient_case.case_id, document=document)

    assert result.case_id == patient_case.case_id
    assert result.case_status == CaseStatus.PARTIAL_EXTRACTION
    assert result.was_duplicate is False
    assert result.extraction is not None
    assert result.extraction_reference is not None
    assert case_service.get_case_core_records(patient_case.case_id).extractions == (
        result.extraction_reference,
    )
    assert (
        case_service.get_case_core_records(patient_case.case_id).patient_case.status
        == CaseStatus.PARTIAL_EXTRACTION
    )


def test_parse_document_routes_short_extraction_to_partial_extraction() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_parse_001_short")
    patient_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_parse_001_short",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_parse_001_short",
    )
    _build_processed_case(
        case_service=case_service,
        case_id=patient_case.case_id,
        document=document,
        now=now,
    )

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw document bytes",
        document_parser=lambda _bytes, _document: ("short", 0.96),
        clock=lambda: now,
        provider_name="stub",
    )
    node = ParseDocumentNode(
        case_service=case_service,
        ocr_client=client,
        settings=Settings(
            document_extraction_min_confidence=0.75,
            document_extraction_min_text_length=16,
        ),
    )

    result = node.parse_document(case_id=patient_case.case_id, document=document)

    assert result.case_status == CaseStatus.PARTIAL_EXTRACTION
    assert result.extraction is not None
    assert result.extraction.extracted_text == "short"
    assert result.extraction.confidence == 0.96
    assert (
        case_service.get_case_core_records(patient_case.case_id).patient_case.status
        == CaseStatus.PARTIAL_EXTRACTION
    )


def test_parse_document_skips_attach_when_partial_transition_fails() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_parse_001_fail")
    patient_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_parse_001_fail",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_parse_001_fail",
    )
    _build_processed_case(
        case_service=case_service,
        case_id=patient_case.case_id,
        document=document,
        now=now,
    )

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw document bytes",
        document_parser=lambda _bytes, _document: ("enough text for partial state", 0.41),
        clock=lambda: now,
        provider_name="stub",
    )
    node = ParseDocumentNode(
        case_service=case_service,
        ocr_client=client,
        settings=Settings(
            document_extraction_min_confidence=0.75,
            document_extraction_min_text_length=16,
        ),
    )
    node._mark_partial_extraction = lambda *, case_id: CaseStatus.READY_FOR_SUMMARY  # type: ignore[method-assign]

    result = node.parse_document(case_id=patient_case.case_id, document=document)

    assert result.extraction is None
    assert result.extraction_reference is None
    assert result.failure_code == "case_transition_failed"
    assert result.case_status == CaseStatus.READY_FOR_SUMMARY
    assert case_service.get_case_core_records(patient_case.case_id).extractions == ()
    assert (
        case_service.get_case_core_records(patient_case.case_id).patient_case.status
        == CaseStatus.PROCESSING_DOCUMENTS
    )


def test_parse_document_is_idempotent_for_repeated_job_execution() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_parse_002")
    patient_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_parse_002",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_parse_002",
    )
    _build_processed_case(
        case_service=case_service,
        case_id=patient_case.case_id,
        document=document,
        now=now,
    )

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw document bytes",
        document_parser=lambda _bytes, _document: ("raw extracted text", 0.79),
        clock=lambda: now,
    )
    node = ParseDocumentNode(case_service=case_service, ocr_client=client)

    first_result = node.parse_document(case_id=patient_case.case_id, document=document)
    second_result = node.parse_document(case_id=patient_case.case_id, document=document)

    assert first_result.extraction_reference == second_result.extraction_reference
    assert second_result.was_duplicate is True
    assert len(case_service.get_case_core_records(patient_case.case_id).extractions) == 1
    assert (
        case_service.get_case_core_records(patient_case.case_id).patient_case.status
        == CaseStatus.PROCESSING_DOCUMENTS
    )


def test_parse_document_is_idempotent_for_repeated_partial_extraction_execution() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_parse_002_partial")
    patient_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_parse_002_partial",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_parse_002_partial",
    )
    _build_processed_case(
        case_service=case_service,
        case_id=patient_case.case_id,
        document=document,
        now=now,
    )

    parser_calls: list[tuple[bytes, DocumentUploadMetadata]] = []

    def parser(document_bytes: bytes, payload: DocumentUploadMetadata) -> tuple[str, float]:
        parser_calls.append((document_bytes, payload))
        return ("enough text for partial state", 0.42)

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw document bytes",
        document_parser=parser,
        clock=lambda: now,
    )
    node = ParseDocumentNode(
        case_service=case_service,
        ocr_client=client,
        settings=Settings(
            document_extraction_min_confidence=0.75,
            document_extraction_min_text_length=16,
        ),
    )

    first_result = node.parse_document(case_id=patient_case.case_id, document=document)
    second_result = node.parse_document(case_id=patient_case.case_id, document=document)

    assert first_result.case_status == CaseStatus.PARTIAL_EXTRACTION
    assert second_result.case_status == CaseStatus.PARTIAL_EXTRACTION
    assert second_result.was_duplicate is True
    assert len(parser_calls) == 1
    assert len(case_service.get_case_extraction_records(patient_case.case_id)) == 1
    assert (
        case_service.get_case_core_records(patient_case.case_id).patient_case.status
        == CaseStatus.PARTIAL_EXTRACTION
    )


def test_parse_document_refuses_duplicate_result_after_case_is_closed() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_parse_002b")
    patient_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_parse_002b",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_parse_002b",
    )
    _build_processed_case(
        case_service=case_service,
        case_id=patient_case.case_id,
        document=document,
        now=now,
    )

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw document bytes",
        document_parser=lambda _bytes, _document: ("raw extracted text", 0.79),
        clock=lambda: now,
    )
    node = ParseDocumentNode(case_service=case_service, ocr_client=client)

    first_result = node.parse_document(case_id=patient_case.case_id, document=document)
    case_service.transition_case(patient_case.case_id, CaseStatus.READY_FOR_SUMMARY)
    second_result = node.parse_document(case_id=patient_case.case_id, document=document)

    assert first_result.extraction_reference is not None
    assert first_result.was_duplicate is False
    assert second_result.extraction is None
    assert second_result.failure_code == "case_not_processable"
    assert second_result.case_status == CaseStatus.READY_FOR_SUMMARY
    assert len(case_service.get_case_extraction_records(patient_case.case_id)) == 1


def test_parse_document_does_not_reuse_results_across_cases() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_ids = iter(["case_parse_cross_001", "case_parse_cross_002"])
    case_service = CaseService(clock=lambda: now, id_generator=lambda: next(case_ids))
    first_case = case_service.create_case()
    second_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_parse_cross",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_parse_cross",
    )
    _build_processed_case(
        case_service=case_service,
        case_id=first_case.case_id,
        document=document,
        now=now,
    )
    _build_processed_case(
        case_service=case_service,
        case_id=second_case.case_id,
        document=document,
        now=now,
    )

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw document bytes",
        document_parser=lambda _bytes, _document: ("cross-case text", 0.71),
        clock=lambda: now,
    )
    node = ParseDocumentNode(case_service=case_service, ocr_client=client)

    first_result = node.parse_document(case_id=first_case.case_id, document=document)
    second_result = node.parse_document(case_id=second_case.case_id, document=document)

    assert first_result.case_id == first_case.case_id
    assert second_result.case_id == second_case.case_id
    assert first_result.extraction_reference != second_result.extraction_reference
    assert first_result.extraction is not None
    assert second_result.extraction is not None
    assert first_result.extraction.extracted_text == "cross-case text"
    assert second_result.extraction.extracted_text == "cross-case text"
    assert len(case_service.get_case_extraction_records(first_case.case_id)) == 1
    assert len(case_service.get_case_extraction_records(second_case.case_id)) == 1


def test_parse_document_marks_failure_without_exposing_raw_error_details() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_parse_003")
    patient_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_parse_003",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_parse_003",
    )
    _build_processed_case(
        case_service=case_service,
        case_id=patient_case.case_id,
        document=document,
        now=now,
    )

    def failing_parser(document_bytes: bytes, payload: DocumentUploadMetadata) -> tuple[str, float]:
        raise RuntimeError("provider timeout: stack trace details")

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw document bytes",
        document_parser=failing_parser,
        clock=lambda: now,
    )
    node = ParseDocumentNode(case_service=case_service, ocr_client=client)

    result = node.parse_document(case_id=patient_case.case_id, document=document)

    assert result.case_status == CaseStatus.EXTRACTION_FAILED
    assert result.is_recoverable_failure is True
    assert result.failure_code == "ocr_processing_failed"
    assert "timeout" not in result.failure_message.lower()
    assert case_service.get_case_core_records(patient_case.case_id).extractions == ()
    assert (
        case_service.get_case_core_records(patient_case.case_id).patient_case.status
        == CaseStatus.EXTRACTION_FAILED
    )
