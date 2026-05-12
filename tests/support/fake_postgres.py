from __future__ import annotations

from copy import deepcopy


class FakePostgresStore:
    def __init__(self) -> None:
        self.tables: dict[str, dict[object, dict[str, object]] | list[dict[str, object]]] = {}

    def connection(self) -> FakePostgresConnection:
        return FakePostgresConnection(self)


class FakePostgresConnection:
    def __init__(self, store: FakePostgresStore) -> None:
        self._store = store

    def cursor(self, *, row_factory=None):  # noqa: ANN001 - test fake mirrors psycopg
        _ = row_factory
        return FakePostgresCursor(self._store)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


class FakePostgresCursor:
    def __init__(self, store: FakePostgresStore) -> None:
        self._store = store
        self._rows: list[dict[str, object]] = []

    def __enter__(self) -> FakePostgresCursor:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001 - test fake
        _ = exc_type, exc, tb
        return None

    def execute(self, statement: str, params=None) -> None:  # noqa: ANN001 - test fake
        normalized = " ".join(statement.split())
        params = params or ()

        if normalized.startswith("CREATE TABLE IF NOT EXISTS "):
            table_name = normalized.split()[5]
            self._ensure_table(table_name)
            self._rows = []
            return
        if "FROM information_schema.tables" in normalized:
            requested = set(params[0])
            self._rows = [
                {"table_name": name}
                for name in self._store.tables
                if name in requested
            ]
            return
        if normalized.startswith("SELECT payload FROM cases WHERE case_id = %s"):
            case_row = self._mapping_table("cases").get(params[0])
            self._rows = [] if case_row is None else [{"payload": deepcopy(case_row["payload"])}]
            return
        if normalized.startswith("INSERT INTO cases "):
            self._mapping_table("cases")[params[0]] = {
                "case_id": params[0],
                "status": params[1],
                "created_at": params[2],
                "updated_at": params[3],
                "payload": self._json_payload(params[4]),
            }
            self._rows = []
            return
        if normalized.startswith(
            "SELECT payload FROM case_record_references "
            "WHERE case_id = %s AND record_kind = %s AND record_id = %s"
        ):
            key = (params[0], params[1], params[2])
            row = self._mapping_table("case_record_references").get(key)
            self._rows = [] if row is None else [{"payload": deepcopy(row["payload"])}]
            return
        if normalized.startswith(
            "SELECT payload FROM case_record_references WHERE case_id = %s ORDER BY"
        ):
            rows = [
                deepcopy(row)
                for key, row in self._mapping_table("case_record_references").items()
                if key[0] == params[0]
            ]
            rows.sort(
                key=lambda row: (row["created_at"], row["record_kind"], row["record_id"])
            )
            self._rows = [{"payload": row["payload"]} for row in rows]
            return
        if normalized.startswith("INSERT INTO case_record_references "):
            table = self._mapping_table("case_record_references")
            key = (params[0], params[1], params[2])
            table.setdefault(
                key,
                {
                    "case_id": params[0],
                    "record_kind": params[1],
                    "record_id": params[2],
                    "created_at": params[3],
                    "payload": self._json_payload(params[4]),
                },
            )
            self._rows = []
            return
        if normalized.startswith(
            "SELECT payload FROM case_document_storage_records WHERE case_id = %s AND document_id = %s"
        ):
            key = (params[0], params[1])
            row = self._mapping_table("case_document_storage_records").get(key)
            self._rows = [] if row is None else [{"payload": deepcopy(row["payload"])}]
            return
        if normalized.startswith(
            "SELECT payload FROM case_document_storage_records WHERE case_id = %s ORDER BY"
        ):
            rows = [
                deepcopy(row)
                for key, row in self._mapping_table("case_document_storage_records").items()
                if key[0] == params[0]
            ]
            rows.sort(key=lambda row: (row["created_at"], row["document_id"]))
            self._rows = [{"payload": row["payload"]} for row in rows]
            return
        if normalized.startswith("INSERT INTO case_document_storage_records "):
            table = self._mapping_table("case_document_storage_records")
            key = (params[0], params[1])
            table.setdefault(
                key,
                {
                    "case_id": params[0],
                    "document_id": params[1],
                    "created_at": params[2],
                    "storage_status": params[3],
                    "artifact_path": params[4],
                    "payload": self._json_payload(params[5]),
                },
            )
            self._rows = []
            return
        if normalized.startswith(
            "SELECT payload FROM case_extraction_records "
            "WHERE case_id = %s AND extraction_reference_id = %s"
        ):
            key = (params[0], params[1])
            row = self._mapping_table("case_extraction_records").get(key)
            self._rows = [] if row is None else [{"payload": deepcopy(row["payload"])}]
            return
        if normalized.startswith(
            "SELECT payload FROM case_extraction_records WHERE case_id = %s ORDER BY"
        ):
            rows = [
                deepcopy(row)
                for key, row in self._mapping_table("case_extraction_records").items()
                if key[0] == params[0]
            ]
            rows.sort(key=lambda row: (row["extracted_at"], row["extraction_reference_id"]))
            self._rows = [{"payload": row["payload"]} for row in rows]
            return
        if normalized.startswith("INSERT INTO case_extraction_records "):
            table = self._mapping_table("case_extraction_records")
            key = (params[0], params[1])
            table.setdefault(
                key,
                {
                    "case_id": params[0],
                    "extraction_reference_id": params[1],
                    "extracted_at": params[2],
                    "payload": self._json_payload(params[3]),
                },
            )
            self._rows = []
            return
        if normalized.startswith(
            "SELECT payload FROM case_indicator_records "
            "WHERE case_id = %s AND indicator_reference_id = %s"
        ):
            key = (params[0], params[1])
            row = self._mapping_table("case_indicator_records").get(key)
            self._rows = [] if row is None else [{"payload": deepcopy(row["payload"])}]
            return
        if normalized.startswith(
            "SELECT payload FROM case_indicator_records WHERE case_id = %s ORDER BY"
        ):
            rows = [
                deepcopy(row)
                for key, row in self._mapping_table("case_indicator_records").items()
                if key[0] == params[0]
            ]
            rows.sort(key=lambda row: (row["extracted_at"], row["indicator_reference_id"]))
            self._rows = [{"payload": row["payload"]} for row in rows]
            return
        if normalized.startswith("INSERT INTO case_indicator_records "):
            table = self._mapping_table("case_indicator_records")
            key = (params[0], params[1])
            table.setdefault(
                key,
                {
                    "case_id": params[0],
                    "indicator_reference_id": params[1],
                    "extracted_at": params[2],
                    "payload": self._json_payload(params[3]),
                },
            )
            self._rows = []
            return
        if normalized.startswith("SELECT payload FROM case_readiness_snapshots WHERE case_id = %s"):
            row = self._mapping_table("case_readiness_snapshots").get(params[0])
            self._rows = [] if row is None else [{"payload": deepcopy(row["payload"])}]
            return
        if normalized.startswith("INSERT INTO case_readiness_snapshots "):
            self._mapping_table("case_readiness_snapshots")[params[0]] = {
                "case_id": params[0],
                "payload": self._json_payload(params[1]),
            }
            self._rows = []
            return
        if normalized.startswith("INSERT INTO case_status_transitions "):
            table = self._mapping_table("case_status_transitions")
            key = (params[0], params[1], params[2], params[3])
            table.setdefault(
                key,
                {
                    "case_id": params[0],
                    "from_status": params[1],
                    "to_status": params[2],
                    "transitioned_at": params[3],
                    "payload": self._json_payload(params[4]),
                },
            )
            self._rows = []
            return
        if normalized.startswith(
            "SELECT payload FROM case_status_transitions WHERE case_id = %s ORDER BY"
        ):
            rows = [
                deepcopy(row)
                for key, row in self._mapping_table("case_status_transitions").items()
                if key[0] == params[0]
            ]
            rows.sort(
                key=lambda row: (
                    row["transitioned_at"],
                    row["from_status"],
                    row["to_status"],
                )
            )
            self._rows = [{"payload": row["payload"]} for row in rows]
            return
        if normalized.startswith("SELECT payload FROM audit_events WHERE event_id = %s"):
            row = self._mapping_table("audit_events").get(params[0])
            self._rows = [] if row is None else [{"payload": deepcopy(row["payload"])}]
            return
        if normalized.startswith("INSERT INTO audit_events "):
            self._mapping_table("audit_events").setdefault(
                params[0],
                {
                    "event_id": params[0],
                    "case_id": params[1],
                    "event_type": params[2],
                    "created_at": params[3],
                    "payload": self._json_payload(params[4]),
                },
            )
            self._rows = []
            return
        if normalized.startswith("SELECT payload FROM audit_events WHERE case_id = %s ORDER BY"):
            rows = [
                deepcopy(row)
                for row in self._mapping_table("audit_events").values()
                if row["case_id"] == params[0]
            ]
            rows.sort(key=lambda row: (row["created_at"], row["event_id"]))
            self._rows = [{"payload": row["payload"]} for row in rows]
            return
        if normalized.startswith("SELECT payload FROM summary_audit_traces WHERE trace_id = %s"):
            row = self._mapping_table("summary_audit_traces").get(params[0])
            self._rows = [] if row is None else [{"payload": deepcopy(row["payload"])}]
            return
        if normalized.startswith("INSERT INTO summary_audit_traces "):
            self._mapping_table("summary_audit_traces").setdefault(
                params[0],
                {
                    "trace_id": params[0],
                    "case_id": params[1],
                    "summary_record_id": params[2],
                    "payload": self._json_payload(params[3]),
                },
            )
            self._rows = []
            return
        if normalized.startswith(
            "SELECT payload FROM summary_audit_traces WHERE case_id = %s ORDER BY"
        ):
            rows = [
                deepcopy(row)
                for row in self._mapping_table("summary_audit_traces").values()
                if row["case_id"] == params[0]
            ]
            rows.sort(key=lambda row: (row["summary_record_id"], row["trace_id"]))
            self._rows = [{"payload": row["payload"]} for row in rows]
            return
        msg = f"Unsupported SQL in fake postgres: {normalized}"
        raise AssertionError(msg)

    def fetchone(self):
        return None if not self._rows else self._rows[0]

    def fetchall(self) -> list[dict[str, object]]:
        return list(self._rows)

    def _ensure_table(self, table_name: str) -> None:
        if table_name in {
            "cases",
            "case_readiness_snapshots",
            "audit_events",
            "summary_audit_traces",
        }:
            self._store.tables.setdefault(table_name, {})
            return
        self._store.tables.setdefault(table_name, {})

    def _mapping_table(self, table_name: str) -> dict[object, dict[str, object]]:
        table = self._store.tables.setdefault(table_name, {})
        if isinstance(table, dict):
            return table
        msg = f"Expected mapping table for {table_name}"
        raise AssertionError(msg)

    @staticmethod
    def _json_payload(value: object) -> dict[str, object]:
        payload = getattr(value, "obj", value)
        if isinstance(payload, dict):
            return deepcopy(payload)
        msg = "Unexpected fake Jsonb payload"
        raise AssertionError(msg)
