from app.core.settings import Settings
from app.schemas.document import (
    DocumentUploadMetadata,
    DocumentUploadRejectionReasonCode,
)
from app.services.document_service import DocumentService


def test_validate_document_upload_accepts_supported_pdf() -> None:
    service = DocumentService(
        settings=Settings(
            document_upload_supported_mime_types=(
                "application/pdf",
                "image/jpeg",
                "image/png",
            ),
            document_upload_max_file_size_bytes=20_000_000,
        )
    )
    document = DocumentUploadMetadata(
        file_id="file_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=1024,
    )

    result = service.validate_document_upload(document)

    assert result.is_accepted is True
    assert result.rejection_reason_code is None
    assert result.validation_context is None


def test_validate_document_upload_rejects_unsupported_file_type() -> None:
    service = DocumentService(
        settings=Settings(
            document_upload_supported_mime_types=(
                "application/pdf",
                "image/jpeg",
                "image/png",
            ),
            document_upload_max_file_size_bytes=20_000_000,
        )
    )
    document = DocumentUploadMetadata(
        file_id="file_002",
        file_name="scan.gif",
        mime_type="image/gif",
        file_size=1024,
    )

    result = service.validate_document_upload(document)

    assert result.is_accepted is False
    assert result.rejection_reason_code == (
        DocumentUploadRejectionReasonCode.UNSUPPORTED_FILE_TYPE
    )
    assert result.validation_context is not None
    assert result.validation_context.supported_mime_types == (
        "application/pdf",
        "image/jpeg",
        "image/png",
    )


def test_validate_document_upload_rejects_oversized_file() -> None:
    service = DocumentService(
        settings=Settings(
            document_upload_supported_mime_types=(
                "application/pdf",
                "image/jpeg",
                "image/png",
            ),
            document_upload_max_file_size_bytes=20_000_000,
        )
    )
    document = DocumentUploadMetadata(
        file_id="file_003",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=20_000_001,
    )

    result = service.validate_document_upload(document)

    assert result.is_accepted is False
    assert result.rejection_reason_code == DocumentUploadRejectionReasonCode.FILE_TOO_LARGE
    assert result.validation_context is not None
    assert result.validation_context.configured_max_file_size_bytes == 20_000_000


def test_validate_document_upload_rejects_invalid_metadata() -> None:
    service = DocumentService(
        settings=Settings(
            document_upload_supported_mime_types=(
                "application/pdf",
                "image/jpeg",
                "image/png",
            ),
            document_upload_max_file_size_bytes=20_000_000,
        )
    )
    document = DocumentUploadMetadata(
        file_id="file_004",
        file_name="scan.pdf",
        mime_type=None,
        file_size=1024,
    )

    result = service.validate_document_upload(document)

    assert result.is_accepted is False
    assert result.rejection_reason_code == DocumentUploadRejectionReasonCode.INVALID_DOCUMENT
    assert result.validation_context is not None
    assert result.validation_context.mime_type is None
