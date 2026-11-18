from pydantic import BaseModel


class PlayerSummary(BaseModel):
    player_id: int
    player_name: str
    short_name: str
    role: str
    is_overseas: bool
    is_captain: bool
    preferred_slot: int
