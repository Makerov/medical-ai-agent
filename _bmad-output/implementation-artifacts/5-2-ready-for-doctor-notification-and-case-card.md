# Story 5.2: Ready for Doctor Notification and Case Card

Status: ready-for-dev

## Story

Как врач,
я хочу получать уведомление, когда case готов к review, и открывать structured case card,
чтобы быстро понять цель пациента, ключевые факты, uncertainty, source references и safety boundary без чтения длинного сырого контента.

## Acceptance Criteria

1. **Дано** case переведен в `ready_for_doctor`
   **Когда** `doctor_bot` получает событие готовности
   **Тогда** allowed doctor identity получает concise notification о том, что case готов к review
   **И** notification явно сообщает, что AI подготовил материалы для врача, но не заменяет clinical review.

2. **Дано** allowed doctor открывает ready case
   **Когда** backend формирует doctor-facing delivery
   **Тогда** врач получает structured case card с фиксированным порядком секций
   **И** card включает как минимум goal, document list, extracted facts, uncertainty markers, source references, safety status и AI boundary label.

3. **Дано** case не готов к review, safety validation failed, или handoff prerequisites missing
   **Когда** doctor-facing delivery запрашивается
   **Тогда** система возвращает structured rejection вместо card
   **И** rejection clearly indicates case is not ready for doctor review without pretending the case is fully grounded.

4. **Дано** runtime profile degraded, retrieval/provider outputs incomplete, или source data unavailable
   **Когда** doctor-facing card is built
   **Тогда** card visibly preserves uncertainty and limitation markers
   **И** output must not read as a fully grounded clinical conclusion.

## Story Foundation

Epic 5 delivers doctor handoff and auditability. This story is the first user-visible handoff surface in that epic: it turns a ready case into a concise doctor notification and a structured card that is safe to review inside Telegram.

### Business Value

- Reduces time for a doctor to orient on a ready case.
- Makes the transition to doctor review explicit instead of implicit.
- Keeps AI-prepared content clearly bounded from clinical decision-making.
- Creates the primary doctor-facing operational surface that later audit and provenance flows can build on.

### Story Scope

This story should deliver the ready-case notification and the structured doctor case card only. It must not add audit explorer UX, case-scoped drill-down views, or new access-control rules beyond the existing allowlist boundary.

## Developer Context

### What Already Exists

The repository already contains most of the underlying handoff pipeline this story should use rather than recreate:

- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py) already implements `mark_case_ready_for_review()` and `get_doctor_case_card()`, including allowlist authorization, readiness gating, safety validation, audit recording, notification delivery, and case card assembly.
- [`app/bots/doctor_bot.py`](/Users/maker/Work/medical-ai-agent/app/bots/doctor_bot.py) already sends ready-case notifications and case cards through thin async adapter functions.
- [`app/bots/messages.py`](/Users/maker/Work/medical-ai-agent/app/bots/messages.py) already contains doctor-facing message copy for ready notifications and structured card headers.
- [`app/schemas/handoff.py`](/Users/maker/Work/medical-ai-agent/app/schemas/handoff.py) already defines typed contracts for doctor notifications, rejections, case cards, source references, review warnings, and safety-related card state.
- [`app/services/case_service.py`](/Users/maker/Work/medical-ai-agent/app/services/case_service.py) already evaluates handoff readiness and blocks cases that do not satisfy prerequisites.
- [`app/services/safety_service.py`](/Users/maker/Work/medical-ai-agent/app/services/safety_service.py) already provides the safety gate used before doctor-facing output is delivered.
- [`tests/services/test_handoff_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_handoff_service.py) already exercises ready-case delivery, allowlist rejection, safety-blocked card behavior, and degraded presentation expectations.
- [`tests/bots/test_doctor_bot.py`](/Users/maker/Work/medical-ai-agent/tests/bots/test_doctor_bot.py) already covers the doctor bot delivery helpers and runtime status behavior.

The implementation work here is mostly about preserving and completing the doctor-facing notification/card contract, not inventing a new workflow.

### Story-Specific Technical Requirements

- Ready-case notification must be sent only for allowed doctor identities.
- Case card must remain a thin presentation over backend-derived data.
- The card must expose fixed, review-oriented ordering so Telegram output stays predictable and scannable.
- The card must clearly show AI boundary wording, safety outcome, uncertainty, and provenance references.
- If the case is not ready, delivery must return a typed rejection and not a misleading partial card.
- If runtime or retrieval/source data is degraded, the card must preserve explicit limitation markers rather than implying full grounding.

### Architecture Compliance

- `doctor_bot` is a separate runtime process and must remain a thin adapter over backend services.
- Telegram remains a presentation channel, not a business-logic host.
- `PostgreSQL` remains the source of truth for case state and auditability.
- `Qdrant` remains a backend retrieval dependency, not a bot concern.
- No silent fallback to local stale-only case artifacts is allowed for doctor review.
- Doctor-facing output must remain safety-gated before it is presented as reviewable material.

### File Structure Requirements

Likely files to update:

- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py)
- [`app/bots/doctor_bot.py`](/Users/maker/Work/medical-ai-agent/app/bots/doctor_bot.py)
- [`app/bots/messages.py`](/Users/maker/Work/medical-ai-agent/app/bots/messages.py)
- [`app/schemas/handoff.py`](/Users/maker/Work/medical-ai-agent/app/schemas/handoff.py) only if the delivery or card contract needs a typed extension
- [`app/services/case_service.py`](/Users/maker/Work/medical-ai-agent/app/services/case_service.py) only if readiness gating needs a small correction
- [`app/services/safety_service.py`](/Users/maker/Work/medical-ai-agent/app/services/safety_service.py) only if safety result propagation needs to be aligned

Likely test files:

- [`tests/services/test_handoff_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_handoff_service.py)
- [`tests/bots/test_doctor_bot.py`](/Users/maker/Work/medical-ai-agent/tests/bots/test_doctor_bot.py)
- [`tests/schemas/test_handoff_contract.py`](/Users/maker/Work/medical-ai-agent/tests/schemas/test_handoff_contract.py)
- [`tests/services/test_case_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_case_service.py) only if readiness transitions need regression coverage

Avoid touching patient intake behavior unless a shared handoff helper genuinely requires it.

### Testing Requirements

- Verify an allowed doctor receives the ready-case notification and the structured case card.
- Verify a blocked or not-ready case returns a typed rejection, not a card.
- Verify the card preserves AI boundary text, safety context, and uncertainty markers.
- Verify degraded or partially grounded cases remain visibly limited instead of being presented as fully grounded.
- Keep tests deterministic and isolated from live Telegram, database, Qdrant, OCR, and LLM providers.

### Latest Technical Information

- FastAPI release notes currently list `0.136.1` and `0.136.0` as the latest stable entries, so any route exposure around doctor handoff should continue using structured response models and explicit rejection shapes. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog currently lists `v2.12.5` and notes the upcoming `2.13` minor release, so typed delivery contracts and validators remain the right pattern for card and rejection models. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/)
- aiogram docs currently publish `3.27.0` and emphasize async dispatcher/router organization, so `doctor_bot` should stay thin and async. Source: [aiogram docs](https://docs.aiogram.dev/)

## Dev Notes

### What Must Be Preserved

- Preserve the existing allowlist authorization path in `authorize_capability()`.
- Preserve the current readiness gate that blocks cases before doctor review.
- Preserve safety validation before doctor-facing output.
- Preserve the thin adapter pattern in `doctor_bot`.
- Preserve the existing doctor-facing copy that explains AI is preparing material, not making the medical decision.

### What This Story Changes

- If ready-case notifications are too generic, make them concise but explicit about the review-ready state.
- If card ordering or section labels are inconsistent, normalize them into a stable review structure.
- If case card output can appear more grounded than the backend confidence actually supports, add or strengthen limitation markers.
- If a rejection path currently looks like a successful partial delivery, convert it to a typed rejection.

### Previous Story Intelligence

The previous story in this epic already established the runtime boundary:

- `doctor_bot` has its own runtime status, dispatcher, polling entrypoint, and allowlist-aware startup behavior.
- The current risk is not missing access control primitives; it is leaking weakly grounded or not-ready content into the doctor-facing handoff surface.
- This story should build on the already existing doctor runtime rather than reworking the boundary again.

### Implementation Constraints

- Do not create a new access model.
- Do not add audit explorer UI in this story.
- Do not add a new doctor review workflow.
- Do not bypass readiness or safety checks to force a card delivery.
- Do not hide degraded grounding behind a success-style card.

## Project Context Reference

Use the planning artifacts as the source of truth:

- [`epics.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [`prd.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [`architecture.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [`ux-design-specification.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py)
- [`app/bots/doctor_bot.py`](/Users/maker/Work/medical-ai-agent/app/bots/doctor_bot.py)
- [`app/bots/messages.py`](/Users/maker/Work/medical-ai-agent/app/bots/messages.py)
- [`app/schemas/handoff.py`](/Users/maker/Work/medical-ai-agent/app/schemas/handoff.py)
- [`app/services/case_service.py`](/Users/maker/Work/medical-ai-agent/app/services/case_service.py)
- [`app/services/safety_service.py`](/Users/maker/Work/medical-ai-agent/app/services/safety_service.py)
- [`tests/services/test_handoff_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_handoff_service.py)
- [`tests/bots/test_doctor_bot.py`](/Users/maker/Work/medical-ai-agent/tests/bots/test_doctor_bot.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Epic 5 is still `in-progress`.
- Story 5.1 already locked down the doctor runtime boundary and allowlist contract.
- The key risk for 5.2 is presenting a case as ready without preserving the explicit uncertainty, provenance, and safety boundary that the backend already tracks.

### Completion Notes

- Implemented and verified doctor-facing ready-case notification and structured case card delivery behavior through existing handoff/runtime code paths.
- Confirmed allowlist gating, not-ready rejection, safety-blocked rejection, degraded presentation markers, and thin async bot delivery adapters with targeted tests.
- Validation run: `uv run pytest tests/services/test_handoff_service.py tests/bots/test_doctor_bot.py tests/schemas/test_handoff_contract.py tests/test_runtime_topology.py` (32 passed).

## File List

- `_bmad-output/implementation-artifacts/5-2-ready-for-doctor-notification-and-case-card.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Status

review

## Change Log

- 2026-05-07: Created the story context for ready-for-doctor notification and case card.
- 2026-05-07: Validated the doctor notification and case card handoff implementation and moved the story to review.
