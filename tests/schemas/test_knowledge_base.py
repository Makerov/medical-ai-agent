from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.knowledge_base import (
    KnowledgeApplicability,
    KnowledgeProvenance,
    KnowledgeSeedEntry,
    KnowledgeSourceMetadata,
)


def test_knowledge_seed_entry_validates_nested_metadata_and_normalizes_text() -> None:
    entry = KnowledgeSeedEntry(
        knowledge_id="medlineplus_hemoglobin_test",
        title=" Hemoglobin test interpretation ",
        summary=" Hemoglobin levels help assess anemia risk. ",
        content=" Hemoglobin reference ranges vary by laboratory and patient factors. ",
        source_metadata=KnowledgeSourceMetadata(
            source_id="medlineplus_hemoglobin_test",
            source_title=" Hemoglobin Test ",
            source_url="https://medlineplus.gov/lab-tests/hemoglobin-test/",
            publisher=" MedlinePlus / National Library of Medicine ",
            source_type="medical_test_reference",
            accessed_at=date(2026, 5, 1),
            citation_key="medlineplus-hemoglobin-test",
        ),
        provenance=KnowledgeProvenance(
            curation_method="Manual curation from MedlinePlus medical test guidance.",
            evidence_basis="Reference-range interpretation and anemia screening context.",
            source_reference="https://medlineplus.gov/lab-tests/hemoglobin-test/",
            curation_notes="Demo-grade grounding entry.",
        ),
        applicability=KnowledgeApplicability(
            intended_use="Ground extracted hemoglobin indicators.",
            applicable_contexts=(" adult CBC review ", "anemia screening", "adult CBC review"),
            excluded_contexts=("diagnosis", " treatment recommendation "),
            population_notes="Adult-oriented demo content.",
            limitations_summary="Reference range varies by laboratory and patient factors.",
        ),
        limitations=(
            " Lab-specific reference ranges still govern final interpretation. ",
            "This entry does not diagnose anemia by itself.",
        ),
        domain_tags=(" hematology ", "cbc", "hematology"),
    )

    assert entry.title == "Hemoglobin test interpretation"
    assert entry.summary == "Hemoglobin levels help assess anemia risk."
    assert entry.content == "Hemoglobin reference ranges vary by laboratory and patient factors."
    assert entry.domain_tags == ("hematology", "cbc")
    assert entry.applicability.applicable_contexts == ("adult CBC review", "anemia screening")
    assert entry.applicability.excluded_contexts == ("diagnosis", "treatment recommendation")
    assert entry.limitations == (
        "Lab-specific reference ranges still govern final interpretation.",
        "This entry does not diagnose anemia by itself.",
    )
    assert entry.source_identifier == "medlineplus_hemoglobin_test"

    payload = entry.to_qdrant_payload()

    assert payload["knowledge_id"] == "medlineplus_hemoglobin_test"
    assert payload["source_identifier"] == "medlineplus_hemoglobin_test"
    assert payload["search_text"].startswith("Hemoglobin test interpretation")
    assert payload["source_metadata"]["source_title"] == "Hemoglobin Test"
    assert payload["applicability"]["applicable_contexts"] == [
        "adult CBC review",
        "anemia screening",
    ]


def test_knowledge_seed_entry_rejects_mismatched_source_identifier() -> None:
    with pytest.raises(ValidationError, match="source identifier"):
        KnowledgeSeedEntry(
            knowledge_id="medlineplus_hemoglobin_test",
            title="Hemoglobin test interpretation",
            summary="Hemoglobin levels help assess anemia risk.",
            content="Hemoglobin reference ranges vary by laboratory and patient factors.",
            source_metadata=KnowledgeSourceMetadata(
                source_id="medlineplus_creatinine_test",
                source_title="Creatinine Test",
                source_url="https://medlineplus.gov/lab-tests/creatinine-test/",
                publisher="MedlinePlus / National Library of Medicine",
                source_type="medical_test_reference",
                accessed_at=date(2026, 5, 1),
                citation_key="medlineplus-creatinine-test",
            ),
            provenance=KnowledgeProvenance(
                curation_method="Manual curation from MedlinePlus medical test guidance.",
                evidence_basis="Reference-range interpretation and screening context.",
                source_reference="https://medlineplus.gov/lab-tests/creatinine-test/",
            ),
            applicability=KnowledgeApplicability(
                intended_use="Ground extracted indicators.",
                applicable_contexts=("kidney function review",),
                excluded_contexts=(),
                population_notes="Adult-oriented demo content.",
                limitations_summary="Lab-specific ranges still apply.",
            ),
            limitations=("Lab-specific reference ranges still govern final interpretation.",),
            domain_tags=("kidney",),
        )
