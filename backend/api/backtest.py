from fastapi import APIRouter, Depends

from backend.dependencies import valid_match_id
from backend.services import analytics_service

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.post("/run")
def run():
    return analytics_service.run_backtest()


@router.post("/calibrate")
def calibrate():
    return analytics_service.run_calibration()


@router.get("/parameters")
def parameters():
    return analytics_service.list_parameters()


@router.post("/parameters/{param_id}/activate")
def activate(param_id: int):
    return analytics_service.activate_parameters(param_id)


@router.get("/results")
def results():
    return analytics_service.backtest_results()


@router.get("/{match_id}")
def match(match_id: int = Depends(valid_match_id)):
    return analytics_service.backtest_match(match_id)
