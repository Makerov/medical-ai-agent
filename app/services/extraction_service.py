import re
from collections.abc import Callable, Iterable
from datetime import datetime

from pydantic import ValidationError

from app.schemas.case import CaseRecordKind, CaseRecordReference, utc_now
from app.schemas.extraction import CaseExtractionRecord
from app.schemas.indicator import (
    CaseIndicatorExtractionRecord,
    StructuredMedicalIndicator,
)
from app.services.case_service import CaseService

Clock = Callable[[], datetime]

_INDICATOR_LINE_PATTERN = re.compile(
    r"^\s*(?P<name>.+?)\s*(?:[:=]|-)?\s*"
    r"(?P<value>[+-]?\d+(?:[.,]\d+)?)\s+"
    r"(?P<unit>[^\s,;]+)\s*$"
)


class ExtractionService:
    def __init__(
        self,
        *,
        case_service: CaseService,
        clock: Clock = utc_now,
    ) -> None:
        self._case_service = case_service
        self._clock = clock

    def extract_indicators(
        self,
        *,
        case_id: str,
        extraction_record: CaseExtractionRecord,
    ) -> CaseIndicatorExtractionRecord | None:
        if extraction_record.case_id != case_id:
            msg = "Extraction record must belong to the requested case"
            raise ValueError(msg)
        source_document_reference = extraction_record.source_document_reference
        indicator_reference = self._build_indicator_reference(source_document_reference)

        existing_record = self._find_existing_indicator_record(
            case_id,
            indicator_reference.record_id,
        )
        if existing_record is not None:
            self._case_service.attach_case_record_reference(indicator_reference)
            return existing_record

        indicators = tuple(
            indicator
            for indicator in self._build_candidate_indicators(
                case_id=case_id,
                source_document_reference=source_document_reference,
                extracted_text=extraction_record.extracted_text,
                confidence=extraction_record.confidence,
                extracted_at=extraction_record.extracted_at,
                provider_name=extraction_record.provider_name,
            )
            if indicator is not None
        )
        if not indicators:
            return None

        indicator_record = CaseIndicatorExtractionRecord(
            case_id=case_id,
            source_document=extraction_record.source_document,
            source_document_reference=source_document_reference,
            raw_extraction_reference=extraction_record.extraction_reference,
            indicator_reference=indicator_reference,
            indicators=indicators,
            extracted_at=extraction_record.extracted_at,
            provider_name=extraction_record.provider_name,
        )
        attached_indicator_record = self._case_service.attach_case_indicator_record(
            indicator_record,
        )
        self._case_service.attach_case_record_reference(indicator_reference)
        return attached_indicator_record

    @staticmethod
    def _build_indicator_reference(
        source_document_reference: CaseRecordReference,
    ) -> CaseRecordReference:
        return CaseRecordReference(
            case_id=source_document_reference.case_id,
            record_kind=CaseRecordKind.INDICATOR,
            record_id=f"structured_indicator:{source_document_reference.record_id}",
            created_at=source_document_reference.created_at,
        )

    def _find_existing_indicator_record(
        self,
        case_id: str,
        indicator_reference_id: str,
    ) -> CaseIndicatorExtractionRecord | None:
        for record in self._case_service.get_case_indicator_records(case_id):
            if record.indicator_reference.record_id == indicator_reference_id:
                return record
        return None

    def _build_candidate_indicators(
        self,
        *,
        case_id: str,
        source_document_reference: CaseRecordReference,
        extracted_text: str,
        confidence: float,
        extracted_at: datetime,
        provider_name: str | None,
    ) -> Iterable[StructuredMedicalIndicator | None]:
        for line in extracted_text.splitlines():
            candidate = self._parse_indicator_candidate(
                case_id=case_id,
                source_document_reference=source_document_reference,
                line=line,
                confidence=confidence,
                extracted_at=extracted_at,
                provider_name=provider_name,
            )
            if candidate is not None:
                yield candidate

    def _parse_indicator_candidate(
        self,
        *,
        case_id: str,
        source_document_reference: CaseRecordReference,
        line: str,
        confidence: float,
        extracted_at: datetime,
        provider_name: str | None,
    ) -> StructuredMedicalIndicator | None:
        normalized_line = line.strip()
        if not normalized_line:
            return None

        match = _INDICATOR_LINE_PATTERN.match(normalized_line)
        if match is None:
            return None

        name = match.group("name").strip()
        value_text = match.group("value").replace(",", ".").strip()
        unit = match.group("unit").strip().rstrip(".,;")
        try:
            value = self._normalize_value(value_text)
            return StructuredMedicalIndicator(
                case_id=case_id,
                name=name,
                value=value,
                unit=unit,
                confidence=confidence,
                source_document_reference=source_document_reference,
                extracted_at=extracted_at,
                provider_name=provider_name,
            )
        except (ValidationError, ValueError):
            return None

    @staticmethod
    def _normalize_value(value_text: str) -> int | float | str:
        if value_text.isdigit() or (value_text.startswith("-") and value_text[1:].isdigit()):
            return int(value_text)
        try:
            return float(value_text)
        except ValueError:
            return value_text
