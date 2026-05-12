from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.rows import dict_row


class PostgresOperationalStateError(RuntimeError):
    def __init__(self, *, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(detail)


@dataclass(frozen=True)
class OperationalStateSchemaStatus:
    is_ready: bool
    missing_tables: tuple[str, ...] = ()


ConnectionFactory = Callable[[], psycopg.Connection[Any]]

_REQUIRED_TABLES = (
    "cases",
    "case_status_transitions",
    "case_record_references",
    "case_document_storage_records",
    "case_extraction_records",
    "case_indicator_records",
    "case_readiness_snapshots",
    "audit_events",
    "summary_audit_traces",
)

_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS cases (
        case_id TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL,
        payload JSONB NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS case_status_transitions (
        case_id TEXT NOT NULL,
        from_status TEXT NOT NULL,
        to_status TEXT NOT NULL,
        transitioned_at TIMESTAMPTZ NOT NULL,
        payload JSONB NOT NULL,
        PRIMARY KEY (case_id, from_status, to_status, transitioned_at)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS case_record_references (
        case_id TEXT NOT NULL,
        record_kind TEXT NOT NULL,
        record_id TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        payload JSONB NOT NULL,
        PRIMARY KEY (case_id, record_kind, record_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS case_document_storage_records (
        case_id TEXT NOT NULL,
        document_id TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        storage_status TEXT NOT NULL,
        artifact_path TEXT NOT NULL,
        payload JSONB NOT NULL,
        PRIMARY KEY (case_id, document_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS case_extraction_records (
        case_id TEXT NOT NULL,
        extraction_reference_id TEXT NOT NULL,
        extracted_at TIMESTAMPTZ NOT NULL,
        payload JSONB NOT NULL,
        PRIMARY KEY (case_id, extraction_reference_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS case_indicator_records (
        case_id TEXT NOT NULL,
        indicator_reference_id TEXT NOT NULL,
        extracted_at TIMESTAMPTZ NOT NULL,
        payload JSONB NOT NULL,
        PRIMARY KEY (case_id, indicator_reference_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS case_readiness_snapshots (
        case_id TEXT PRIMARY KEY,
        payload JSONB NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_events (
        event_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        payload JSONB NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS summary_audit_traces (
        trace_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        summary_record_id TEXT NOT NULL,
        payload JSONB NOT NULL
    )
    """,
)


class PostgresOperationalStateBootstrap:
    def __init__(
        self,
        database_url: str,
        *,
        connection_factory: ConnectionFactory | None = None,
    ) -> None:
        self._database_url = database_url
        self._connection_factory = connection_factory or self._default_connection_factory

    def ensure_schema(self) -> None:
        try:
            with self._connection() as connection:
                with connection.cursor() as cursor:
                    for statement in _SCHEMA_STATEMENTS:
                        cursor.execute(statement)
                connection.commit()
        except psycopg.Error as exc:
            raise PostgresOperationalStateError(
                code="case_audit_storage_bootstrap_failed",
                detail="PostgreSQL operational state bootstrap failed.",
            ) from exc

    def verify_schema(self) -> OperationalStateSchemaStatus:
        try:
            with self._connection() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = ANY(%s)
                        """,
                        (_REQUIRED_TABLES,),
                    )
                    present = {
                        str(row["table_name"])
                        for row in cursor.fetchall()
                    }
        except psycopg.Error as exc:
            raise PostgresOperationalStateError(
                code="postgresql_unreachable",
                detail="PostgreSQL operational state check failed.",
            ) from exc

        missing_tables = tuple(table for table in _REQUIRED_TABLES if table not in present)
        return OperationalStateSchemaStatus(
            is_ready=not missing_tables,
            missing_tables=missing_tables,
        )

    @contextmanager
    def _connection(self) -> Any:
        connection = self._connection_factory()
        try:
            yield connection
        finally:
            connection.close()

    def _default_connection_factory(self) -> psycopg.Connection[Any]:
        return psycopg.connect(self._database_url)


def build_operational_state_bootstrap(
    database_url: str,
    *,
    connection_factory: ConnectionFactory | None = None,
) -> PostgresOperationalStateBootstrap:
    return PostgresOperationalStateBootstrap(
        database_url,
        connection_factory=connection_factory,
    )


def required_operational_state_tables() -> Sequence[str]:
    return _REQUIRED_TABLES
