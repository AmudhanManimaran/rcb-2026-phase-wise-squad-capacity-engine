from fastapi import APIRouter

from backend import __version__
from backend.database import fetch_one, ping

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health():
    ok = ping()
    counts = None
    if ok:
        counts = fetch_one("""SELECT (SELECT COUNT(*) FROM rcb_players) AS players,
                                     (SELECT COUNT(*) FROM rcb_matches) AS matches,
                                     (SELECT COUNT(*) FROM rcb_ball_by_ball) AS deliveries,
                                     (SELECT COUNT(*) FROM rcb_backtest_runs) AS backtest_runs""")
    return {"status": "ok" if ok else "degraded", "database": "connected" if ok else "unreachable",
            "version": __version__, "counts": counts}
