from __future__ import annotations

import json
from datetime import date

import pytest

from app.integrations import llm_client as llm_module
from app.integrations.llm_client import (
    HuggingFaceRouterTransport,
    LLMClientError,
    LLMProviderConfig,
    OperationalLLMClient,
)
from app.schemas.knowledge_base import KnowledgeSourceMetadata
from app.schemas.rag import (
    CitationReference,
    GeneratedNarrativeClaim,
    GroundedSummaryContract,
    SummaryGenerationInput,
    SummaryValidationResult,
)


def _grounded_summary() -> GroundedSummaryContract:
    claim = GeneratedNarrativeClaim(
        claim_id="claim-1",
        text="Summary remains evidence bounded.",
        supported_citation_keys=("source-1",),
    )
    return GroundedSummaryContract(
        grounded_facts=(),
        citations=(
            CitationReference(
                citation_key="source-1",
                label="Demo source",
                source_kind="knowledge",
                source_metadata=KnowledgeSourceMetadata(
                    source_id="source-1",
                    source_title="Demo source",
                    source_url="https://example.test/source",
                    publisher="Demo",
                    source_type="medical_test_reference",
                    accessed_at=date(2026, 5, 12),
                    citation_key="source-1",
                ),
            ),
        ),
        narrative="Evidence bounded narrative.",
        claims=(claim,),
        validation=SummaryValidationResult(
            status="valid",
            supported_claims=(claim,),
            unsupported_claims=(),
            grounded_fact_count=0,
        ),
    )


class _FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def __enter__(self) -> _FakeHTTPResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_hugging_face_adapter_returns_typed_summary_result(monkeypatch) -> None:
    grounded_summary = _grounded_summary()
    provider_payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "status": "generated",
                            "grounded_summary": grounded_summary.model_dump(mode="json"),
                            "failure": None,
                            "grounding_is_complete": True,
                            "grounding_notes": ["grounding_complete"],
                            "llm_provider_name": "huggingface",
                        }
                    )
                }
            }
        ]
    }

    def fake_urlopen(http_request, timeout: float):  # noqa: ANN001
        assert http_request.headers["Authorization"] == "Bearer hf-token"
        assert timeout == 60.0
        return _FakeHTTPResponse(provider_payload)

    monkeypatch.setattr(llm_module.request_module, "urlopen", fake_urlopen)
    transport = HuggingFaceRouterTransport()
    client = OperationalLLMClient(
        config=LLMProviderConfig(
            provider_name="huggingface",
            model_name="Qwen/Qwen3-30B-A3B-Instruct-2507-FP8",
            api_key="hf-token",
        ),
        transport=transport,
    )
    request_payload = SummaryGenerationInput(
        case_id="case-1",
        grounded_summary=grounded_summary,
        extracted_facts=(),
    )

    result = client.generate_summary(request_payload)

    assert result.status == "generated"
    assert result.grounded_summary == grounded_summary
    assert result.llm_provider_name == "huggingface"
    assert result.structured_inputs == request_payload


def test_hugging_face_adapter_rejects_invalid_response(monkeypatch) -> None:
    monkeypatch.setattr(
        llm_module.request_module,
        "urlopen",
        lambda _request, timeout: _FakeHTTPResponse({"choices": []}),
    )

    with pytest.raises(LLMClientError) as exc_info:
        HuggingFaceRouterTransport().generate_summary(
            provider_name="huggingface",
            model_name="model",
            api_key="hf-token",
            request={"case_id": "case-1"},
        )

    assert exc_info.value.code == "invalid_provider_response"


def test_hugging_face_adapter_maps_provider_error(monkeypatch) -> None:
    def raise_provider_error(_request, timeout: float):  # noqa: ANN001
        raise OSError("network down")

    monkeypatch.setattr(llm_module.request_module, "urlopen", raise_provider_error)

    with pytest.raises(LLMClientError) as exc_info:
        HuggingFaceRouterTransport().generate_summary(
            provider_name="huggingface",
            model_name="model",
            api_key="hf-token",
            request={"case_id": "case-1"},
        )

    assert exc_info.value.code == "provider_request_failed"
