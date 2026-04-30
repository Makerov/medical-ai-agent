from datetime import UTC, datetime

from app.integrations.ocr_client import OCRClient
from app.schemas.case import CaseStatus
from app.schemas.document import DocumentUploadMetadata
from app.services.case_service import CaseService
from app.services.document_service import DocumentService
from app.workers.process_case_worker import ProcessCaseWorker
from app.workflow.nodes.parse_document import ParseDocumentNode


def _build_case_with_document(
    *,
    case_service: CaseService,
    case_id: str,
    document: DocumentUploadMetadata,
    now: datetime,
) -> None:
    case_service.transition_case(case_id, CaseStatus.AWAITING_CONSENT)
    case_service.transition_case(case_id, CaseStatus.COLLECTING_INTAKE)
    case_service.attach_case_record_reference(
        DocumentService.build_document_reference(
            case_id=case_id,
            document_metadata=document,
            created_at=now,
        )
    )
    case_service.transition_case(case_id, CaseStatus.DOCUMENTS_UPLOADED)


def test_process_case_worker_processes_case_without_touching_tg_boundary() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_worker_001")
    patient_case = case_service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_worker_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_worker_001",
    )
    _build_case_with_document(
        case_service=case_service,
        case_id=patient_case.case_id,
        document=document,
        now=now,
    )

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw document bytes",
        document_parser=lambda _bytes, _document: ("worker text", 0.83),
        clock=lambda: now,
    )
    worker = ProcessCaseWorker(
        case_service=case_service,
        parse_document_node=ParseDocumentNode(case_service=case_service, ocr_client=client),
    )

    result = worker.process_case(case_id=patient_case.case_id, document=document)

    assert result.case_id == patient_case.case_id
    assert result.case_status == CaseStatus.PROCESSING_DOCUMENTS
    assert result.extraction is not None
    assert case_service.get_case_core_records(patient_case.case_id).extractions == (
        result.extraction_reference,
    )
