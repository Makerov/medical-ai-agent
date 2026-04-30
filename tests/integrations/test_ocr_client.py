from datetime import UTC, datetime

import pytest

from app.integrations.ocr_client import OCRClient, OCRClientError
from app.schemas.document import DocumentUploadMetadata


def test_extract_text_returns_normalized_payload_and_preserves_source_metadata() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    document = DocumentUploadMetadata(
        file_id="file_ocr_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=2048,
        file_unique_id="unique_ocr_001",
    )

    def fetcher(payload: DocumentUploadMetadata) -> bytes:
        assert payload == document
        return b"raw bytes"

    def parser(document_bytes: bytes, payload: DocumentUploadMetadata) -> tuple[str, float]:
        assert document_bytes == b"raw bytes"
        assert payload == document
        return ("  extracted text  ", 0.91)

    client = OCRClient(
        document_bytes_fetcher=fetcher,
        document_parser=parser,
        clock=lambda: now,
        provider_name="local-stub",
    )

    result = client.extract_text(document)

    assert result.source_document == document
    assert result.extracted_text == "extracted text"
    assert result.confidence == 0.91
    assert result.extracted_at == now
    assert result.provider_name == "local-stub"


def test_extract_text_raises_safe_error_when_not_configured() -> None:
    client = OCRClient()
    document = DocumentUploadMetadata(
        file_id="file_ocr_002",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=2048,
        file_unique_id="unique_ocr_002",
    )

    with pytest.raises(OCRClientError) as exc_info:
        client.extract_text(document)

    assert exc_info.value.code == "document_fetch_unavailable"


def test_extract_text_raises_safe_error_for_invalid_parser_payload() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    document = DocumentUploadMetadata(
        file_id="file_ocr_003",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=2048,
        file_unique_id="unique_ocr_003",
    )

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw bytes",
        document_parser=lambda _bytes, _document: (123, "bad-confidence"),
        clock=lambda: now,
    )

    with pytest.raises(OCRClientError) as exc_info:
        client.extract_text(document)

    assert exc_info.value.code == "invalid_extracted_text"


def test_extract_text_raises_safe_error_for_naive_clock() -> None:
    document = DocumentUploadMetadata(
        file_id="file_ocr_004",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=2048,
        file_unique_id="unique_ocr_004",
    )

    client = OCRClient(
        document_bytes_fetcher=lambda _: b"raw bytes",
        document_parser=lambda _bytes, _document: ("valid text", 0.9),
        clock=lambda: datetime(2026, 4, 28, 6, 0),
    )

    with pytest.raises(OCRClientError) as exc_info:
        client.extract_text(document)

    assert exc_info.value.code == "invalid_extraction_result"
