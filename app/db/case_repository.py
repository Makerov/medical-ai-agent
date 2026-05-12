from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Protocol

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.db.postgres import ConnectionFactory, build_operational_state_bootstrap
from app.schemas.case import (
    CaseReadinessSnapshot,
    CaseRecordKind,
    CaseRecordReference,
    CaseTransition,
    PatientCase,
)
from app.schemas.extraction import CaseExtractionRecord
from app.schemas.indicator import CaseIndicatorExtractionRecord
from app.schemas.document_storage import PersistedDocumentRecord


class CaseRepository(Protocol):
    def get_case(self, case_id: str) -> PatientCase | None: ...

    def save_case(self, patient_case: PatientCase) -> PatientCase: ...

    def list_record_references(self, case_id: str) -> tuple[CaseRecordReference, ...]: ...

    def get_record_reference(
        self,
        case_id: str,
        record_kind: CaseRecordKind,
        record_id: str,
    ) -> CaseRecordReference | None: ...

    def save_record_reference(self, reference: CaseRecordReference) -> CaseRecordReference: ...

    def get_document_storage_record(
        self,
        case_id: str,
        document_id: str,
    ) -> PersistedDocumentRecord | None: ...

    def list_document_storage_records(self, case_id: str) -> tuple[PersistedDocumentRecord, ...]: ...

    def save_document_storage_record(
        self,
        record: PersistedDocumentRecord,
    ) -> PersistedDocumentRecord: ...

    def list_extraction_records(self, case_id: str) -> tuple[CaseExtractionRecord, ...]: ...

    def get_extraction_record(
        self,
        case_id: str,
        extraction_reference_id: str,
    ) -> CaseExtractionRecord | None: ...

    def save_extraction_record(
        self,
        extraction_record: CaseExtractionRecord,
    ) -> CaseExtractionRecord: ...

    def list_indicator_records(self, case_id: str) -> tuple[CaseIndicatorExtractionRecord, ...]: ...

    def get_indicator_record(
        self,
        case_id: str,
        indicator_reference_id: str,
    ) -> CaseIndicatorExtractionRecord | None: ...

    def save_indicator_record(
        self,
        indicator_record: CaseIndicatorExtractionRecord,
    ) -> CaseIndicatorExtractionRecord: ...

    def get_readiness_snapshot(self, case_id: str) -> CaseReadinessSnapshot | None: ...

    def save_readiness_snapshot(
        self,
        case_id: str,
        snapshot: CaseReadinessSnapshot,
    ) -> CaseReadinessSnapshot: ...

    def append_transition(self, transition: CaseTransition) -> CaseTransition: ...

    def list_transitions(self, case_id: str) -> tuple[CaseTransition, ...]: ...


class InMemoryCaseRepository:
    def __init__(self) -> None:
        self._cases: dict[str, PatientCase] = {}
        self._record_references: dict[str, list[CaseRecordReference]] = {}
        self._document_storage_records: dict[str, dict[str, PersistedDocumentRecord]] = {}
        self._extraction_records: dict[str, list[CaseExtractionRecord]] = {}
        self._indicator_records: dict[str, list[CaseIndicatorExtractionRecord]] = {}
        self._readiness_snapshots: dict[str, CaseReadinessSnapshot] = {}
        self._transitions: dict[str, list[CaseTransition]] = {}

    def get_case(self, case_id: str) -> PatientCase | None:
        return self._cases.get(case_id)

    def save_case(self, patient_case: PatientCase) -> PatientCase:
        self._cases[patient_case.case_id] = patient_case
        return patient_case

    def list_record_references(self, case_id: str) -> tuple[CaseRecordReference, ...]:
        return tuple(self._record_references.get(case_id, ()))

    def get_record_reference(
        self,
        case_id: str,
        record_kind: CaseRecordKind,
        record_id: str,
    ) -> CaseRecordReference | None:
        for reference in self._record_references.get(case_id, ()):
            if reference.record_kind == record_kind and reference.record_id == record_id:
                return reference
        return None

    def save_record_reference(self, reference: CaseRecordReference) -> CaseRecordReference:
        self._record_references.setdefault(reference.case_id, []).append(reference)
        return reference

    def get_document_storage_record(
        self,
        case_id: str,
        document_id: str,
    ) -> PersistedDocumentRecord | None:
        return self._document_storage_records.get(case_id, {}).get(document_id)

    def list_document_storage_records(self, case_id: str) -> tuple[PersistedDocumentRecord, ...]:
        records = self._document_storage_records.get(case_id, {})
        return tuple(records[key] for key in sorted(records))

    def save_document_storage_record(
        self,
        record: PersistedDocumentRecord,
    ) -> PersistedDocumentRecord:
        case_records = self._document_storage_records.setdefault(record.case_id, {})
        case_records.setdefault(record.document_id, record)
        return case_records[record.document_id]

    def list_extraction_records(self, case_id: str) -> tuple[CaseExtractionRecord, ...]:
        return tuple(self._extraction_records.get(case_id, ()))

    def get_extraction_record(
        self,
        case_id: str,
        extraction_reference_id: str,
    ) -> CaseExtractionRecord | None:
        for record in self._extraction_records.get(case_id, ()):
            if record.extraction_reference.record_id == extraction_reference_id:
                return record
        return None

    def save_extraction_record(
        self,
        extraction_record: CaseExtractionRecord,
    ) -> CaseExtractionRecord:
        self._extraction_records.setdefault(extraction_record.case_id, []).append(extraction_record)
        return extraction_record

    def list_indicator_records(self, case_id: str) -> tuple[CaseIndicatorExtractionRecord, ...]:
        return tuple(self._indicator_records.get(case_id, ()))

    def get_indicator_record(
        self,
        case_id: str,
        indicator_reference_id: str,
    ) -> CaseIndicatorExtractionRecord | None:
        for record in self._indicator_records.get(case_id, ()):
            if record.indicator_reference.record_id == indicator_reference_id:
                return record
        return None

    def save_indicator_record(
        self,
        indicator_record: CaseIndicatorExtractionRecord,
    ) -> CaseIndicatorExtractionRecord:
        self._indicator_records.setdefault(indicator_record.case_id, []).append(indicator_record)
        return indicator_record

    def get_readiness_snapshot(self, case_id: str) -> CaseReadinessSnapshot | None:
        return self._readiness_snapshots.get(case_id)

    def save_readiness_snapshot(
        self,
        case_id: str,
        snapshot: CaseReadinessSnapshot,
    ) -> CaseReadinessSnapshot:
        self._readiness_snapshots[case_id] = snapshot
        return snapshot

    def append_transition(self, transition: CaseTransition) -> CaseTransition:
        self._transitions.setdefault(transition.case_id, []).append(transition)
        return transition

    def list_transitions(self, case_id: str) -> tuple[CaseTransition, ...]:
        return tuple(self._transitions.get(case_id, ()))


class PostgresCaseRepository:
    def __init__(
        self,
        database_url: str,
        *,
        connection_factory: ConnectionFactory | None = None,
        bootstrap: bool = False,
    ) -> None:
        self._database_url = database_url
        self._connection_factory = connection_factory or self._default_connection_factory
        if bootstrap:
            build_operational_state_bootstrap(
                database_url,
                connection_factory=self._connection_factory,
            ).ensure_schema()

    def get_case(self, case_id: str) -> PatientCase | None:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT payload FROM cases WHERE case_id = %s", (case_id,))
                row = cursor.fetchone()
        return None if row is None else PatientCase.model_validate(_payload(row["payload"]))

    def save_case(self, patient_case: PatientCase) -> PatientCase:
        payload = patient_case.model_dump(mode="json")
        with self._write_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO cases (case_id, status, created_at, updated_at, payload)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (case_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        created_at = EXCLUDED.created_at,
                        updated_at = EXCLUDED.updated_at,
                        payload = EXCLUDED.payload
                    """,
                    (
                        patient_case.case_id,
                        patient_case.status.value,
                        patient_case.created_at,
                        patient_case.updated_at,
                        Jsonb(payload),
                    ),
                )
        return patient_case

    def list_record_references(self, case_id: str) -> tuple[CaseRecordReference, ...]:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT payload
                    FROM case_record_references
                    WHERE case_id = %s
                    ORDER BY created_at, record_kind, record_id
                    """,
                    (case_id,),
                )
                rows = cursor.fetchall()
        return tuple(CaseRecordReference.model_validate(_payload(row["payload"])) for row in rows)

    def get_record_reference(
        self,
        case_id: str,
        record_kind: CaseRecordKind,
        record_id: str,
    ) -> CaseRecordReference | None:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT payload
                    FROM case_record_references
                    WHERE case_id = %s AND record_kind = %s AND record_id = %s
                    """,
                    (case_id, record_kind.value, record_id),
                )
                row = cursor.fetchone()
        return None if row is None else CaseRecordReference.model_validate(_payload(row["payload"]))

    def save_record_reference(self, reference: CaseRecordReference) -> CaseRecordReference:
        payload = reference.model_dump(mode="json")
        with self._write_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO case_record_references (
                        case_id,
                        record_kind,
                        record_id,
                        created_at,
                        payload
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (case_id, record_kind, record_id) DO NOTHING
                    """,
                    (
                        reference.case_id,
                        reference.record_kind.value,
                        reference.record_id,
                        reference.created_at,
                        Jsonb(payload),
                    ),
                )
        return reference

    def get_document_storage_record(
        self,
        case_id: str,
        document_id: str,
    ) -> PersistedDocumentRecord | None:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT payload
                    FROM case_document_storage_records
                    WHERE case_id = %s AND document_id = %s
                    """,
                    (case_id, document_id),
                )
                row = cursor.fetchone()
        return None if row is None else PersistedDocumentRecord.model_validate(_payload(row["payload"]))

    def list_document_storage_records(self, case_id: str) -> tuple[PersistedDocumentRecord, ...]:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT payload
                    FROM case_document_storage_records
                    WHERE case_id = %s
                    ORDER BY created_at, document_id
                    """,
                    (case_id,),
                )
                rows = cursor.fetchall()
        return tuple(PersistedDocumentRecord.model_validate(_payload(row["payload"])) for row in rows)

    def save_document_storage_record(
        self,
        record: PersistedDocumentRecord,
    ) -> PersistedDocumentRecord:
        payload = record.model_dump(mode="json")
        with self._write_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO case_document_storage_records (
                        case_id,
                        document_id,
                        created_at,
                        storage_status,
                        artifact_path,
                        payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (case_id, document_id) DO NOTHING
                    """,
                    (
                        record.case_id,
                        record.document_id,
                        record.created_at,
                        record.storage_status.value,
                        record.artifact_path,
                        Jsonb(payload),
                    ),
                )
        return record

    def list_extraction_records(self, case_id: str) -> tuple[CaseExtractionRecord, ...]:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT payload
                    FROM case_extraction_records
                    WHERE case_id = %s
                    ORDER BY extracted_at, extraction_reference_id
                    """,
                    (case_id,),
                )
                rows = cursor.fetchall()
        return tuple(CaseExtractionRecord.model_validate(_payload(row["payload"])) for row in rows)

    def get_extraction_record(
        self,
        case_id: str,
        extraction_reference_id: str,
    ) -> CaseExtractionRecord | None:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT payload
                    FROM case_extraction_records
                    WHERE case_id = %s AND extraction_reference_id = %s
                    """,
                    (case_id, extraction_reference_id),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        return CaseExtractionRecord.model_validate(_payload(row["payload"]))

    def save_extraction_record(
        self,
        extraction_record: CaseExtractionRecord,
    ) -> CaseExtractionRecord:
        payload = extraction_record.model_dump(mode="json")
        with self._write_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO case_extraction_records (
                        case_id,
                        extraction_reference_id,
                        extracted_at,
                        payload
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (case_id, extraction_reference_id) DO NOTHING
                    """,
                    (
                        extraction_record.case_id,
                        extraction_record.extraction_reference.record_id,
                        extraction_record.extracted_at,
                        Jsonb(payload),
                    ),
                )
        return extraction_record

    def list_indicator_records(self, case_id: str) -> tuple[CaseIndicatorExtractionRecord, ...]:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT payload
                    FROM case_indicator_records
                    WHERE case_id = %s
                    ORDER BY extracted_at, indicator_reference_id
                    """,
                    (case_id,),
                )
                rows = cursor.fetchall()
        return tuple(
            CaseIndicatorExtractionRecord.model_validate(_payload(row["payload"])) for row in rows
        )

    def get_indicator_record(
        self,
        case_id: str,
        indicator_reference_id: str,
    ) -> CaseIndicatorExtractionRecord | None:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT payload
                    FROM case_indicator_records
                    WHERE case_id = %s AND indicator_reference_id = %s
                    """,
                    (case_id, indicator_reference_id),
                )
                row = cursor.fetchone()
        return (
            None
            if row is None
            else CaseIndicatorExtractionRecord.model_validate(_payload(row["payload"]))
        )

    def save_indicator_record(
        self,
        indicator_record: CaseIndicatorExtractionRecord,
    ) -> CaseIndicatorExtractionRecord:
        payload = indicator_record.model_dump(mode="json")
        with self._write_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO case_indicator_records (
                        case_id,
                        indicator_reference_id,
                        extracted_at,
                        payload
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (case_id, indicator_reference_id) DO NOTHING
                    """,
                    (
                        indicator_record.case_id,
                        indicator_record.indicator_reference.record_id,
                        indicator_record.extracted_at,
                        Jsonb(payload),
                    ),
                )
        return indicator_record

    def get_readiness_snapshot(self, case_id: str) -> CaseReadinessSnapshot | None:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT payload FROM case_readiness_snapshots WHERE case_id = %s",
                    (case_id,),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        return CaseReadinessSnapshot.model_validate(_payload(row["payload"]))

    def save_readiness_snapshot(
        self,
        case_id: str,
        snapshot: CaseReadinessSnapshot,
    ) -> CaseReadinessSnapshot:
        payload = snapshot.model_dump(mode="json")
        with self._write_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO case_readiness_snapshots (case_id, payload)
                    VALUES (%s, %s)
                    ON CONFLICT (case_id) DO UPDATE SET
                        payload = EXCLUDED.payload
                    """,
                    (case_id, Jsonb(payload)),
                )
        return snapshot

    def append_transition(self, transition: CaseTransition) -> CaseTransition:
        payload = transition.model_dump(mode="json")
        with self._write_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO case_status_transitions (
                        case_id,
                        from_status,
                        to_status,
                        transitioned_at,
                        payload
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (case_id, from_status, to_status, transitioned_at) DO NOTHING
                    """,
                    (
                        transition.case_id,
                        transition.from_status.value,
                        transition.to_status.value,
                        transition.transitioned_at,
                        Jsonb(payload),
                    ),
                )
        return transition

    def list_transitions(self, case_id: str) -> tuple[CaseTransition, ...]:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT payload
                    FROM case_status_transitions
                    WHERE case_id = %s
                    ORDER BY transitioned_at, from_status, to_status
                    """,
                    (case_id,),
                )
                rows = cursor.fetchall()
        return tuple(CaseTransition.model_validate(_payload(row["payload"])) for row in rows)

    @contextmanager
    def _connection(self) -> Any:
        connection = self._connection_factory()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def _write_connection(self) -> Any:
        connection = self._connection_factory()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _default_connection_factory(self) -> psycopg.Connection[Any]:
        return psycopg.connect(self._database_url)


def _payload(value: object) -> dict[str, object]:
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, dict):
        return value
    msg = "Unexpected PostgreSQL payload type"
    raise TypeError(msg)
