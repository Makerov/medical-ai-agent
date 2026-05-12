from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import error, request

from app.core.settings import Settings
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


class HuggingFaceRouterTransport:
    def __init__(
        self,
        *,
        base_url: str = "https://router.huggingface.co/v1/chat/completions",
        timeout_seconds: float = 60.0,
    ) -> None:
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds

    def generate_summary(
        self,
        *,
        provider_name: str,
        model_name: str,
        api_key: str | None,
        request: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        if provider_name != "huggingface":
            raise LLMClientError("provider_not_supported", "LLM provider is not supported")
        if not api_key:
            raise LLMClientError("provider_auth_missing", "HF token is not configured")

        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return only JSON matching the existing SummaryGenerationResult "
                        "shape. Do not include markdown or explanatory text."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(request, ensure_ascii=False),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        raw_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        http_request = request_module.Request(
            self._base_url,
            data=raw_body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with request_module.urlopen(http_request, timeout=self._timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raise LLMClientError("provider_request_failed", "HF provider request failed") from exc
        except TimeoutError as exc:
            raise LLMClientError("provider_timeout", "HF provider request timed out") from exc
        except OSError as exc:
            raise LLMClientError("provider_request_failed", "HF provider request failed") from exc

        try:
            payload = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise LLMClientError("invalid_provider_response", "HF response was not JSON") from exc
        if not isinstance(payload, Mapping):
            raise LLMClientError("invalid_provider_response", "HF response payload was invalid")
        return self._extract_summary_payload(payload)

    @staticmethod
    def _extract_summary_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMClientError("invalid_provider_response", "HF response missing choices")
        first_choice = choices[0]
        if not isinstance(first_choice, Mapping):
            raise LLMClientError("invalid_provider_response", "HF response choice was invalid")
        message = first_choice.get("message")
        if not isinstance(message, Mapping):
            raise LLMClientError("invalid_provider_response", "HF response message was invalid")
        content = message.get("content")
        if isinstance(content, list):
            content = "".join(
                str(item.get("text", ""))
                for item in content
                if isinstance(item, Mapping)
            )
        if not isinstance(content, str) or not content.strip():
            raise LLMClientError("invalid_provider_response", "HF response content was empty")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMClientError(
                "invalid_provider_response",
                "HF response content was not JSON",
            ) from exc
        if not isinstance(parsed, Mapping):
            raise LLMClientError("invalid_provider_response", "HF response content was invalid")
        return parsed


request_module = request


def build_operational_llm_client(settings: Settings) -> OperationalLLMClient:
    return OperationalLLMClient(
        config=LLMProviderConfig(
            provider_name=settings.llm_provider or "",
            model_name=settings.llm_model or "",
            api_key=settings.hf_token,
        ),
        transport=HuggingFaceRouterTransport(),
    )


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
            raise LLMClientError(
                "invalid_provider_response",
                "LLM provider response status was invalid",
            )
        if not isinstance(grounded_summary, Mapping):
            raise LLMClientError(
                "invalid_provider_response",
                "LLM provider response missing summary",
            )
        if failure is not None and not isinstance(failure, Mapping):
            raise LLMClientError(
                "invalid_provider_response",
                "LLM provider failure payload was invalid",
            )
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
