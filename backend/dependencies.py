"""Shared FastAPI dependencies."""
from fastapi import HTTPException, Path

from backend.services.common import season_data


def valid_match_id(match_id: int = Path(..., ge=1)) -> int:
    data = season_data()
    if match_id not in set(data.matches["match_id"].astype(int)):
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    return match_id
