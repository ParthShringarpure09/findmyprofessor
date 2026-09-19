from packages.schemas.researcher import (
    Institution,
    Researcher,
    SeniorityEstimate,
    TopicScore,
)
import pytest
from pydantic import ValidationError
from datetime import datetime
from packages.schemas.work import *
from packages.schemas.field_stats import *
from packages.schemas.position import PositionEvidence, PositionSignal
from packages.schemas.evidence import EvidenceItem
from packages.schemas.chat import Citation, ChatMessage, ChatSession
from packages.schemas.sop import Claim, GroundingReport, SOPDraft

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

def test_authorship_accepts_valid_data():
    authorship = Authorship(
        researcher_id="A123",
        display_name="Alice Smith",
        position="first",
        institution_id="I123",
    )

    assert authorship.position == "first"
    assert authorship.is_corresponding is False

def test_authorship_rejects_invalid_position():
    with pytest.raises(ValidationError):
        Authorship(
            researcher_id="A123",
            display_name="Alice Smith",
            position="lead",
            institution_id="I123",
        )
def test_work_accepts_nested_authorship():
    work = Work(
        id="W123",
        doi=None,
        title="AI for Medical Imaging",
        abstract="A study of AI methods for medical imaging.",
        publication_year=2026,
        publication_date=None,
        venue="MICCAI",
        type="article",
        authorships=[
            Authorship(
                researcher_id="A123",
                display_name="Alice Smith",
                position="first",
                institution_id="I123",
            )
        ],
        topics=["Medical Imaging", "Artificial Intelligence"],
        cited_by_count=10,
        is_open_access=True,
        open_access_url=None,
        source="openalex",
        ingested_at=datetime(2026, 9, 19),
    )

    assert work.authorships[0].researcher_id == "A123"
    assert work.source == "openalex"

def test_work_json_round_trip():
    work = Work(
        id="W123",
        doi=None,
        title="AI for Medical Imaging",
        abstract=None,
        publication_year=2026,
        publication_date=None,
        venue=None,
        type=None,
        authorships=[],
        topics=[],
        cited_by_count=0,
        is_open_access=False,
        open_access_url=None,
        source="openalex",
        ingested_at=datetime(2026, 9, 19),
    )

    restored = Work.model_validate_json(work.model_dump_json())

    assert restored == work



def test_field_stats_json_round_trip():
    stats = FieldStats(
        field_id="computer_science",
        field_name="Computer Science",
        authorship_convention="contribution",
        activity_threshold_years=3,
        works_per_year_percentiles={10: 0.5, 50: 2.5, 90: 8.0},
        career_output_percentiles={10: 5.0, 50: 30.0, 90: 120.0},
        median_abstract_coverage=0.75,
        computed_at=datetime(2026, 9, 19),
        sample_size=5000,
    )

    restored = FieldStats.model_validate_json(stats.model_dump_json())

    assert restored == stats
def test_position_signal_json_round_trip():
    signal = PositionSignal(
        researcher_id="A123",
        tier="confirmed",
        evidence=[
            PositionEvidence(
                type="university_listing",
                url="https://example.edu/phd",
                snippet="Applications are open for a PhD position.",
                fetched_at=datetime(2026, 9, 19),
            )
        ],
        deadline=date(2027, 1, 12),
        funding_note="Fully funded",
        checked_at=datetime(2026, 9, 19),
        expires_at=datetime(2026, 9, 26),
    )

    restored = PositionSignal.model_validate_json(signal.model_dump_json())

    assert restored == signal

def test_evidence_item_json_round_trip():
    item = EvidenceItem(
        id="ev_123",
        applicant_id="app_123",
        text="Built a speech-based depression detection pipeline.",
        type="project",
        source_document_id="doc_123",
        page=2,
        section="Projects",
        confidence=0.94,
        document_version="v1",
    )

    restored = EvidenceItem.model_validate_json(item.model_dump_json())

    assert restored == item
    assert item.verified_by_user is False
def test_chat_schemas_json_round_trip():
    session = ChatSession(
        id="cs_123",
        applicant_id="app_123",
        researcher_id="A123",
        mode="fit",
        created_at=datetime(2026, 9, 19),
    )

    message = ChatMessage(
        id="msg_123",
        session_id=session.id,
        role="assistant",
        content="This researcher works on medical imaging.",
        citations=[
            Citation(
                work_id="W123",
                title="AI for Medical Imaging",
                year=2026,
                url="https://example.org/paper",
                source_type="paper",
            )
        ],
        created_at=datetime(2026, 9, 19),
    )

    restored = ChatMessage.model_validate_json(message.model_dump_json())

    assert restored == message
    assert session.mode == "fit"
def test_sop_draft_json_round_trip():
    draft = SOPDraft(
        id="sop_123",
        applicant_id="app_123",
        researcher_id="A123",
        position_id=None,
        sections={
            "opening": "Opening paragraph",
            "fit": "Fit paragraph",
        },
        claims=[
            Claim(
                text="Built a speech-based depression detection pipeline.",
                subject="applicant",
                evidence_ids=["ev_123"],
                support="supported",
            )
        ],
        grounding=GroundingReport(
            unsupported_applicant_claims=[],
            unsupported_researcher_claims=[],
            generic_motivation_flags=[],
            mismatch_flags=[],
            passed=True,
        ),
        version=1,
        created_at=datetime(2026, 9, 19),
    )

    restored = SOPDraft.model_validate_json(draft.model_dump_json())

    assert restored == draft