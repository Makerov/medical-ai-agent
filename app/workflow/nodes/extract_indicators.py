from app.schemas.case import CaseStatus
from app.schemas.extraction import CaseExtractionRecord, DocumentProcessingResult
from app.schemas.indicator import CaseIndicatorExtractionRecord
from app.services.case_service import CaseService
from app.services.extraction_service import ExtractionService


class ExtractIndicatorsNode:
    def __init__(
        self,
        *,
        case_service: CaseService,
        extraction_service: ExtractionService | None = None,
    ) -> None:
        self._case_service = case_service
        self._extraction_service = extraction_service or ExtractionService(
            case_service=case_service,
        )

    def extract_indicators(
        self,
        *,
        processing_result: DocumentProcessingResult,
    ) -> CaseIndicatorExtractionRecord | None:
        if processing_result.extraction is None:
            return None
        if processing_result.source_document_reference is None:
            return None
        if processing_result.extraction_reference is None:
            return None
        if processing_result.case_status != CaseStatus.PROCESSING_DOCUMENTS:
            return None

        extraction_record = CaseExtractionRecord(
            case_id=processing_result.case_id,
            source_document=processing_result.source_document,
            source_document_reference=processing_result.source_document_reference,
            extraction_reference=processing_result.extraction_reference,
            extracted_text=processing_result.extraction.extracted_text,
            confidence=processing_result.extraction.confidence,
            extracted_at=processing_result.extraction.extracted_at,
            provider_name=processing_result.extraction.provider_name,
        )
        return self._extraction_service.extract_indicators(
            case_id=processing_result.case_id,
            extraction_record=extraction_record,
        )
