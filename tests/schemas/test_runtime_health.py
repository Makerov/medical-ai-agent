from app.schemas.runtime_health import (
    RuntimeProcess,
    StartupVerificationResponse,
    StartupVerificationStatus,
    StartupVerificationStep,
    StartupVerificationStepStatus,
)


def test_startup_verification_response_serializes_structured_status() -> None:
    response = StartupVerificationResponse(
        process=RuntimeProcess.API,
        status=StartupVerificationStatus.DEGRADED,
        runtime_profile="local",
        can_process_cases=True,
        steps=(
            StartupVerificationStep(
                name="runtime_profile",
                required=False,
                status=StartupVerificationStepStatus.DEGRADED,
                reason_code="runtime_profile_local",
                detail="Runtime profile is not operational.",
            ),
            StartupVerificationStep(
                name="schema_compatibility",
                required=True,
                status=StartupVerificationStepStatus.READY,
            ),
        ),
        reason_codes=("runtime_profile_local",),
    )

    payload = response.model_dump(mode="json")

    assert payload["process"] == RuntimeProcess.API.value
    assert payload["status"] == StartupVerificationStatus.DEGRADED.value
    assert payload["can_process_cases"] is True
    assert payload["steps"][0]["name"] == "runtime_profile"
    assert payload["steps"][0]["status"] == StartupVerificationStepStatus.DEGRADED.value
    assert payload["reason_codes"] == ["runtime_profile_local"]
