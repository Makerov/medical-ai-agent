from app.schemas.safety import SafetyCheckResult, SafetyIssue


def test_safety_check_result_serializes_typed_contract_boundaries() -> None:
    result = SafetyCheckResult(
        case_id="case_123",
        decision="corrected",
        issues=(
            SafetyIssue(
                category="borderline_phrasing",
                severity="medium",
                message="Borderline phrasing should be corrected before handoff.",
                evidence="might",
            ),
        ),
        decision_rationale="Borderline phrasing should be corrected before handoff.",
        correction_path="recoverable_correction",
    )

    dumped = result.model_dump(mode="json")

    assert dumped["case_id"] == "case_123"
    assert dumped["decision"] == "corrected"
    assert dumped["issues"][0]["category"] == "borderline_phrasing"
    assert dumped["issues"][0]["severity"] == "medium"
    assert dumped["correction_path"] == "recoverable_correction"

