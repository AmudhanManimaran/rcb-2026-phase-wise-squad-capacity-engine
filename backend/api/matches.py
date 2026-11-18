from fastapi import APIRouter, Depends

from backend.dependencies import valid_match_id
from backend.schemas.capacity import CapacityRequest
from backend.services import capacity_service, match_service

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("")
def matches():
    return match_service.list_matches()


@router.get("/{match_id}")
def match(match_id: int = Depends(valid_match_id)):
    return match_service.match_detail(match_id)


@router.get("/{match_id}/capacity")
def capacity(match_id: int = Depends(valid_match_id)):
    return capacity_service.match_capacity(match_id)


@router.post("/{match_id}/capacity")
def capacity_custom(body: CapacityRequest, match_id: int = Depends(valid_match_id)):
    return capacity_service.match_capacity(match_id, body.xi_player_ids)
