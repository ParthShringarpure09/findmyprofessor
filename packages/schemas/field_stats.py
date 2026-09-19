from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class FieldStats(BaseModel):
    field_id: str
    field_name: str
    authorship_convention: Literal["contribution", "alphabetical", "mixed"]
    activity_threshold_years: int
    works_per_year_percentiles: dict[int, float]
    career_output_percentiles: dict[int, float]
    median_abstract_coverage: float
    computed_at: datetime
    sample_size: int