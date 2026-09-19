from packages.schemas.researcher import Institution
import pytest
from pydantic import ValidationError


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