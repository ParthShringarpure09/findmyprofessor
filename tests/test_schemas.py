from packages.schemas.researcher import Institution
import pytest
from pydantic import ValidationError
from packages.schemas.researcher import Institution, TopicScore


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