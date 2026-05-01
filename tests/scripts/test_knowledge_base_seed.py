from pathlib import Path

from app.integrations.qdrant_client import QdrantClientError
from app.schemas.knowledge_base import KnowledgeSeedEntry
from scripts.seed_knowledge_base import (
    load_seed_entries,
    seed_knowledge_base,
)
from scripts.setup_qdrant_collections import ensure_qdrant_collection, wait_for_qdrant_ready


class _FakeQdrantClient:
    def __init__(self) -> None:
        self.collections: dict[str, dict[str, object]] = {}
        self.create_calls: list[tuple[str, int, dict[str, object] | None]] = []
        self.upsert_calls: list[tuple[str, tuple[dict[str, object], ...]]] = []

    def collection_exists(self, collection_name: str) -> bool:
        return collection_name in self.collections

    def create_collection(
        self,
        *,
        collection_name: str,
        vector_size: int,
        metadata: dict[str, object] | None = None,
    ) -> bool:
        self.create_calls.append((collection_name, vector_size, metadata))
        self.collections.setdefault(collection_name, {"points": {}, "metadata": metadata or {}})
        return True

    def upsert_points(
        self,
        *,
        collection_name: str,
        points: tuple[dict[str, object], ...],
    ) -> int:
        self.upsert_calls.append((collection_name, points))
        collection = self.collections.setdefault(collection_name, {"points": {}, "metadata": {}})
        stored_points = collection["points"]
        assert isinstance(stored_points, dict)
        for point in points:
            stored_points[str(point["id"])] = point
        return len(points)


class _RetryingQdrantClient(_FakeQdrantClient):
    def __init__(self) -> None:
        super().__init__()
        self.collection_exists_calls = 0

    def collection_exists(self, collection_name: str) -> bool:
        self.collection_exists_calls += 1
        if self.collection_exists_calls == 1:
            raise QdrantClientError("connection_failed", "Qdrant request failed")
        return super().collection_exists(collection_name)


def test_load_seed_entries_returns_stable_order_and_validates_files() -> None:
    seed_dir = Path("data/knowledge_base")

    entries = load_seed_entries(seed_dir)

    assert entries
    assert all(isinstance(entry, KnowledgeSeedEntry) for entry in entries)
    assert [entry.knowledge_id for entry in entries] == sorted(
        entry.knowledge_id for entry in entries
    )
    assert all(entry.source_metadata.source_url for entry in entries)
    assert all(entry.limitations for entry in entries)


def test_seed_knowledge_base_is_idempotent_across_reruns() -> None:
    client = _FakeQdrantClient()
    seed_dir = Path("data/knowledge_base")

    first_run = seed_knowledge_base(
        client=client,
        collection_name="curated_medical_knowledge_v1",
        seed_dir=seed_dir,
        vector_size=384,
    )
    second_run = seed_knowledge_base(
        client=client,
        collection_name="curated_medical_knowledge_v1",
        seed_dir=seed_dir,
        vector_size=384,
    )

    assert first_run == second_run
    assert len(client.create_calls) == 1
    assert len(client.upsert_calls) == 2
    assert len(client.collections["curated_medical_knowledge_v1"]["points"]) == first_run


def test_ensure_qdrant_collection_only_creates_once() -> None:
    client = _FakeQdrantClient()

    first = ensure_qdrant_collection(
        client=client,
        collection_name="curated_medical_knowledge_v1",
        vector_size=384,
    )
    second = ensure_qdrant_collection(
        client=client,
        collection_name="curated_medical_knowledge_v1",
        vector_size=384,
    )

    assert first is True
    assert second is False
    assert len(client.create_calls) == 1


def test_wait_for_qdrant_ready_retries_connection_failures(monkeypatch) -> None:
    client = _RetryingQdrantClient()
    sleep_calls: list[float] = []

    monkeypatch.setattr(
        "scripts.setup_qdrant_collections.time.sleep",
        lambda delay: sleep_calls.append(delay),
    )

    wait_for_qdrant_ready(client=client, collection_name="curated_medical_knowledge_v1")

    assert client.collection_exists_calls == 2
    assert sleep_calls == [1.0]


def test_seed_knowledge_base_waits_for_qdrant_before_upserting(monkeypatch) -> None:
    client = _RetryingQdrantClient()
    sleep_calls: list[float] = []

    monkeypatch.setattr(
        "scripts.setup_qdrant_collections.time.sleep",
        lambda delay: sleep_calls.append(delay),
    )

    seed_dir = Path("data/knowledge_base")

    seeded_count = seed_knowledge_base(
        client=client,
        collection_name="curated_medical_knowledge_v1",
        seed_dir=seed_dir,
        vector_size=384,
    )

    assert seeded_count > 0
    assert client.collection_exists_calls == 3
    assert sleep_calls == [1.0]
    assert len(client.create_calls) == 1
    assert len(client.upsert_calls) == 1
