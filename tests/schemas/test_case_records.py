from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.case import (
    CaseCoreRecords,
    CaseRecordKind,
    CaseRecordReference,
    CaseStatus,
    PatientCase,
)


def test_case_record_reference_requires_non_empty_identifiers() -> None:
    with pytest.raises(ValidationError):
        CaseRecordReference(
            case_id="",
            record_kind=CaseRecordKind.PATIENT_PROFILE,
            record_id="profile_001",
            created_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        )

    with pytest.raises(ValidationError):
        CaseRecordReference(
            case_id="case_001",
            record_kind=CaseRecordKind.PATIENT_PROFILE,
            record_id="",
            created_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        )


def test_case_record_reference_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        CaseRecordReference(
            case_id="case_001",
            record_kind=CaseRecordKind.CONSENT,
            record_id="consent_001",
            created_at=datetime(2026, 4, 28, 6, 0),
        )


def test_case_core_records_rejects_cross_case_reference() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)

    with pytest.raises(ValidationError, match="match patient case id"):
        CaseCoreRecords(
            patient_case=PatientCase(
                case_id="case_001",
                status=CaseStatus.DRAFT,
                created_at=now,
                updated_at=now,
            ),
            documents=(
                CaseRecordReference(
                    case_id="case_002",
                    record_kind=CaseRecordKind.DOCUMENT,
                    record_id="document_001",
                    created_at=now,
                ),
            ),
        )


def test_case_core_records_rejects_reference_in_wrong_section() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)

    with pytest.raises(ValidationError, match="match aggregate section kind"):
        CaseCoreRecords(
            patient_case=PatientCase(
                case_id="case_001",
                status=CaseStatus.DRAFT,
                created_at=now,
                updated_at=now,
            ),
            summaries=(
                CaseRecordReference(
                    case_id="case_001",
                    record_kind=CaseRecordKind.DOCUMENT,
                    record_id="document_001",
                    created_at=now,
                ),
            ),
        )
