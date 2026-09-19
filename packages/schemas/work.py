from typing import Literal
from datetime import date, datetime
from pydantic import BaseModel


class Authorship(BaseModel):
    researcher_id: str
    display_name: str
    position: Literal["first", "middle", "last"]
    is_corresponding: bool = False
    institution_id: str | None
class Work(BaseModel):
    id: str
    doi: str | None
    title: str
    abstract: str | None
    publication_year: int
    publication_date: date | None
    venue: str | None
    type: str | None
    authorships: list[Authorship]
    topics: list[str] = []
    cited_by_count: int
    is_open_access: bool
    open_access_url: str | None
    source: Literal["openalex", "semantic_scholar", "arxiv"]
    ingested_at: datetime