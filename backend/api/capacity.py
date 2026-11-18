"""Formula catalogue and parameter endpoints that support the capacity module."""
from fastapi import APIRouter

from backend.formulas import FORMULA_CATALOGUE, PHASE_BALLS, SLOT_BALL_TEMPLATE
from backend.services.common import active_params

router = APIRouter(prefix="/api/capacity", tags=["capacity"])


@router.get("/formulas")
def formulas():
    return [{"number": n, "name": name, "expression": expr} for n, name, expr in FORMULA_CATALOGUE]


@router.get("/config")
def config():
    return {"phase_balls": PHASE_BALLS, "slot_ball_template": SLOT_BALL_TEMPLATE, "active_params": active_params().as_dict()}
