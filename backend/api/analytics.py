from fastapi import APIRouter

from backend.services import analytics_service

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/dashboard")
def dashboard():
    return analytics_service.dashboard()


@router.get("/analytics/phases")
def phases():
    return analytics_service.phase_analytics()


@router.get("/analytics/venues")
def venues():
    return analytics_service.venue_analytics()


@router.get("/analytics/players")
def players():
    return analytics_service.player_analytics()
