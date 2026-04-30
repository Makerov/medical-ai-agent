from app.core.settings import Settings, get_settings
from app.integrations.ocr_client import OCRClient, OCRClientError
from app.schemas.case import (
    CaseRecordKind,
    CaseRecordReference,
    CaseStatus,
    CaseTransitionError,
)
from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import (
    CaseExtractionRecord,
    DocumentProcessingResult,
    OCRTextExtractionResult,
)
from app.services.case_service import CaseService
from app.services.document_service import DocumentService


class ParseDocumentNode:
    _SUCCESS_STATES = frozenset(
        {
            CaseStatus.DOCUMENTS_UPLOADED,
            CaseStatus.PROCESSING_DOCUMENTS,
        }
    )
    _TERMINAL_OR_BLOCKED_STATES = frozenset(
        {
            CaseStatus.DELETION_REQUESTED,
            CaseStatus.DELETED,
            CaseStatus.DOCTOR_REVIEWED,
            CaseStatus.READY_FOR_DOCTOR,
            CaseStatus.READY_FOR_SUMMARY,
            CaseStatus.SUMMARY_FAILED,
            CaseStatus.SAFETY_FAILED,
        }
    )

    def __init__(
        self,
        *,
        case_service: CaseService,
        ocr_client: OCRClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._case_service = case_service
        self._ocr_client = ocr_client or OCRClient()
        self._settings = settings or get_settings()

    def parse_document(
        self,
        *,
        case_id: str,
        document: DocumentUploadMetadata,
    ) -> DocumentProcessingResult:
        try:
            records = self._case_service.get_case_core_records(case_id)
        except CaseTransitionError:
            return self._build_failure_result(
                case_id=case_id,
                case_status=CaseStatus.DELETED,
                document=document,
                source_document_reference=CaseRecordReference(
                    case_id=case_id,
                    record_kind=CaseRecordKind.DOCUMENT,
                    record_id=(
                        "telegram_document:"
                        f"{DocumentService.build_document_identity_key(document)}"
                    ),
                    created_at=self._case_service.current_time(),
                ),
                failure_code="case_not_found",
                failure_message="Case is not available for document processing.",
                is_recoverable_failure=False,
            )
        patient_case = records.patient_case
        try:
            source_document_reference = self._resolve_source_document_reference(
                case_id=case_id,
                document_references=records.documents,
                document=document,
            )
        except CaseTransitionError:
            return self._build_failure_result(
                case_id=case_id,
                case_status=patient_case.status,
                document=document,
                source_document_reference=CaseRecordReference(
                    case_id=case_id,
                    record_kind=CaseRecordKind.DOCUMENT,
                    record_id=(
                        "telegram_document:"
                        f"{DocumentService.build_document_identity_key(document)}"
                    ),
                    created_at=self._case_service.current_time(),
                ),
                failure_code="source_document_missing",
                failure_message="Document metadata is not linked to this case.",
                is_recoverable_failure=True,
            )
        extraction_record_id = self._build_extraction_record_id(source_document_reference)

        if patient_case.status in self._TERMINAL_OR_BLOCKED_STATES:
            return self._build_failure_result(
                case_id=case_id,
                case_status=patient_case.status,
                document=document,
                source_document_reference=source_document_reference,
                failure_code="case_not_processable",
                failure_message="Case cannot be processed in its current state.",
                is_recoverable_failure=False,
            )

        existing_extraction = self._find_existing_extraction(case_id, extraction_record_id)
        if existing_extraction is not None:
            return self._build_result_from_extraction(
                existing_extraction,
                was_duplicate=True,
            )

        if patient_case.status not in self._SUCCESS_STATES:
            return self._build_failure_result(
                case_id=case_id,
                case_status=patient_case.status,
                document=document,
                source_document_reference=source_document_reference,
                failure_code="processing_state_unavailable",
                failure_message="Document processing is not available for the current case state.",
                is_recoverable_failure=True,
            )

        if patient_case.status == CaseStatus.DOCUMENTS_UPLOADED:
            try:
                self._case_service.transition_case(case_id, CaseStatus.PROCESSING_DOCUMENTS)
            except CaseTransitionError:
                return self._build_failure_result(
                    case_id=case_id,
                    case_status=self._case_service.get_case_core_records(case_id).patient_case.status,
                    document=document,
                    source_document_reference=source_document_reference,
                    failure_code="case_transition_failed",
                    failure_message=(
                        "Document processing is not available for the current case state."
                    ),
                    is_recoverable_failure=True,
                )

        try:
            extraction = self._ocr_client.extract_text(document)
            extraction_reference = CaseRecordReference(
                case_id=case_id,
                record_kind=CaseRecordKind.EXTRACTION,
                record_id=extraction_record_id,
                created_at=extraction.extracted_at,
            )
            extraction_record = CaseExtractionRecord(
                case_id=case_id,
                source_document=document,
                source_document_reference=source_document_reference,
                extraction_reference=extraction_reference,
                extracted_text=extraction.extracted_text,
                confidence=extraction.confidence,
                extracted_at=extraction.extracted_at,
                provider_name=extraction.provider_name,
            )
            quality_case_status: CaseStatus | None = None
            if self._is_low_quality_extraction(extraction_record):
                quality_case_status = self._mark_partial_extraction(case_id=case_id)
                if quality_case_status != CaseStatus.PARTIAL_EXTRACTION:
                    return self._build_failure_result(
                        case_id=case_id,
                        case_status=quality_case_status,
                        document=document,
                        source_document_reference=source_document_reference,
                        failure_code="case_transition_failed",
                        failure_message="Не удалось обработать документ.",
                        is_recoverable_failure=True,
                    )
            attached_extraction_record = self._case_service.attach_case_extraction_record(
                extraction_record,
            )
            attached_extraction_reference = self._case_service.attach_case_record_reference(
                extraction_reference,
            )
            if quality_case_status is not None:
                return self._build_result_from_extraction(
                    attached_extraction_record,
                    extraction_reference=attached_extraction_reference,
                    case_status=quality_case_status,
                )
        except OCRClientError:
            failed_case = self._mark_processing_failed(case_id=case_id)
            return self._build_failure_result(
                case_id=case_id,
                case_status=failed_case,
                document=document,
                source_document_reference=source_document_reference,
                failure_code="ocr_processing_failed",
                failure_message="Не удалось обработать документ.",
                is_recoverable_failure=True,
            )
        except CaseTransitionError:
            failed_case = self._mark_processing_failed(case_id=case_id)
            return self._build_failure_result(
                case_id=case_id,
                case_status=failed_case,
                document=document,
                source_document_reference=source_document_reference,
                failure_code="case_transition_failed",
                failure_message="Не удалось обработать документ.",
                is_recoverable_failure=True,
            )

        return self._build_result_from_extraction(
            attached_extraction_record,
            extraction_reference=attached_extraction_reference,
        )

    def _resolve_source_document_reference(
        self,
        *,
        case_id: str,
        document_references: tuple[CaseRecordReference, ...],
        document: DocumentUploadMetadata,
    ) -> CaseRecordReference:
        expected_record_id = (
            f"telegram_document:{DocumentService.build_document_identity_key(document)}"
        )
        for reference in reversed(document_references):
            if reference.record_id == expected_record_id:
                return reference
        raise CaseTransitionError(
            code="source_document_missing",
            case_id=case_id,
            from_status=None,
            to_status=expected_record_id,
        )

    @staticmethod
    def _build_extraction_record_id(source_document_reference: CaseRecordReference) -> str:
        return f"extraction:{source_document_reference.record_id}"

    def _is_low_quality_extraction(self, extraction_record: CaseExtractionRecord) -> bool:
        if extraction_record.confidence < self._settings.document_extraction_min_confidence:
            return True
        return (
            len(extraction_record.extracted_text)
            < self._settings.document_extraction_min_text_length
        )

    def _find_existing_extraction(
        self,
        case_id: str,
        extraction_record_id: str,
    ) -> CaseExtractionRecord | None:
        for record in self._case_service.get_case_extraction_records(case_id):
            if record.extraction_reference.record_id == extraction_record_id:
                return record
        return None

    def _build_result_from_extraction(
        self,
        extraction_record: CaseExtractionRecord,
        *,
        was_duplicate: bool = False,
        extraction_reference: CaseRecordReference | None = None,
        case_status: CaseStatus | None = None,
    ) -> DocumentProcessingResult:
        normalized_extraction_reference = (
            extraction_reference or extraction_record.extraction_reference
        )
        return DocumentProcessingResult(
            case_id=extraction_record.case_id,
            case_status=(
                case_status
                or self._case_service.get_case_core_records(extraction_record.case_id)
                .patient_case.status
            ),
            source_document=extraction_record.source_document,
            source_document_reference=extraction_record.source_document_reference,
            extraction_reference=normalized_extraction_reference,
            extraction=OCRTextExtractionResult(
                source_document=extraction_record.source_document,
                extracted_text=extraction_record.extracted_text,
                confidence=extraction_record.confidence,
                extracted_at=extraction_record.extracted_at,
                provider_name=extraction_record.provider_name,
            ),
            was_duplicate=was_duplicate,
        )

    def _mark_processing_failed(self, *, case_id: str) -> CaseStatus:
        current_status = self._case_service.get_case_core_records(case_id).patient_case.status
        try:
            if current_status == CaseStatus.PROCESSING_DOCUMENTS:
                failed_case = self._case_service.transition_case(
                    case_id,
                    CaseStatus.EXTRACTION_FAILED,
                )
                return failed_case.status
            if current_status == CaseStatus.DOCUMENTS_UPLOADED:
                self._case_service.transition_case(case_id, CaseStatus.PROCESSING_DOCUMENTS)
                failed_case = self._case_service.transition_case(
                    case_id,
                    CaseStatus.EXTRACTION_FAILED,
                )
                return failed_case.status
        except CaseTransitionError:
            return self._case_service.get_case_core_records(case_id).patient_case.status
        return current_status

    def _mark_partial_extraction(self, *, case_id: str) -> CaseStatus:
        current_status = self._case_service.get_case_core_records(case_id).patient_case.status
        try:
            if current_status == CaseStatus.PROCESSING_DOCUMENTS:
                partial_case = self._case_service.transition_case(
                    case_id,
                    CaseStatus.PARTIAL_EXTRACTION,
                )
                return partial_case.status
            if current_status == CaseStatus.DOCUMENTS_UPLOADED:
                self._case_service.transition_case(case_id, CaseStatus.PROCESSING_DOCUMENTS)
                partial_case = self._case_service.transition_case(
                    case_id,
                    CaseStatus.PARTIAL_EXTRACTION,
                )
                return partial_case.status
        except CaseTransitionError:
            return self._case_service.get_case_core_records(case_id).patient_case.status
        return current_status

    @staticmethod
    def _build_failure_result(
        *,
        case_id: str,
        case_status: CaseStatus,
        document: DocumentUploadMetadata,
        source_document_reference: CaseRecordReference,
        failure_code: str,
        failure_message: str,
        is_recoverable_failure: bool,
    ) -> DocumentProcessingResult:
        return DocumentProcessingResult(
            case_id=case_id,
            case_status=case_status,
            source_document=document,
            source_document_reference=source_document_reference,
            extraction_reference=None,
            extraction=None,
            was_duplicate=False,
            is_recoverable_failure=is_recoverable_failure,
            failure_code=failure_code,
            failure_message=failure_message,
        )
