---
title: 'Operational provider adapters'
type: 'feature'
created: '2026-05-12'
status: 'done'
baseline_commit: '428e9347c7c3cf35c1089f5d885ed210ee87b244'
context: []
---

<frozen-after-approval reason="human-owned intent - do not modify unless human renegotiates">

## Intent

**Problem:** The operational profile validates some infrastructure but still lacks explicit Hugging Face LLM and PaddleOCR OCR provider configuration and wiring, so real-provider startup can silently remain unimplemented.

**Approach:** Add typed runtime settings, health/startup gates, operational adapter implementations, and focused tests so `RUNTIME_PROFILE=operational` either uses Hugging Face plus PaddleOCR or blocks/fails visibly through existing recoverable failure flows.

## Boundaries & Constraints

**Always:** Keep secrets out of health/readiness/startup responses and logs; preserve local/dev/test fixture behavior; return existing typed `SummaryGenerationResult` and `OCRClientError` failure contracts.

**Ask First:** Adding broad production compliance, replacing Telegram/document fetch architecture, or changing provider choices away from Hugging Face/PaddleOCR.

**Never:** Do not commit real secrets, do not silently fall back to mock/stub providers in operational profile, and do not log full OCR text.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Operational config valid | PostgreSQL URL, Qdrant URL, HF token, Hugging Face model, PaddleOCR model/lang, bot tokens | Settings load; readiness/startup expose provider config presence without secrets | N/A |
| Operational config invalid | Missing/wrong provider values or non-PostgreSQL DB URL | Startup/settings blocked or readiness not ready with machine-readable reason codes | No silent fallback |
| HF response valid | HF router returns JSON content matching summary contract | `OperationalLLMClient` returns typed `SummaryGenerationResult` | N/A |
| HF response invalid/error | Timeout, HTTP/provider error, malformed JSON/contract | Existing summary flow returns recoverable `summary_failed` | `LLMClientError` boundary |
| PaddleOCR result valid | OCR recognitions with text and scores | `OCRClient` receives joined text and mean confidence | N/A |
| PaddleOCR result empty/invalid | Empty text, missing/invalid confidence | Existing OCR recoverable document failure path | `OCRClientError` boundary |

</frozen-after-approval>

## Code Map

- `app/core/settings.py` -- runtime provider configuration and operational validation.
- `app/services/runtime_health_service.py` -- readiness/startup provider gates and reason codes.
- `app/integrations/llm_client.py` -- LLM contract plus operational Hugging Face transport.
- `app/integrations/ocr_client.py` -- OCR contract plus PaddleOCR parser.
- `app/services/summary_service.py` -- default operational LLM wiring.
- `app/workflow/nodes/parse_document.py` -- default operational OCR wiring.
- `pyproject.toml` -- runtime dependency declaration if needed.
- `.env.example`, `README.md` -- operator-facing provider settings/startup docs.
- `tests/api/test_health.py`, `tests/services/test_runtime_health_service.py`, `tests/integrations/*`, `tests/services/test_summary_service.py`, `tests/workflow/test_parse_document.py` -- focused coverage.

## Tasks & Acceptance

**Execution:**
- [x] `app/core/settings.py` -- add/normalize `LLM_PROVIDER`, `LLM_MODEL`, `OCR_MODEL`, `OCR_LANG` and operational validation.
- [x] `app/integrations/llm_client.py` -- add HF OpenAI-compatible router transport and parser tests.
- [x] `app/integrations/ocr_client.py` -- add PaddleOCR document parser with text/confidence aggregation and tests.
- [x] `app/services/runtime_health_service.py` -- add provider config readiness/startup checks without secret exposure.
- [x] `app/services/summary_service.py`, `app/workflow/nodes/parse_document.py` -- wire operational defaults without affecting non-operational profiles.
- [x] `.env.example`, `README.md`, `pyproject.toml` -- document provider settings and install/runtime expectations.
- [x] `tests/...` -- update/add tests for settings, readiness, HF adapter, PaddleOCR parser, and wiring.

**Acceptance Criteria:**
- Given `RUNTIME_PROFILE=operational` with the selected providers and models, when settings load, then required config is accepted and secrets remain response-only absent.
- Given operational provider config is missing or incompatible, when readiness/startup/settings are evaluated, then runtime is blocked/not ready with explicit reason codes.
- Given provider failures or invalid payloads, when summary/OCR flows run, then existing recoverable failure contracts are used.
- Given local/dev/test profiles, when existing tests and fixtures run, then mock/stub behavior remains explicit and unchanged.

## Verification

**Commands:**
- `uv run pytest tests/api/test_health.py tests/services/test_runtime_health_service.py tests/integrations/test_llm_client.py tests/integrations/test_ocr_client.py tests/services/test_summary_service.py tests/workflow/test_parse_document.py` -- expected: relevant tests pass.
