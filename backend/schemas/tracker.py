from pydantic import BaseModel, Field


class TrackerUpdate(BaseModel):
    match_id: int = Field(..., ge=1)
    overs: str = Field(..., pattern=r"^\d{1,2}(\.[0-5])?$", examples=["12.3"])
    runs: int = Field(..., ge=0, le=400)
    wickets: int = Field(..., ge=0, le=10)
    prediction_id: int | None = None
