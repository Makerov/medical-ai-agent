from datetime import UTC, datetime

import pytest

from app.integrations.ocr_client import OCRClient, OCRClientError, PaddleOCRDocumentParser
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


class _FakePaddleEngine:
    def __init__(self, result) -> None:
        self.result = result
        self.paths: list[str] = []

    def ocr(self, path: str):
        self.paths.append(path)
        return self.result


def test_paddleocr_parser_joins_text_and_averages_confidence() -> None:
    engine = _FakePaddleEngine(
        [
            [
                [[[0, 0], [1, 0], [1, 1], [0, 1]], (" first line ", 0.8)],
                [[[0, 2], [1, 2], [1, 3], [0, 3]], ("second line", 0.6)],
            ]
        ]
    )
    parser = PaddleOCRDocumentParser(
        model_name="PP-OCRv5_server",
        lang="ru",
        engine_factory=lambda **_: engine,
    )
    document = DocumentUploadMetadata(
        file_id="file_ocr_paddle_001",
        file_name="scan.png",
        mime_type="image/png",
        file_size=2048,
    )

    text, confidence = parser(b"raw image bytes", document)

    assert text == "first line\nsecond line"
    assert confidence == pytest.approx(0.7)
    assert engine.paths
    assert engine.paths[0].endswith(".png")


def test_paddleocr_parser_reads_newer_recognition_result_shape() -> None:
    engine = _FakePaddleEngine(
        {
            "rec_texts": ["alpha", " beta "],
            "rec_scores": [0.9, 0.7],
        }
    )
    parser = PaddleOCRDocumentParser(
        model_name="PP-OCRv5_server",
        lang="ru",
        engine_factory=lambda **_: engine,
    )
    document = DocumentUploadMetadata(
        file_id="file_ocr_paddle_002",
        mime_type="application/pdf",
        file_size=2048,
    )

    text, confidence = parser(b"raw pdf bytes", document)

    assert text == "alpha\nbeta"
    assert confidence == pytest.approx(0.8)


def test_paddleocr_parser_raises_for_empty_result() -> None:
    engine = _FakePaddleEngine([])
    parser = PaddleOCRDocumentParser(
        model_name="PP-OCRv5_server",
        lang="ru",
        engine_factory=lambda **_: engine,
    )
    document = DocumentUploadMetadata(
        file_id="file_ocr_paddle_003",
        mime_type="image/jpeg",
        file_size=2048,
    )

    with pytest.raises(OCRClientError) as exc_info:
        parser(b"raw image bytes", document)

    assert exc_info.value.code == "empty_extraction"
