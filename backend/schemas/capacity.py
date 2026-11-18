from pydantic import BaseModel, Field


class CapacityRequest(BaseModel):
    xi_player_ids: list[int] | None = Field(None, description="Optional custom XI in batting order (11 player ids)")
