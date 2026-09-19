from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Citation(BaseModel):
    work_id: str | None
    title: str | None
    year: int | None
    url: str | None
    source_type: Literal[
        "paper",
        "profile",
        "position",
        "cv_evidence",
    ]
class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    citations: list[Citation] = []
    created_at: datetime
class ChatSession(BaseModel):
    id: str
    applicant_id: str
    researcher_id: str
    mode: Literal["explain", "fit", "interview"]
    created_at: datetime