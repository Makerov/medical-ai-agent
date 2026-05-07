from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from app.schemas.rag import (
    GroundedSummaryContract,
    SummaryGenerationFailure,
    SummaryGenerationInput,
    SummaryGenerationResult,
)


class LLMClientError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class LLMClient(Protocol):
    def generate_summary(self, request: SummaryGenerationInput) -> SummaryGenerationResult: ...


@dataclass(frozen=True)
class LLMProviderConfig:
    provider_name: str
    model_name: str
    api_key: str | None = None


class OperationalLLMClient:
    def __init__(self, *, config: LLMProviderConfig, transport: Any) -> None:
        self._config = config
        self._transport = transport

    def generate_summary(self, request: SummaryGenerationInput) -> SummaryGenerationResult:
        try:
            response = self._transport.generate_summary(
                provider_name=self._config.provider_name,
                model_name=self._config.model_name,
                api_key=self._config.api_key,
                request=request.model_dump(mode="json"),
            )
        except LLMClientError:
            raise
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise LLMClientError("provider_request_failed", "LLM request failed") from exc

        if not isinstance(response, Mapping):
            raise LLMClientError("invalid_provider_response", "LLM provider response was invalid")
        return self._parse_response(request=request, response=response)

    def _parse_response(
        self,
        *,
        request: SummaryGenerationInput,
        response: Mapping[str, Any],
    ) -> SummaryGenerationResult:
        status = response.get("status")
        failure = response.get("failure")
        grounded_summary = response.get("grounded_summary")
        grounding_notes = response.get("grounding_notes", ())
        if status not in {"generated", "generated_with_incomplete_grounding"}:
            raise LLMClientError("invalid_provider_response", "LLM provider response status was invalid")
        if not isinstance(grounded_summary, Mapping):
            raise LLMClientError("invalid_provider_response", "LLM provider response missing summary")
        if failure is not None and not isinstance(failure, Mapping):
            raise LLMClientError("invalid_provider_response", "LLM provider failure payload was invalid")
        return SummaryGenerationResult(
            status=status,
            grounded_summary=GroundedSummaryContract.model_validate(grounded_summary),
            failure=None
            if failure is None
            else SummaryGenerationFailure.model_validate(failure),
            grounding_is_complete=bool(response.get("grounding_is_complete", True)),
            grounding_notes=tuple(str(item) for item in grounding_notes if str(item).strip()),
            llm_provider_name=response.get("llm_provider_name") or self._config.provider_name,
            structured_inputs=request,
        )
