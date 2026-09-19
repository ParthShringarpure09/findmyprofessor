from typing import Literal

from pydantic import BaseModel


class EvidenceItem(BaseModel):
    id: str
    applicant_id: str
    text: str
    type: Literal[
        "skill",
        "project",
        "result",
        "education",
        "publication",
        "experience",
    ]
    source_document_id: str
    page: int | None
    section: str | None
    confidence: float
    verified_by_user: bool = False
    document_version: str