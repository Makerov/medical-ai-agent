---
workflow: bmad-correct-course
project: medical-ai-agent
date: 2026-04-26
status: approved
trigger_stories:
  - Story 4.7
  - Story 1.3
recommended_approach: Direct Adjustment
scope_classification: Minor
---

# Sprint Change Proposal - Story Sequencing and Forward-Dependency Cleanup

## 1. Issue Summary

Во время review backlog обнаружен forward-dependency риск в Story 4.7 и premature implementation риск в Story 1.3.

Story 4.7 сейчас формулирует acceptance criteria так, будто к моменту ее выполнения уже существуют patient-facing, doctor-facing и demo/documentation outputs, включая новые doctor-facing templates. Это может заблокировать story на будущих Epic 5/6 artifacts или вынудить developer agent создавать templates раньше нужного.

Story 1.3 сейчас требует typed schemas для patient profile, consent, document metadata, extracted facts, summary metadata и audit trace. Это может преждевременно закрепить persistence models или AI output schemas для downstream областей, которые должны быть раскрыты позже в Epic 3 и Epic 4.

## 2. Impact Analysis

### Epic Impact

Epic 1 остается валидным. Требуется уточнить Story 1.3 так, чтобы она закрепляла case-linked references и отсутствие corrupted state, но не требовала полной реализации downstream persistence/schema.

Epic 4 остается валидным. Требуется уточнить Story 4.7 как guardrail story: она проверяет safety wording для уже существующих outputs/templates и задает acceptance constraint для будущих downstream stories.

Epic 5 и Epic 6 не требуют изменения структуры. Они должны наследовать safety boundary requirement, когда будут добавлять doctor-facing и demo outputs.

### Story Impact

Affected stories:

- Story 1.3: acceptance criteria need narrowed scope around references/placeholders instead of complete downstream schemas.
- Story 4.7: acceptance criteria need changed from all future output surfaces to implemented/current output surfaces, plus explicit downstream inheritance rule.

No new stories are required. No stories should be removed or resequenced.

### Artifact Conflicts

PRD does not need changes. The product goals, MVP scope, FR10, FR38 and FR39 remain intact.

Architecture does not require immediate changes. It already supports staged implementation, typed contracts and downstream validation. Optional future wording could clarify that early stories may use references/placeholders before downstream schemas are introduced.

Epics artifact requires direct updates in `epics.md`.

UX design artifact is not present.

### Technical Impact

The change reduces implementation risk:

- Story 1.3 can be completed without creating premature extraction, summary or audit persistence models.
- Story 4.7 can be completed without waiting for future doctor handoff or demo documentation templates.
- Future stories retain safety boundary obligations through explicit acceptance constraints.

## 3. Recommended Approach

Recommended path: Direct Adjustment.

Rationale: the issue is a backlog sequencing and acceptance-criteria precision problem, not a product pivot or architecture conflict. Direct story edits preserve MVP scope while reducing the chance that implementation agents overbuild early foundations or block on future outputs.

Effort estimate: Low.

Risk level: Low.

Timeline impact: None expected.

Alternatives considered:

- Rollback: not applicable, because this is a planning artifact correction rather than a completed implementation defect.
- MVP Review: not needed, because MVP goals remain achievable.

## 4. Detailed Change Proposals

### Story 1.3: Case-Linked Core Records

Section: Acceptance Criteria.

OLD:

```md
**Дано** существующий case
**Когда** связанные records прикрепляются к нему
**Тогда** каждый record связан с тем же `case_id`
**И** typed schemas определяют минимальные контракты для patient profile, consent, document metadata, extracted facts, summary metadata и audit trace.
```

NEW:

```md
**Дано** существующий case
**Когда** базовые records прикрепляются к нему
**Тогда** каждый доступный record связан с тем же `case_id`
**И** typed contracts определяют только минимальные references/placeholders для будущих document, extraction, summary и audit records, не создавая полноценные persistence models или AI output schemas раньше соответствующих epics.
```

OLD:

```md
**Дано** case запрашивается
**Когда** linked records существуют
**Тогда** система возвращает case aggregate или structured representation, показывающий присутствующие related records
**И** отсутствующие будущие records представлены явно, а не считаются corrupted state.
```

NEW:

```md
**Дано** case запрашивается
**Когда** часть downstream records еще не реализована
**Тогда** система возвращает case aggregate или structured representation с явно пустыми или pending references
**И** отсутствие будущих records не требует premature schema/persistence implementation и не считается corrupted state.
```

Justification: Story 1.3 should preserve traceability through `case_id` without forcing full downstream schemas or persistence models before Epic 3 and Epic 4.

### Story 4.7: Safety Boundary Consistency Across Outputs

Section: Acceptance Criteria.

OLD:

```md
**Дано** patient-facing, doctor-facing и demo/documentation copy используют safety messaging
**Когда** тексты проверяются
**Тогда** они согласованно говорят, что AI готовит информацию для врача, но не ставит диагноз и не назначает лечение
**И** human doctor review остается явным обязательным boundary.
```

NEW:

```md
**Дано** реализованные на текущий момент patient-facing, doctor-facing или demo/documentation outputs используют safety messaging
**Когда** тексты проверяются
**Тогда** доступные outputs согласованно говорят, что AI готовит информацию для врача, но не ставит диагноз и не назначает лечение
**И** human doctor review остается явным обязательным boundary.
```

OLD:

```md
**Дано** появляется новый doctor-facing output template
**Когда** он добавляется в систему
**Тогда** template содержит AI boundary labeling
**И** соответствующий test или checklist проверяет отсутствие autonomous medical decision language.
```

NEW:

```md
**Дано** появляется новый patient-facing, doctor-facing или demo output/template после этой story
**Когда** он добавляется в соответствующей downstream story
**Тогда** эта downstream story должна включить AI boundary labeling
**И** соответствующий test, fixture или checklist должен проверить отсутствие autonomous medical decision language.
```

ADD:

```md
**Scope note:** Story 4.7 проверяет и закрепляет safety wording для уже существующих outputs/templates. Она не должна блокироваться отсутствием будущих doctor handoff или demo documentation templates; будущие stories наследуют этот safety boundary как acceptance constraint.
```

Justification: Story 4.7 should be a safety guardrail story, not a hidden dependency on future doctor/demo outputs.

## 5. Implementation Handoff

Scope classification: Minor.

Route to: Developer agent.

Responsibilities:

- Update `epics.md` with the approved Story 1.3 and Story 4.7 acceptance criteria changes.
- Keep PRD unchanged.
- Keep Architecture unchanged unless a future review requests an explicit note about placeholder references in early stories.
- No implementation code changes are needed for this proposal.

Success criteria:

- Story 1.3 no longer requires premature downstream persistence models or AI output schemas.
- Story 4.7 can be implemented against currently available outputs/templates.
- Future patient-facing, doctor-facing and demo outputs still inherit explicit AI boundary labeling and anti-autonomous-medical-decision checks.

## 6. Checklist Completion

- [x] Trigger and context identified.
- [x] Epic impact assessed.
- [x] PRD, Architecture and UX artifact impact assessed.
- [x] Direct Adjustment selected as recommended path.
- [x] Detailed before/after edit proposals created.
- [x] User approved the two edit proposals.
- [x] Final approval received and artifact edits applied.

## 7. Handoff Log

Approval: Maker approved implementation on 2026-04-26.

Artifacts updated:

- `_bmad-output/planning-artifacts/epics.md`

Handoff route: Developer agent can proceed with updated Story 1.3 and Story 4.7 definitions.
