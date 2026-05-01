from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from typing import Any

from app.core.settings import Settings, get_settings
from app.integrations.qdrant_client import (
    QdrantClientError,
    QdrantHttpClient,
    QdrantVectorStore,
)

DEFAULT_COLLECTION_METADATA = {
    "collection_kind": "curated_medical_knowledge_seed",
    "embedding_strategy": "deterministic_hash_v1",
    "source_system": "medical-ai-agent",
}
DEFAULT_QDRANT_READY_RETRIES = 30
DEFAULT_QDRANT_READY_DELAY_SECONDS = 1.0


def build_qdrant_client(settings: Settings | None = None) -> QdrantHttpClient:
    active_settings = settings or get_settings()
    return QdrantHttpClient(
        base_url=active_settings.qdrant_url,
        api_key=active_settings.qdrant_api_key,
    )


def wait_for_qdrant_ready(
    *,
    client: QdrantVectorStore,
    collection_name: str,
    retries: int = DEFAULT_QDRANT_READY_RETRIES,
    delay_seconds: float = DEFAULT_QDRANT_READY_DELAY_SECONDS,
) -> None:
    for attempt in range(1, retries + 1):
        try:
            client.collection_exists(collection_name)
            return
        except QdrantClientError as exc:
            if exc.code != "connection_failed" or attempt == retries:
                raise
            time.sleep(delay_seconds)


def ensure_qdrant_collection(
    *,
    client: QdrantVectorStore,
    collection_name: str,
    vector_size: int,
    metadata: dict[str, Any] | None = None,
) -> bool:
    if client.collection_exists(collection_name):
        return False
    return client.create_collection(
        collection_name=collection_name,
        vector_size=vector_size,
        metadata=metadata or DEFAULT_COLLECTION_METADATA,
    )


def run_setup(
    *,
    client: QdrantVectorStore,
    collection_name: str,
    vector_size: int,
) -> bool:
    return ensure_qdrant_collection(
        client=client,
        collection_name=collection_name,
        vector_size=vector_size,
        metadata={
            **DEFAULT_COLLECTION_METADATA,
            "vector_size": vector_size,
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap the curated Qdrant knowledge collection",
    )
    parser.add_argument("--collection-name", default=get_settings().qdrant_collection_name)
    parser.add_argument("--vector-size", type=int, default=get_settings().qdrant_vector_size)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = get_settings()
    client = build_qdrant_client(settings)
    wait_for_qdrant_ready(client=client, collection_name=args.collection_name)
    created = run_setup(
        client=client,
        collection_name=args.collection_name,
        vector_size=args.vector_size,
    )
    if created:
        print(f"Created Qdrant collection: {args.collection_name}")
    else:
        print(f"Qdrant collection already exists: {args.collection_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
