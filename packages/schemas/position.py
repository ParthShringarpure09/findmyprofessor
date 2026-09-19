from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PositionEvidence(BaseModel):
    type: Literal[
        "university_listing",
        "lab_page",
        "vacancy_board",
        "euraxess",
        "profile_statement",
    ]
    url: str
    snippet: str
    fetched_at: datetime

from datetime import date


class PositionSignal(BaseModel):
    researcher_id: str
    tier: Literal["confirmed", "likely", "none"]
    evidence: list[PositionEvidence] = []
    deadline: date | None
    funding_note: str | None
    checked_at: datetime
    expires_at: datetime