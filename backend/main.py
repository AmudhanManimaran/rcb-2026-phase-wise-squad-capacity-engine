"""EeSaala Tracker API.

    uvicorn backend.main:app --reload
Swagger UI: http://127.0.0.1:8000/docs   Dashboard: http://127.0.0.1:8000/
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend import __version__
from backend.api import analytics, backtest, capacity, health, matches, squad, targets, tracker
from backend.config import settings

app = FastAPI(title="EeSaala Tracker API", version=__version__,
              description="RCB squad-specific phase-wise target intelligence system (IPL 2026, synthetic data).")

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS + ["null"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(LookupError)
async def not_found(_: Request, exc: LookupError):
    return JSONResponse(status_code=404, content={"detail": str(exc).strip("'")})


@app.exception_handler(ValueError)
async def bad_request(_: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


for r in (health, analytics, squad, matches, capacity, targets, tracker, backtest):
    app.include_router(r.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/app/index.html")


if settings.FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=settings.FRONTEND_DIR, html=True), name="frontend")
