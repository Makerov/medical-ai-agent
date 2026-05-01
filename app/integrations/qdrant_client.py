from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from json import dumps, loads
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class QdrantClientError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class QdrantVectorStore(Protocol):
    def collection_exists(self, collection_name: str) -> bool: ...

    def create_collection(
        self,
        *,
        collection_name: str,
        vector_size: int,
        metadata: dict[str, Any] | None = None,
    ) -> bool: ...

    def upsert_points(
        self,
        *,
        collection_name: str,
        points: Sequence[Mapping[str, Any]],
    ) -> int: ...

    def query_points(
        self,
        *,
        collection_name: str,
        vector: Sequence[float],
        limit: int,
        query_filter: Mapping[str, Any] | None = None,
    ) -> list[Mapping[str, Any]]: ...


def build_deterministic_vector(text: str, *, dimension: int) -> tuple[float, ...]:
    normalized_text = text.strip()
    if dimension <= 0:
        msg = "Vector dimension must be greater than zero"
        raise ValueError(msg)
    if not normalized_text:
        msg = "Vector source text must not be empty"
        raise ValueError(msg)

    values: list[float] = []
    block_index = 0
    seed = normalized_text.encode("utf-8")
    while len(values) < dimension:
        digest = sha256(seed + block_index.to_bytes(4, byteorder="big", signed=False)).digest()
        for byte_value in digest:
            values.append(round(byte_value / 255.0, 8))
            if len(values) == dimension:
                break
        block_index += 1
    return tuple(values)


@dataclass(frozen=True)
class QdrantHttpConfig:
    base_url: str = "http://localhost:6333"
    api_key: str | None = None
    timeout_seconds: float = 10.0


class QdrantHttpClient:
    def __init__(
        self,
        *,
        base_url: str = "http://localhost:6333",
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
        opener: Callable[[Request], Any] = urlopen,
    ) -> None:
        self._config = QdrantHttpConfig(
            base_url=base_url.rstrip("/"),
            api_key=api_key.strip() if isinstance(api_key, str) and api_key.strip() else None,
            timeout_seconds=timeout_seconds,
        )
        self._opener = opener

    def collection_exists(self, collection_name: str) -> bool:
        try:
            self._request_json("GET", f"/collections/{collection_name}")
        except QdrantClientError as exc:
            if exc.code in {"collection_not_found", "not_found"}:
                return False
            raise
        return True

    def create_collection(
        self,
        *,
        collection_name: str,
        vector_size: int,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        body: dict[str, Any] = {
            "vectors": {
                "size": vector_size,
                "distance": "Cosine",
            },
        }
        if metadata:
            body["metadata"] = metadata
        try:
            self._request_json("PUT", f"/collections/{collection_name}", body=body)
        except QdrantClientError as exc:
            if exc.code in {"collection_already_exists", "http_409"}:
                return False
            raise
        return True

    def upsert_points(
        self,
        *,
        collection_name: str,
        points: Sequence[Mapping[str, Any]],
    ) -> int:
        point_list = [dict(point) for point in points]
        self._request_json(
            "PUT",
            f"/collections/{collection_name}/points",
            body={"points": point_list},
            query={"wait": "true", "ordering": "strong"},
        )
        return len(point_list)

    def query_points(
        self,
        *,
        collection_name: str,
        vector: Sequence[float],
        limit: int,
        query_filter: Mapping[str, Any] | None = None,
    ) -> list[Mapping[str, Any]]:
        body: dict[str, Any] = {
            "vector": [float(value) for value in vector],
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
        }
        if query_filter is not None:
            body["filter"] = dict(query_filter)
        response = self._request_json(
            "POST",
            f"/collections/{collection_name}/points/search",
            body=body,
        )
        if isinstance(response, dict):
            points = response.get("result", [])
        else:
            points = response or []
        if not isinstance(points, list):
            return []
        return [point for point in points if isinstance(point, Mapping)]

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> Any:
        url = f"{self._config.base_url}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        request_body = None if body is None else dumps(body, ensure_ascii=True).encode("utf-8")
        request = Request(url, data=request_body, method=method)
        request.add_header("Content-Type", "application/json")
        if self._config.api_key is not None:
            request.add_header("api-key", self._config.api_key)
        try:
            with self._opener(request) as response:
                payload = response.read()
        except HTTPError as exc:
            if exc.code == 404:
                raise QdrantClientError(
                    "collection_not_found",
                    "Qdrant collection not found",
                ) from exc
            if exc.code == 409:
                raise QdrantClientError(
                    "collection_already_exists",
                    "Qdrant collection already exists",
                ) from exc
            raise QdrantClientError(
                f"http_{exc.code}",
                f"Qdrant request failed with HTTP {exc.code}",
            ) from exc
        except URLError as exc:
            raise QdrantClientError("connection_failed", "Qdrant request failed") from exc

        if not payload:
            return None
        return loads(payload.decode("utf-8"))
