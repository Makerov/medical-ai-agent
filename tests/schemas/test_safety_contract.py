from app.schemas.safety import SafetyCheckExampleSet, SafetyCheckResult, SafetyIssue


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


def test_safety_check_example_set_preserves_case_linked_typed_results() -> None:
    pass_result = SafetyCheckResult(
        case_id="case_123",
        decision="pass",
        issues=(),
        decision_rationale="Summary draft contains no blocked safety language.",
    )
    result = SafetyCheckExampleSet(
        case_id="case_123",
        data_classification="synthetic_anonymized_demo",
        examples=(
            pass_result,
            SafetyCheckResult(
                case_id="case_123",
                decision="blocked",
                issues=(
                    SafetyIssue(
                        category="diagnosis_language",
                        severity="high",
                        message=(
                            "Diagnosis language is not allowed in the doctor-facing summary draft."
                        ),
                        evidence="diagnosis",
                    ),
                ),
                decision_rationale="Unsafe clinical language requires blocking before handoff.",
                correction_path="manual_review_required",
            ),
        ),
        example_note="Synthetic demo safety examples derived from the stable seed case.",
    )

    dumped = result.model_dump(mode="json")

    assert dumped["case_id"] == "case_123"
    assert dumped["data_classification"] == "synthetic_anonymized_demo"
    assert dumped["examples"][0]["decision"] == "pass"
    assert dumped["examples"][1]["decision"] == "blocked"
    assert dumped["examples"][1]["issues"][0]["category"] == "diagnosis_language"
