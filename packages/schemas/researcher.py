from pydantic import BaseModel
from typing import Literal



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
