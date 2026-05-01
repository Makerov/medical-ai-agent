from __future__ import annotations

from app.schemas.rag import DoctorFacingSummaryDraft
from app.schemas.safety import SafetyCheckResult, SafetyIssue


class SafetyService:
    _DIAGNOSIS_PATTERNS = (
        "diagnosis",
        "diagnosed",
        "suggests diagnosis",
        "likely diagnosis",
        "final diagnosis",
    )
    _TREATMENT_PATTERNS = (
        "treatment recommendation",
        "start treatment",
        "prescribe",
        "treatment plan",
        "should take",
        "recommend treatment",
    )
    _CERTAINTY_PATTERNS = (
        "certainly",
        "definitely",
        "absolutely",
        "guaranteed",
        "confirmed diagnosis",
    )
    _BORDERLINE_PATTERNS = (
        "might",
        "may",
        "borderline",
        "possibly",
        "unclear",
        "uncertain",
        "low-confidence",
    )

    def validate_doctor_facing_summary(
        self,
        *,
        case_id: str,
        draft: DoctorFacingSummaryDraft,
    ) -> SafetyCheckResult:
        text = self._compose_validation_text(draft)
        issues = self._detect_issues(text)
        if not issues:
            return SafetyCheckResult(
                case_id=case_id,
                decision="pass",
                issues=(),
                decision_rationale="Summary draft contains no blocked safety language.",
            )

        if any(issue.severity == "high" for issue in issues):
            return SafetyCheckResult(
                case_id=case_id,
                decision="blocked",
                issues=tuple(issues),
                decision_rationale="Unsafe clinical language requires blocking before handoff.",
                correction_path="manual_review_required",
            )

        return SafetyCheckResult(
            case_id=case_id,
            decision="corrected",
            issues=tuple(issues),
            decision_rationale="Borderline phrasing should be corrected before handoff.",
            correction_path="recoverable_correction",
        )

    def _compose_validation_text(self, draft: DoctorFacingSummaryDraft) -> str:
        parts = [draft.narrative]
        parts.extend(question.text for question in draft.questions_for_doctor)
        parts.extend(marker.text for marker in draft.uncertainty_markers)
        parts.extend(marker.text for marker in draft.possible_deviations)
        parts.extend(claim.text for claim in draft.grounded_summary.claims)
        return " ".join(parts).lower()

    def _detect_issues(self, text: str) -> list[SafetyIssue]:
        issues: list[SafetyIssue] = []
        if self._contains_any(text, self._DIAGNOSIS_PATTERNS):
            issues.append(
                SafetyIssue(
                    category="diagnosis_language",
                    severity="high",
                    message="Diagnosis language is not allowed in the doctor-facing summary draft.",
                    evidence=self._matched_fragment(text, self._DIAGNOSIS_PATTERNS),
                )
            )
        if self._contains_any(text, self._TREATMENT_PATTERNS):
            issues.append(
                SafetyIssue(
                    category="treatment_recommendation_language",
                    severity="high",
                    message=(
                        "Treatment recommendation language is not allowed in the doctor-facing "
                        "summary draft."
                    ),
                    evidence=self._matched_fragment(text, self._TREATMENT_PATTERNS),
                )
            )
        if self._contains_any(text, self._CERTAINTY_PATTERNS):
            issues.append(
                SafetyIssue(
                    category="unsupported_clinical_certainty",
                    severity="high",
                    message="Unsupported certainty language must be blocked.",
                    evidence=self._matched_fragment(text, self._CERTAINTY_PATTERNS),
                )
            )
        if self._contains_any(text, self._BORDERLINE_PATTERNS):
            issues.append(
                SafetyIssue(
                    category="borderline_phrasing",
                    severity="medium",
                    message="Borderline phrasing should be corrected before handoff.",
                    evidence=self._matched_fragment(text, self._BORDERLINE_PATTERNS),
                )
            )
        return issues

    @staticmethod
    def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
        return any(pattern in text for pattern in patterns)

    @staticmethod
    def _matched_fragment(text: str, patterns: tuple[str, ...]) -> str | None:
        for pattern in patterns:
            if pattern in text:
                return pattern
        return None
