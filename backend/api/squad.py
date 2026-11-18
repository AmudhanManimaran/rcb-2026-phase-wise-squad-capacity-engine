from fastapi import APIRouter, Query

from backend.services import squad_service

router = APIRouter(prefix="/api/squad", tags=["squad"])


@router.get("")
def squad(as_of_match_id: int | None = Query(None, ge=1, description="Profiles as of this match (pre-match)")):
    return squad_service.list_squad(as_of_match_id)


@router.get("/{player_id}")
def player(player_id: int):
    return squad_service.player_detail(player_id)
