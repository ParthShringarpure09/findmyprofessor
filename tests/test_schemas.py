from packages.schemas.researcher import (
    Institution,
    Researcher,
    SeniorityEstimate,
    TopicScore,
)
import pytest
from pydantic import ValidationError
from datetime import datetime


def test_institution_accepts_valid_data():
    institution = Institution(
        id="I123",
        display_name="University of Edinburgh",
        country_code="GB",
        ror=None,
        type="education",
    )

    assert institution.id == "I123"
    assert institution.display_name == "University of Edinburgh"
    assert institution.country_code == "GB"

    ## There are test cases for Institution schema. For Exmaple institution id should be I123 not I765. 

def test_institution_rejects_invalid_type():
    with pytest.raises(ValidationError):
            Institution(
                id="I123",
                display_name="University of Edinburgh",
                country_code="GB",
                ror=None,
                type=123,
            )
def test_institution_round_trip():
    original = Institution(
            id="I123",
            display_name="University of Edinburgh",
            country_code="GB",
            ror=None,
            type="education",
        )

    dumped = original.model_dump()
    restored = Institution.model_validate(dumped)

    assert restored == original
    

def test_institution_json_round_trip():
    original = Institution(
        id="I123",
        display_name="University of Edinburgh",
        country_code="GB",
        ror=None,
        type="education",
    )

    json_data = original.model_dump_json()
    restored = Institution.model_validate_json(json_data)

    assert restored == original

def test_topic_score_accepts_valid_data():
    topic = TopicScore(
        name="Medical Imaging",
        score=0.45,
        source="openalex",
    )

    assert topic.name == "Medical Imaging"
    assert topic.score == 0.45
    assert topic.source == "openalex"


def test_topic_score_rejects_invalid_source():
    with pytest.raises(ValidationError):
        TopicScore(
            name="Medical Imaging",
            score=0.45,
            source="google",
        )
def test_topic_score_json_round_trip():
    original = TopicScore(
        name="Medical Imaging",
        score=0.45,
        source="openalex",
    )

    json_data = original.model_dump_json()
    restored = TopicScore.model_validate_json(json_data)

    assert restored == original
def test_seniority_estimate_accepts_valid_data():
    seniority = SeniorityEstimate(
        tier="senior",
        confidence=0.82,
        signals=["career_span=14y"],
        verified_title=None,
    )

    assert seniority.tier == "senior"
    assert seniority.verified is False


def test_seniority_estimate_rejects_invalid_tier():
    with pytest.raises(ValidationError):
        SeniorityEstimate(
            tier="expert",
            confidence=0.82,
            signals=[],
            verified_title=None,
        )


def test_seniority_estimate_json_round_trip():
    original = SeniorityEstimate(
        tier="senior",
        confidence=0.82,
        signals=["career_span=14y"],
        verified_title=None,
    )

    json_data = original.model_dump_json()
    restored = SeniorityEstimate.model_validate_json(json_data)

    assert restored == original

def test_researcher_accepts_nested_models():
    researcher = Researcher(
        id="A123",
        display_name="Alice Smith",
        alternative_names=[],
        orcid=None,
        institution=Institution(
            id="I123",
            display_name="University of Edinburgh",
            country_code="GB",
            ror=None,
            type="education",
        ),
        past_institutions=[],
        primary_field="Computer Science",
        subfields=["Artificial Intelligence"],
        works_count=42,
        cited_by_count=1200,
        h_index=18,
        first_publication_year=2012,
        last_publication_year=2026,
        topics=[
            TopicScore(
                name="Medical Imaging",
                score=0.4,
                source="openalex",
            )
        ],
        profile_url=None,
        seniority=SeniorityEstimate(
            tier="senior",
            confidence=0.82,
            signals=["career_span=14y"],
            verified_title=None,
        ),
        ingested_at=datetime(2026, 9, 19),
        source_hash="abc123",
    )

    assert researcher.institution.display_name == "University of Edinburgh"
    assert researcher.topics[0].name == "Medical Imaging"
    assert researcher.seniority.tier == "senior"


def test_researcher_json_round_trip():
    researcher = Researcher(
        id="A123",
        display_name="Alice Smith",
        alternative_names=[],
        orcid=None,
        institution=None,
        past_institutions=[],
        primary_field="Computer Science",
        subfields=[],
        works_count=42,
        cited_by_count=1200,
        h_index=None,
        first_publication_year=2012,
        last_publication_year=2026,
        topics=[],
        profile_url=None,
        seniority=SeniorityEstimate(
            tier="unknown",
            confidence=0.0,
            signals=[],
            verified_title=None,
        ),
        ingested_at=datetime(2026, 9, 19),
        source_hash="abc123",
    )

    restored = Researcher.model_validate_json(researcher.model_dump_json())

    assert restored == researcher