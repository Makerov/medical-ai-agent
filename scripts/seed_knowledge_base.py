from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from app.core.settings import Settings, get_settings
from app.integrations.qdrant_client import (
    QdrantVectorStore,
    build_deterministic_vector,
)
from app.schemas.knowledge_base import KnowledgeSeedEntry
from scripts.setup_qdrant_collections import run_setup


def load_seed_entries(seed_dir: Path) -> tuple[KnowledgeSeedEntry, ...]:
    if not seed_dir.exists():
        msg = f"Knowledge base seed directory does not exist: {seed_dir}"
        raise FileNotFoundError(msg)

    seed_files = sorted(path for path in seed_dir.iterdir() if path.suffix.lower() == ".json")
    if not seed_files:
        msg = f"No knowledge base seed files found in {seed_dir}"
        raise FileNotFoundError(msg)

    entries = tuple(
        KnowledgeSeedEntry.model_validate_json(path.read_text(encoding="utf-8"))
        for path in seed_files
    )
    return entries


def build_seed_points(
    entries: Sequence[KnowledgeSeedEntry],
    *,
    vector_size: int,
) -> tuple[dict[str, object], ...]:
    return tuple(
        entry.to_qdrant_point(
            build_deterministic_vector(entry.search_text, dimension=vector_size)
        )
        for entry in entries
    )


def seed_knowledge_base(
    *,
    client: QdrantVectorStore,
    collection_name: str,
    seed_dir: Path,
    vector_size: int,
) -> int:
    entries = load_seed_entries(seed_dir)
    run_setup(client=client, collection_name=collection_name, vector_size=vector_size)
    points = build_seed_points(entries, vector_size=vector_size)
    client.upsert_points(collection_name=collection_name, points=points)
    return len(points)


def build_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Seed the curated Qdrant knowledge base")
    parser.add_argument("--collection-name", default=settings.qdrant_collection_name)
    parser.add_argument("--seed-dir", default=str(settings.knowledge_base_seed_dir))
    parser.add_argument("--vector-size", type=int, default=settings.qdrant_vector_size)
    return parser


def build_qdrant_client(settings: Settings | None = None):
    from scripts.setup_qdrant_collections import build_qdrant_client as build_setup_client

    return build_setup_client(settings)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = get_settings()
    client = build_qdrant_client(settings)
    seeded_count = seed_knowledge_base(
        client=client,
        collection_name=args.collection_name,
        seed_dir=Path(args.seed_dir),
        vector_size=args.vector_size,
    )
    print(f"Seeded {seeded_count} knowledge entries into {args.collection_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
