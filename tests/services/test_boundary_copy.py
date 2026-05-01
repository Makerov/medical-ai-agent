from app.services.boundary_copy import (
    HUMAN_REVIEW_STATEMENT,
    SAFETY_BOUNDARY_SENTENCES,
    SAFETY_BOUNDARY_STATEMENT,
)


def test_canonical_safety_boundary_statements_cover_shared_surfaces() -> None:
    assert SAFETY_BOUNDARY_STATEMENT == (
        "ИИ подготавливает информацию для врача, но не ставит диагноз и не "
        "назначает лечение."
    )
    assert HUMAN_REVIEW_STATEMENT == (
        "Медицинское решение принимает врач после личной проверки материалов."
    )
    assert SAFETY_BOUNDARY_SENTENCES == (
        SAFETY_BOUNDARY_STATEMENT,
        HUMAN_REVIEW_STATEMENT,
    )


def test_canonical_safety_boundary_statements_do_not_imply_autonomous_clinical_action() -> None:
    combined = " ".join(SAFETY_BOUNDARY_SENTENCES).lower()
    for forbidden in (
        "автоном",
        "autonomous",
        "самостоятельно ставит диагноз",
        "сам назначает лечение",
    ):
        assert forbidden not in combined
