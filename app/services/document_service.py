from datetime import datetime

from app.core.settings import Settings, get_settings
from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.document import (
    DocumentUploadMetadata,
    DocumentUploadRejectionReasonCode,
    DocumentUploadValidationContext,
    DocumentUploadValidationResult,
)


class DocumentService:
    def __init__(self, *, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._supported_mime_types = tuple(
            mime_type.lower() for mime_type in self._settings.document_upload_supported_mime_types
        )
        self._max_file_size_bytes = self._settings.document_upload_max_file_size_bytes

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
        record_id = DocumentService.build_document_identity_key(document_metadata)
        return CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.DOCUMENT,
            record_id=f"telegram_document:{record_id}",
            created_at=created_at,
        )

    @staticmethod
    def build_document_identity_key(document_metadata: DocumentUploadMetadata) -> str:
        return document_metadata.file_unique_id or document_metadata.file_id

    def validate_document_upload(
        self,
        document: DocumentUploadMetadata,
    ) -> DocumentUploadValidationResult:
        validation_context = DocumentUploadValidationContext(
            supported_mime_types=self._supported_mime_types,
            configured_max_file_size_bytes=self._max_file_size_bytes,
            file_name=document.file_name,
            mime_type=document.mime_type,
            file_size=document.file_size,
        )
        if document.mime_type is None or document.file_size is None or document.file_size <= 0:
            return DocumentUploadValidationResult(
                is_accepted=False,
                rejection_reason_code=DocumentUploadRejectionReasonCode.INVALID_DOCUMENT,
                validation_context=validation_context,
            )

        normalized_mime_type = document.mime_type.lower()
        if normalized_mime_type not in self._supported_mime_types:
            return DocumentUploadValidationResult(
                is_accepted=False,
                rejection_reason_code=DocumentUploadRejectionReasonCode.UNSUPPORTED_FILE_TYPE,
                validation_context=validation_context,
            )

        if document.file_size > self._max_file_size_bytes:
            return DocumentUploadValidationResult(
                is_accepted=False,
                rejection_reason_code=DocumentUploadRejectionReasonCode.FILE_TOO_LARGE,
                validation_context=validation_context,
            )

        return DocumentUploadValidationResult(is_accepted=True)
