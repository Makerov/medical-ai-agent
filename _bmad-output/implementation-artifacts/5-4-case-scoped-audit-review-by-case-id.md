# Story 5.4: Case-Scoped Audit Review by `case_id`

Status: done

## Story

Как maintainer,
я хочу инспектировать audit и summary artifacts по `case_id`,
чтобы объяснить, как был получен doctor-facing output или почему case остановился в recoverable state.

## Acceptance Criteria

1. **Дано** известен `case_id`
   **Когда** запрашивается audit review
   **Тогда** система возвращает state transitions, provider outcomes, retrieval citations, retry/recovery events, summary artifacts и safety decisions для этого case
   **И** все records связаны достаточно coherently, чтобы объяснить, почему case готов или blocked.

2. **Дано** audit artifacts возвращены для operational review
   **Когда** они отображаются или экспортируются
   **Тогда** unnecessary sensitive payload minimized
   **И** выбранный runtime profile и degraded/fallback markers остаются visible.

3. **Дано** audit review запрашивается для unknown, deleted, not-ready, or access-denied case
   **Когда** backend cannot assemble a complete case-scoped audit view
   **Тогда** система возвращает structured rejection or explicit partial-view limitation
   **И** does not pretend that missing provenance or summary data is a successful complete review.

4. **Дано** audit review includes summary or recovery evidence
   **When** the case-scoped view is rendered
   **Then** the view preserves case-scoped provenance links, artifact references, and reason codes
   **And** it does not re-derive business conclusions from raw payloads on the presentation side.

## Story Foundation

Epic 5 owns doctor handoff and auditability. This story is the final maintainer-facing step in that epic: it turns the existing case-linked audit trail into a reviewable operational surface so support and engineering can explain a handoff outcome, degraded path, or stop-state using a single `case_id`.

### Business Value

- Reduces time to explain why a case was ready, blocked, or degraded.
- Gives maintainers a case-scoped view of transitions, provider behavior, and summary decisions.
- Preserves traceability without exposing unnecessary sensitive payload.
- Completes the operational auditability story for the doctor handoff flow.

### Story Scope

This story should add a case-scoped audit review surface only. It should not expand patient intake, not alter doctor-facing review UX, and not introduce a general-purpose admin dashboard.

## Developer Context

### What Already Exists

The repository already contains the core audit and trace primitives this story should assemble rather than recreate:

- [`app/services/audit_service.py`](/Users/maker/Work/medical-ai-agent/app/services/audit_service.py) already records case-linked audit events, builds case-scoped artifact paths, and stores summary traces in memory.
- [`app/schemas/audit.py`](/Users/maker/Work/medical-ai-agent/app/schemas/audit.py) already defines `AuditEvent`, `AuditEventType`, `ArtifactKind`, `CaseArtifactPath`, `SummaryAuditTrace`, `SummaryAuditTraceMetadata`, and related trace references.
- [`app/services/case_service.py`](/Users/maker/Work/medical-ai-agent/app/services/case_service.py) already exposes case core records, indicator/extraction records, and case status history surfaces that can be joined into a review view.
- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py) already records handoff readiness, ready notifications, and doctor-facing case card assembly.
- [`app/services/summary_service.py`](/Users/maker/Work/medical-ai-agent/app/services/summary_service.py) already produces grounded summary drafts that can feed a review trail.
- [`app/services/safety_service.py`](/Users/maker/Work/medical-ai-agent/app/services/safety_service.py) already emits the safety decision that must remain visible in audit review.
- [`app/api/v1/doctor.py`](/Users/maker/Work/medical-ai-agent/app/api/v1/doctor.py) already demonstrates a protected doctor-facing route pattern and typed forbidden responses.
- [`tests/services/test_audit_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_audit_service.py) and [`tests/schemas/test_audit_contract.py`](/Users/maker/Work/medical-ai-agent/tests/schemas/test_audit_contract.py) already cover core audit and trace contracts.
- [`tests/services/test_handoff_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_handoff_service.py) already exercises handoff readiness and doctor notification behavior that this audit surface should explain.

The main implementation risk is not missing data. The risk is exposing an over-broad or loosely structured admin view that leaks payloads or loses the explicit case-scoped chain of evidence.

### Story-Specific Technical Requirements

- Audit review must be case-scoped and keyed by `case_id`.
- The surface must include transitions, provider outcomes, retrieval citations, retry/recovery events, summary artifacts, and safety decisions when available.
- Missing pieces must be shown as explicit limitations rather than being fabricated or silently omitted.
- The view must minimize sensitive payload and prefer references, reason codes, and summaries over raw source dumps.
- Runtime profile, degraded markers, and fallback markers must be visible in the review surface.
- Presentation should remain thin over backend data and must not recompute provenance or safety conclusions in the route/bot layer.

### Architecture Compliance

- `api` remains the backend entrypoint for operational tooling.
- Telegram, if used for display, remains a thin presentation layer over backend review data.
- `PostgreSQL` remains the source of truth for persistent case state and audit metadata.
- `Qdrant` remains a backend retrieval dependency, not part of the review UI logic.
- No silent fallback to partial local artifacts is allowed when the backend cannot assemble a coherent case-scoped review.
- Case-scoped audit review must preserve explicit degraded/recoverable state instead of disguising it as a complete success.

### File Structure Requirements

Likely files to update:

- [`app/services/audit_service.py`](/Users/maker/Work/medical-ai-agent/app/services/audit_service.py)
- [`app/schemas/audit.py`](/Users/maker/Work/medical-ai-agent/app/schemas/audit.py)
- [`app/api/v1/doctor.py`](/Users/maker/Work/medical-ai-agent/app/api/v1/doctor.py) or a new case-audit API module under `app/api/v1/`
- [`app/bots/doctor_bot.py`](/Users/maker/Work/medical-ai-agent/app/bots/doctor_bot.py) only if the review surface is exposed through the doctor runtime
- [`app/bots/messages.py`](/Users/maker/Work/medical-ai-agent/app/bots/messages.py) only if maintainer-facing copy is needed

Likely test files:

- [`tests/services/test_audit_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_audit_service.py)
- [`tests/schemas/test_audit_contract.py`](/Users/maker/Work/medical-ai-agent/tests/schemas/test_audit_contract.py)
- [`tests/api/test_doctor_access.py`](/Users/maker/Work/medical-ai-agent/tests/api/test_doctor_access.py) if the route is exposed through the doctor API boundary
- [`tests/bots/test_doctor_bot.py`](/Users/maker/Work/medical-ai-agent/tests/bots/test_doctor_bot.py) if the review surface is rendered in Telegram

Avoid touching patient intake flow unless a shared audit helper genuinely requires it.

### Testing Requirements

- Verify a known `case_id` returns a coherent, case-scoped review bundle.
- Verify unknown, deleted, or inaccessible cases return a structured rejection or explicit limitation.
- Verify runtime profile and degraded/fallback markers are visible in the returned review view.
- Verify sensitive payload is minimized and raw business conclusions are not re-derived in presentation code.
- Keep tests deterministic and isolated from live Telegram, database, Qdrant, OCR, and LLM providers.

### Latest Technical Information

- FastAPI release notes currently list `0.136.1` and `0.136.0` as the latest stable entries, so any new review route should continue using explicit response models and structured error payloads. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog currently lists `v2.12.5` and notes the upcoming `2.13` minor release, so typed review DTOs and validators remain the correct pattern for this surface. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/)
- aiogram docs currently publish `3.27.0` and emphasize async router/dispatcher organization, so any Telegram rendering for audit review should stay thin and async. Source: [aiogram docs](https://docs.aiogram.dev/)

## Dev Notes

### What Must Be Preserved

- Preserve the existing case-linked audit event model and case-scoped artifact path helpers.
- Preserve the existing summary trace contract, including recovered state markers and presentation metadata.
- Preserve the current handoff pipeline and ready-for-doctor behavior.
- Preserve structured forbidden/rejection handling for inaccessible cases.
- Preserve payload minimization and case-scoped provenance links.

### What This Story Changes

- If audit data is only available through scattered services, gather it into a single case-scoped review response.
- If the review surface currently has no explicit limitation/rejection shape, add one.
- If runtime profile or degraded markers are missing from the review output, surface them.
- If summary or recovery evidence is buried in raw payloads, replace that with structured references and reason codes.

### Previous Story Intelligence

The previous story in this epic already established the doctor-facing review surface:

- Story 5.3 proved the handoff surface can separate facts, questions, sources, and uncertainty cleanly.
- The current risk is not doctor-facing presentation quality.
- The current risk is making audit review too loose, too payload-heavy, or too detached from the case-scoped evidence chain that already exists.

### Implementation Constraints

- Do not create a generic admin dashboard.
- Do not expose more sensitive payload than needed for operational explanation.
- Do not recalculate provenance or safety decisions in the presentation layer.
- Do not bypass access control if the review surface is exposed through a protected route.
- Do not silently collapse missing data into a success response.

## Project Context Reference

Use the planning artifacts as the source of truth:

- [`epics.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [`prd.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [`architecture.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [`ux-design-specification.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [`app/services/audit_service.py`](/Users/maker/Work/medical-ai-agent/app/services/audit_service.py)
- [`app/schemas/audit.py`](/Users/maker/Work/medical-ai-agent/app/schemas/audit.py)
- [`app/services/case_service.py`](/Users/maker/Work/medical-ai-agent/app/services/case_service.py)
- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py)
- [`app/services/summary_service.py`](/Users/maker/Work/medical-ai-agent/app/services/summary_service.py)
- [`app/services/safety_service.py`](/Users/maker/Work/medical-ai-agent/app/services/safety_service.py)
- [`tests/services/test_audit_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_audit_service.py)
- [`tests/schemas/test_audit_contract.py`](/Users/maker/Work/medical-ai-agent/tests/schemas/test_audit_contract.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Epic 5 is still `in-progress`.
- The repository already has case-scoped audit primitives and summary trace contracts.
- The story should focus on assembling a coherent `case_id` review surface, not on inventing new audit storage concepts.

### Completion Notes

- Implemented a case-scoped audit review bundle in `AuditService` that assembles transitions, provider outcomes, retrieval citations, retry/recovery events, summary artifacts, safety decisions, and explicit limitations by `case_id`.
- Added typed audit review DTOs to keep the review surface reference-driven and payload-minimized.
- Added schema and service tests covering complete, partial, and rejected review views.

### File List

- `app/api/v1/doctor.py`
- `app/schemas/__init__.py`
- `app/schemas/audit.py`
- `app/services/audit_service.py`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `tests/schemas/test_audit_contract.py`
- `tests/services/test_audit_service.py`

## Status

review

## Change Log

- 2026-05-07: Created the story context for case-scoped audit review by `case_id`.
- 2026-05-07: Implemented case-scoped audit review aggregation, typed review DTOs, and validation tests.
