from pydantic import BaseModel


class Institution(BaseModel):
    id: str
    display_name: str
    country_code: str | None
    ror: str | None
    type: str | None