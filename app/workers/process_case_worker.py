from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import DocumentProcessingResult
from app.services.case_service import CaseService
from app.workflow.nodes.parse_document import ParseDocumentNode


class ProcessCaseWorker:
    def __init__(
        self,
        *,
        case_service: CaseService,
        parse_document_node: ParseDocumentNode | None = None,
    ) -> None:
        self._case_service = case_service
        self._parse_document_node = parse_document_node or ParseDocumentNode(
            case_service=case_service,
        )

    def process_case(
        self,
        *,
        case_id: str,
        document: DocumentUploadMetadata,
    ) -> DocumentProcessingResult:
        return self._parse_document_node.parse_document(case_id=case_id, document=document)

