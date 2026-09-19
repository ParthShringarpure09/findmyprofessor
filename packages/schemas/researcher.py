from pydantic import BaseModel
from typing import Literal
from datetime import datetime



class Institution(BaseModel):
    id: str
    display_name: str
    country_code: str | None
    ror: str | None
    type: str | None

class TopicScore(BaseModel):
    name: str
    score: float
    source: Literal["openalex", "clustered"]

class SeniorityEstimate(BaseModel):
    tier: Literal["senior", "mid", "early", "unknown"]
    confidence: float
    signals: list[str]
    verified: bool = False
    verified_title: str | None
class Researcher(BaseModel):
    id: str
    display_name: str
    alternative_names: list[str] = []
    orcid: str | None
    institution: Institution | None
    past_institutions: list[Institution] = []
    primary_field: str | None
    subfields: list[str] = []
    works_count: int
    cited_by_count: int
    h_index: int | None
    first_publication_year: int | None
    last_publication_year: int | None
    topics: list[TopicScore] = []
    profile_url: str | None
    seniority: SeniorityEstimate
    ingested_at: datetime
    source_hash: str
