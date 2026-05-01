from app.integrations.qdrant_client import (
    QdrantClientError,
    QdrantHttpClient,
    build_deterministic_vector,
)


class _FakeResponse:
    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


def test_qdrant_client_builds_deterministic_vectors() -> None:
    vector_a = build_deterministic_vector("hemoglobin", dimension=8)
    vector_b = build_deterministic_vector("hemoglobin", dimension=8)

    assert vector_a == vector_b
    assert len(vector_a) == 8
    assert all(0.0 <= value <= 1.0 for value in vector_a)


def test_qdrant_client_sends_collection_and_point_payloads() -> None:
    requests: list[tuple[str, str, bytes | None, dict[str, str]]] = []

    def opener(request):  # noqa: ANN001
        body = request.data if request.data is not None else None
        headers = {key.lower(): value for key, value in request.headers.items()}
        requests.append((request.get_method(), request.full_url, body, headers))
        if request.get_method() == "GET":
            raise QdrantClientError(
                code="not_found",
                message="collection missing",
            )
        return _FakeResponse(200, b'{"status":"ok","result":true}')

    client = QdrantHttpClient(
        base_url="http://qdrant.local:6333",
        api_key="secret-token",
        opener=opener,
    )

    assert client.collection_exists("curated_medical_knowledge_v1") is False
    created = client.create_collection(
        collection_name="curated_medical_knowledge_v1",
        vector_size=384,
        metadata={"embedding_strategy": "deterministic_hash_v1"},
    )
    upserted = client.upsert_points(
        collection_name="curated_medical_knowledge_v1",
        points=(
            {
                "id": "medlineplus_hemoglobin_test",
                "vector": [0.1, 0.2, 0.3],
                "payload": {"knowledge_id": "medlineplus_hemoglobin_test"},
            },
        ),
    )

    assert created is True
    assert upserted == 1
    assert requests[0][0] == "GET"
    assert requests[1][0] == "PUT"
    assert requests[1][1] == "http://qdrant.local:6333/collections/curated_medical_knowledge_v1"
    assert b'"size": 384' in (requests[1][2] or b"")
    assert b'"Cosine"' in (requests[1][2] or b"")
    assert requests[2][1].startswith(
        "http://qdrant.local:6333/collections/curated_medical_knowledge_v1/points"
    )
    assert "wait=true" in requests[2][1]
    assert "ordering=strong" in requests[2][1]
    assert b'"medlineplus_hemoglobin_test"' in (requests[2][2] or b"")
    assert requests[2][3]["api-key"] == "secret-token"
