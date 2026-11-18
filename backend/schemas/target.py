from typing import Literal

from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    match_id: int = Field(..., ge=1)
    plan_mode: Literal["BAT_FIRST", "CHASE"] | None = Field(None, description="Defaults to the fixture's batting order")
    chase_target: float | None = Field(None, gt=0, le=400, description="Runs required when chasing")
    wicket_penalty: float | None = Field(None, ge=0, le=30, description="Overrides w in the checkpoint cost")
    xi_player_ids: list[int] | None = Field(None, description="Custom XI in batting order (11 player ids)")
