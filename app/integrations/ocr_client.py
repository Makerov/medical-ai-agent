from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from pydantic import ValidationError

from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import OCRTextExtractionResult


class OCRClientError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class DocumentBytesFetcher(Protocol):
    def __call__(self, document: DocumentUploadMetadata) -> bytes: ...


class DocumentParser(Protocol):
    def __call__(
        self,
        document_bytes: bytes,
        document: DocumentUploadMetadata,
    ) -> tuple[str, float]: ...


Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


def _unconfigured_fetcher(document: DocumentUploadMetadata) -> bytes:
    raise OCRClientError(
        code="document_fetch_unavailable",
        message="OCR document fetcher is not configured",
    )


def _unconfigured_parser(
    document_bytes: bytes,
    document: DocumentUploadMetadata,
) -> tuple[str, float]:
    raise OCRClientError(
        code="document_parse_unavailable",
        message="OCR document parser is not configured",
    )


class OCRClient:
    def __init__(
        self,
        *,
        document_bytes_fetcher: DocumentBytesFetcher | None = None,
        document_parser: DocumentParser | None = None,
        clock: Clock = utc_now,
        provider_name: str = "provider_agnostic",
    ) -> None:
        self._document_bytes_fetcher = document_bytes_fetcher or _unconfigured_fetcher
        self._document_parser = document_parser or _unconfigured_parser
        self._clock = clock
        self._provider_name = provider_name.strip() or "provider_agnostic"

    def extract_text(self, document: DocumentUploadMetadata) -> OCRTextExtractionResult:
        document_bytes = self._fetch_document_bytes(document)
        extracted_text, confidence = self._parse_document(document_bytes, document)
        if not isinstance(extracted_text, str):
            raise OCRClientError(
                code="invalid_extracted_text",
                message="OCR parser returned invalid text payload",
            )
        if not isinstance(confidence, (int, float)):
            raise OCRClientError(
                code="invalid_confidence_payload",
                message="OCR parser returned invalid confidence payload",
            )
        normalized_text = extracted_text.strip()
        if not normalized_text:
            raise OCRClientError(
                code="empty_extraction",
                message="OCR parser returned empty text",
            )
        if confidence < 0.0 or confidence > 1.0:
            raise OCRClientError(
                code="invalid_confidence",
                message="OCR parser returned invalid confidence",
            )
        try:
            return OCRTextExtractionResult(
                source_document=document,
                extracted_text=normalized_text,
                confidence=confidence,
                extracted_at=self._clock(),
                provider_name=self._provider_name,
            )
        except ValidationError as exc:
            raise OCRClientError(
                code="invalid_extraction_result",
                message="OCR parser returned invalid extraction result",
            ) from exc

    def _fetch_document_bytes(self, document: DocumentUploadMetadata) -> bytes:
        try:
            return self._document_bytes_fetcher(document)
        except OCRClientError:
            raise
        except Exception as exc:  # noqa: BLE001 - recoverable adapter boundary
            raise OCRClientError(
                code="document_fetch_failed",
                message="OCR document fetch failed",
            ) from exc

    def _parse_document(
        self,
        document_bytes: bytes,
        document: DocumentUploadMetadata,
    ) -> tuple[str, float]:
        try:
            return self._document_parser(document_bytes, document)
        except OCRClientError:
            raise
        except Exception as exc:  # noqa: BLE001 - recoverable adapter boundary
            raise OCRClientError(
                code="document_parse_failed",
                message="OCR document parse failed",
            ) from exc
