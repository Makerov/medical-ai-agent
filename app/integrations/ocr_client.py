from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Protocol

from pydantic import ValidationError

from app.core.settings import Settings
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
PaddleOCRFactory = Callable[..., Any]


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


class PaddleOCRDocumentParser:
    def __init__(
        self,
        *,
        model_name: str,
        lang: str,
        engine_factory: PaddleOCRFactory | None = None,
    ) -> None:
        self._model_name = model_name
        self._lang = lang
        self._engine_factory = engine_factory
        self._engine: Any | None = None

    def __call__(
        self,
        document_bytes: bytes,
        document: DocumentUploadMetadata,
    ) -> tuple[str, float]:
        if not document_bytes:
            raise OCRClientError("empty_document_bytes", "Document bytes are empty")

        suffix = self._suffix_for_document(document)
        with NamedTemporaryFile(suffix=suffix) as temp_file:
            temp_file.write(document_bytes)
            temp_file.flush()
            raw_result = self._run_ocr(Path(temp_file.name))

        pairs = self._extract_text_score_pairs(raw_result)
        non_empty_pairs = [
            (text.strip(), float(score))
            for text, score in pairs
            if text.strip() and isinstance(score, (int, float))
        ]
        if not non_empty_pairs:
            raise OCRClientError("empty_extraction", "PaddleOCR returned no text")
        scores = [score for _, score in non_empty_pairs]
        if any(score < 0.0 or score > 1.0 for score in scores):
            raise OCRClientError("invalid_confidence", "PaddleOCR returned invalid confidence")
        extracted_text = "\n".join(text for text, _ in non_empty_pairs)
        aggregate_confidence = sum(scores) / len(scores)
        return extracted_text, aggregate_confidence

    def _run_ocr(self, document_path: Path) -> Any:
        engine = self._get_engine()
        if hasattr(engine, "ocr"):
            return engine.ocr(str(document_path))
        if hasattr(engine, "predict"):
            return engine.predict(str(document_path))
        raise OCRClientError("ocr_engine_invalid", "PaddleOCR engine is invalid")

    def _get_engine(self) -> Any:
        if self._engine is not None:
            return self._engine
        factory = self._engine_factory or self._load_paddleocr_factory()
        try:
            self._engine = factory(lang=self._lang, ocr_version=self._model_name)
        except TypeError as exc:
            raise OCRClientError(
                "ocr_provider_configuration_invalid",
                "PaddleOCR engine does not accept the configured model selector",
            ) from exc
        return self._engine

    @staticmethod
    def _load_paddleocr_factory() -> PaddleOCRFactory:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:  # pragma: no cover - depends on optional runtime package
            raise OCRClientError(
                "ocr_provider_unavailable",
                "PaddleOCR package is not installed",
            ) from exc
        return PaddleOCR

    @classmethod
    def _extract_text_score_pairs(cls, payload: Any) -> list[tuple[str, float]]:
        pairs: list[tuple[str, float]] = []
        if isinstance(payload, dict):
            texts = payload.get("rec_texts")
            scores = payload.get("rec_scores")
            if isinstance(texts, list) and isinstance(scores, list):
                pairs.extend(
                    (str(text), float(score))
                    for text, score in zip(texts, scores, strict=False)
                    if isinstance(score, (int, float))
                )
            for value in payload.values():
                pairs.extend(cls._extract_text_score_pairs(value))
            return pairs

        json_payload = getattr(payload, "json", None)
        if isinstance(json_payload, dict):
            return cls._extract_text_score_pairs(json_payload)
        to_dict = getattr(payload, "to_dict", None)
        if callable(to_dict):
            try:
                return cls._extract_text_score_pairs(to_dict())
            except TypeError:
                return pairs

        if isinstance(payload, tuple) and len(payload) == 2:
            text_candidate, score_candidate = payload
            if isinstance(text_candidate, str) and isinstance(score_candidate, (int, float)):
                return [(text_candidate, float(score_candidate))]

        if isinstance(payload, list):
            if (
                len(payload) == 2
                and isinstance(payload[0], str)
                and isinstance(payload[1], (int, float))
            ):
                return [(payload[0], float(payload[1]))]
            for item in payload:
                pairs.extend(cls._extract_text_score_pairs(item))
        return pairs

    @staticmethod
    def _suffix_for_document(document: DocumentUploadMetadata) -> str:
        if document.file_name:
            suffix = Path(document.file_name).suffix
            if suffix:
                return suffix
        return {
            "application/pdf": ".pdf",
            "image/jpeg": ".jpg",
            "image/png": ".png",
        }.get((document.mime_type or "").lower(), ".bin")


def build_paddleocr_parser(settings: Settings) -> PaddleOCRDocumentParser:
    return PaddleOCRDocumentParser(
        model_name=settings.ocr_model or "",
        lang=settings.ocr_lang or "",
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
