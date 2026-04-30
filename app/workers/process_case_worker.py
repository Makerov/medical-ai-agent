from app.schemas.case import CaseStatus
from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import DocumentProcessingResult
from app.services.case_service import CaseService
from app.workflow.nodes.extract_indicators import ExtractIndicatorsNode
from app.workflow.nodes.parse_document import ParseDocumentNode


class ProcessCaseWorker:
    def __init__(
        self,
        *,
        case_service: CaseService,
        parse_document_node: ParseDocumentNode | None = None,
        extract_indicators_node: ExtractIndicatorsNode | None = None,
    ) -> None:
        self._case_service = case_service
        self._parse_document_node = parse_document_node or ParseDocumentNode(
            case_service=case_service,
        )
        self._extract_indicators_node = extract_indicators_node or ExtractIndicatorsNode(
            case_service=case_service,
        )

    def process_case(
        self,
        *,
        case_id: str,
        document: DocumentUploadMetadata,
    ) -> DocumentProcessingResult:
        result = self._parse_document_node.parse_document(case_id=case_id, document=document)
        if result.case_status == CaseStatus.PROCESSING_DOCUMENTS and result.extraction is not None:
            self._extract_indicators_node.extract_indicators(processing_result=result)
        return result
