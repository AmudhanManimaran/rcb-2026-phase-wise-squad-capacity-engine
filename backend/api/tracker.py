from fastapi import APIRouter, Depends, Query

from backend.dependencies import valid_match_id
from backend.schemas.tracker import TrackerUpdate
from backend.services import tracker_service

router = APIRouter(prefix="/api/tracker", tags=["tracker"])


@router.post("/update")
def update(body: TrackerUpdate):
    valid_match_id(body.match_id)
    return tracker_service.update_state(body.match_id, body.overs, body.runs, body.wickets, body.prediction_id)


@router.get("/{match_id}")
def state(match_id: int = Depends(valid_match_id)):
    return tracker_service.current_state(match_id)


@router.get("/{match_id}/recommendation")
def recommendation(match_id: int = Depends(valid_match_id)):
    return tracker_service.recommendation(match_id)


@router.get("/{match_id}/replay")
def replay(match_id: int = Depends(valid_match_id), prediction_id: int | None = Query(None)):
    return tracker_service.replay(match_id, prediction_id)


@router.delete("/{match_id}")
def reset(match_id: int = Depends(valid_match_id)):
    return {"deleted": tracker_service.reset(match_id)}
