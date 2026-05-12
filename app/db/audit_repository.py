from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Protocol

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.db.postgres import ConnectionFactory, build_operational_state_bootstrap
from app.schemas.audit import AuditEvent, SummaryAuditTrace


class AuditRepository(Protocol):
    def get_event(self, event_id: str) -> AuditEvent | None: ...

    def save_event(self, event: AuditEvent) -> AuditEvent: ...

    def list_case_events(self, case_id: str) -> tuple[AuditEvent, ...]: ...

    def get_summary_trace(self, trace_id: str) -> SummaryAuditTrace | None: ...

    def save_summary_trace(self, trace: SummaryAuditTrace) -> SummaryAuditTrace: ...

    def list_case_summary_traces(self, case_id: str) -> tuple[SummaryAuditTrace, ...]: ...


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self._events_by_id: dict[str, AuditEvent] = {}
        self._summary_traces_by_id: dict[str, SummaryAuditTrace] = {}

    def get_event(self, event_id: str) -> AuditEvent | None:
        return self._events_by_id.get(event_id)

    def save_event(self, event: AuditEvent) -> AuditEvent:
        self._events_by_id[event.event_id] = event
        return event

    def list_case_events(self, case_id: str) -> tuple[AuditEvent, ...]:
        return tuple(event for event in self._events_by_id.values() if event.case_id == case_id)

    def get_summary_trace(self, trace_id: str) -> SummaryAuditTrace | None:
        return self._summary_traces_by_id.get(trace_id)

    def save_summary_trace(self, trace: SummaryAuditTrace) -> SummaryAuditTrace:
        self._summary_traces_by_id[trace.trace_id] = trace
        return trace

    def list_case_summary_traces(self, case_id: str) -> tuple[SummaryAuditTrace, ...]:
        return tuple(
            trace for trace in self._summary_traces_by_id.values() if trace.case_id == case_id
        )


class PostgresAuditRepository:
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

    def get_event(self, event_id: str) -> AuditEvent | None:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT payload FROM audit_events WHERE event_id = %s", (event_id,))
                row = cursor.fetchone()
        return None if row is None else AuditEvent.model_validate(_payload(row["payload"]))

    def save_event(self, event: AuditEvent) -> AuditEvent:
        payload = event.model_dump(mode="json")
        with self._write_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO audit_events (
                        event_id,
                        case_id,
                        event_type,
                        created_at,
                        payload
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    (
                        event.event_id,
                        event.case_id,
                        event.event_type.value,
                        event.created_at,
                        Jsonb(payload),
                    ),
                )
        return event

    def list_case_events(self, case_id: str) -> tuple[AuditEvent, ...]:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT payload
                    FROM audit_events
                    WHERE case_id = %s
                    ORDER BY created_at, event_id
                    """,
                    (case_id,),
                )
                rows = cursor.fetchall()
        return tuple(AuditEvent.model_validate(_payload(row["payload"])) for row in rows)

    def get_summary_trace(self, trace_id: str) -> SummaryAuditTrace | None:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT payload FROM summary_audit_traces WHERE trace_id = %s",
                    (trace_id,),
                )
                row = cursor.fetchone()
        return None if row is None else SummaryAuditTrace.model_validate(_payload(row["payload"]))

    def save_summary_trace(self, trace: SummaryAuditTrace) -> SummaryAuditTrace:
        payload = trace.model_dump(mode="json")
        with self._write_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO summary_audit_traces (
                        trace_id,
                        case_id,
                        summary_record_id,
                        payload
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (trace_id) DO NOTHING
                    """,
                    (
                        trace.trace_id,
                        trace.case_id,
                        trace.summary_reference.record_id,
                        Jsonb(payload),
                    ),
                )
        return trace

    def list_case_summary_traces(self, case_id: str) -> tuple[SummaryAuditTrace, ...]:
        with self._connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT payload
                    FROM summary_audit_traces
                    WHERE case_id = %s
                    ORDER BY summary_record_id, trace_id
                    """,
                    (case_id,),
                )
                rows = cursor.fetchall()
        return tuple(SummaryAuditTrace.model_validate(_payload(row["payload"])) for row in rows)

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
