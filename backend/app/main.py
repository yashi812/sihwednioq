from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
import re

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .analysis import evaluate_day, month_summary
from .elexon import ElexonError, fetch_actuals, fetch_forecast

app = FastAPI(title="WindDesk API", version="1.0.0", description="Elexon-only GB wind forecast replay and accuracy analysis for January 2026.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = PROJECT_ROOT / "frontend" / "dist"


def _validate_cutoff(cutoff: str) -> str:
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", cutoff):
        raise HTTPException(status_code=422, detail="Cutoff must be a 24-hour HH:MM time.")
    return cutoff


def _validate_january_day(day: date) -> date:
    if day.year != 2026 or day.month != 1:
        raise HTTPException(status_code=422, detail="This pilot is scoped to January 2026 delivery days.")
    return day


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "winddesk"}


@app.get("/api/health")
def api_health() -> dict[str, str]:
    return health()


@app.get("/api/dashboard")
def dashboard(cutoff: str = Query(default="11:00")) -> dict:
    cutoff = _validate_cutoff(cutoff)
    try:
        actuals = fetch_actuals()
    except ElexonError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    requested_days = [date(2026, 1, day) for day in range(1, 32)]
    forecasts: dict[date, tuple[list[dict], str]] = {}
    errors: dict[date, str] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_forecast, day, cutoff): day for day in requested_days}
        for future in as_completed(futures):
            day = futures[future]
            try:
                forecasts[day] = future.result()
            except (ElexonError, ValueError) as exc:
                errors[day] = str(exc)

    days = []
    for day in requested_days:
        rows, publish_time = forecasts.get(day, ([], ""))
        days.append(evaluate_day(day, cutoff, rows, publish_time, actuals, errors.get(day)))

    summary = month_summary(days)
    return {
        "month": "2026-01",
        "timezone": "Europe/London",
        "cutoff": cutoff,
        "forecastSource": "Elexon WINDFOR historical wind generation forecast",
        "actualSource": "Elexon FUELHH, fuelType=WIND",
        "unit": "MW",
        "errorDefinition": "forecast minus actual; positive bias means over-forecast",
        "actualAggregation": "Hourly actual is the arithmetic mean of the two matching 30-minute FUELHH average-MW values.",
        "summary": summary,
        "days": days,
        "fetchedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@app.get("/api/day")
def day_detail(
    delivery_date: date = Query(alias="date"),
    cutoff: str = Query(default="11:00"),
) -> dict:
    delivery_date = _validate_january_day(delivery_date)
    cutoff = _validate_cutoff(cutoff)
    try:
        actuals = fetch_actuals()
        forecast_rows, publish_time = fetch_forecast(delivery_date, cutoff)
    except (ElexonError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return evaluate_day(delivery_date, cutoff, forecast_rows, publish_time, actuals)


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
