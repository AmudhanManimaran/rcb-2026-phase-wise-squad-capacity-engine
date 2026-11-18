from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import valid_match_id
from backend.schemas.target import PlanRequest
from backend.services import target_service

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.post("/plan")
def plan(body: PlanRequest):
    valid_match_id(body.match_id)
    return target_service.generate_plan(body.match_id, body.plan_mode, body.chase_target, body.wicket_penalty,
                                        body.xi_player_ids)


@router.get("/{match_id}")
def saved(match_id: int = Depends(valid_match_id)):
    res = target_service.saved_prediction(match_id)
    if res is None:
        raise HTTPException(404, "No saved prediction for this match. POST /api/targets/plan first.")
    return res
