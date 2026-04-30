from datetime import datetime

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.document import DocumentUploadMetadata


class DocumentService:
    @staticmethod
    def normalize_document_metadata(
        *,
        file_id: str,
        file_name: str | None = None,
        mime_type: str | None = None,
        file_size: int | None = None,
        file_unique_id: str | None = None,
    ) -> DocumentUploadMetadata:
        return DocumentUploadMetadata(
            file_id=file_id,
            file_name=file_name,
            mime_type=mime_type,
            file_size=file_size,
            file_unique_id=file_unique_id,
        )

    @staticmethod
    def build_document_reference(
        *,
        case_id: str,
        document_metadata: DocumentUploadMetadata,
        created_at: datetime,
    ) -> CaseRecordReference:
        record_id = document_metadata.file_unique_id or document_metadata.file_id
        return CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.DOCUMENT,
            record_id=f"telegram_document:{record_id}",
            created_at=created_at,
        )
