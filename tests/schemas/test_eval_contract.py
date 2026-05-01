from datetime import UTC, datetime

import pytest

from app.schemas.eval import EvalCheckResult, EvalSuiteSummary


def test_eval_check_result_requires_failure_reason_for_failures() -> None:
    with pytest.raises(ValueError, match="Failing eval checks must include a failure reason"):
        EvalCheckResult(
            category="extraction",
            fixture_id="fixture-a",
            case_id="case-1",
            outcome="fail",
            score=0.0,
            threshold_signal="missing_fields",
        )


def test_eval_suite_summary_links_all_results_to_same_case() -> None:
    summary = EvalSuiteSummary(
        case_id="case-1",
        generated_at=datetime(2026, 5, 1, 6, 0, tzinfo=UTC),
        data_classification="synthetic_anonymized_demo",
        results=(
            EvalCheckResult(
                category="safety",
                fixture_id="fixture-a",
                case_id="case-1",
                outcome="pass",
                score=1.0,
                threshold_signal="ok",
            ),
        ),
        artifact_path="case-1/demo/minimal-eval-suite.json",
    )

    assert summary.synthetic_by_default is True
    assert summary.case_id == "case-1"
