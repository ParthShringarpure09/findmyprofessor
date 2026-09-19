from typing import Literal

from pydantic import BaseModel
from datetime import datetime

class Claim(BaseModel):
    text: str
    subject: Literal["applicant", "researcher", "general"]
    evidence_ids: list[str] = []
    support: Literal["supported", "weak", "unsupported"]

class GroundingReport(BaseModel):
    unsupported_applicant_claims: list[str]
    unsupported_researcher_claims: list[str]
    generic_motivation_flags: list[str]
    mismatch_flags: list[str]
    passed: bool

class SOPDraft(BaseModel):
    id: str
    applicant_id: str
    researcher_id: str
    position_id: str | None
    sections: dict[str, str]
    claims: list[Claim]
    grounding: GroundingReport
    version: int
    created_at: datetime