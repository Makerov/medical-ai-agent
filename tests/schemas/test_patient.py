import pytest
from pydantic import ValidationError

from app.schemas.patient import ConsultationGoal, PatientIntakePayload, PatientProfile


def test_patient_profile_requires_non_empty_name_and_sane_age() -> None:
    profile = PatientProfile(full_name="Иван Петров", age=34)

    assert profile.full_name == "Иван Петров"
    assert profile.age == 34


def test_patient_profile_rejects_blank_name_and_out_of_range_age() -> None:
    with pytest.raises(ValidationError, match="must be non-empty"):
        PatientProfile(full_name=" ", age=34)

    with pytest.raises(ValidationError, match="less than or equal to 120"):
        PatientProfile(full_name="Иван Петров", age=121)


def test_consultation_goal_rejects_blank_and_too_short_text() -> None:
    with pytest.raises(ValidationError, match="at least 8 characters"):
        ConsultationGoal(text="  ")

    with pytest.raises(ValidationError, match="at least 8 characters"):
        ConsultationGoal(text="checkup")


def test_patient_intake_payload_keeps_case_scoped_profile_and_goal() -> None:
    payload = PatientIntakePayload(
        case_id="case_patient_001",
        patient_profile=PatientProfile(full_name="Иван Петров", age=34),
        consultation_goal=ConsultationGoal(text="Нужен check-up по давлению"),
    )

    assert payload.case_id == "case_patient_001"
    assert payload.patient_profile is not None
    assert payload.patient_profile.full_name == "Иван Петров"
    assert payload.consultation_goal is not None
    assert payload.consultation_goal.text == "Нужен check-up по давлению"
