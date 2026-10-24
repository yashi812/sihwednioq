from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from threading import Lock
from time import monotonic, sleep
from typing import Any, Callable
from zoneinfo import ZoneInfo

import requests

API_ROOT = "https://data.elexon.co.uk/bmrs/api/v1"
LONDON = ZoneInfo("Europe/London")
UTC = timezone.utc
CACHE_SECONDS = 15 * 60
_cache: dict[str, tuple[float, Any]] = {}
_cache_lock = Lock()


class ElexonError(RuntimeError):
    """Raised when the upstream Elexon response cannot be used."""


def _cached(key: str, loader: Callable[[], Any]) -> Any:
    now = monotonic()
    with _cache_lock:
        item = _cache.get(key)
        if item and now - item[0] < CACHE_SECONDS:
            return item[1]
    value = loader()
    with _cache_lock:
        _cache[key] = (monotonic(), value)
    return value


def _get_json(path: str, params: dict[str, str]) -> Any:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(
                f"{API_ROOT}{path}",
                params=params,
                headers={"Accept": "application/json", "User-Agent": "WindDesk-pilot/1.0"},
                timeout=(5, 25),
            )
            if response.status_code == 429 or response.status_code >= 500:
                response.raise_for_status()
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                sleep(0.4 * (attempt + 1))
    raise ElexonError(f"Elexon request failed: {last_error}") from last_error


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        rows = payload.get("data", [])
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _iso_utc(value: str | datetime) -> str:
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        parsed = value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def decision_cutoff(delivery_day: date, cutoff: str) -> datetime:
    try:
        hour, minute = (int(part) for part in cutoff.split(":"))
        local_time = time(hour=hour, minute=minute)
    except (ValueError, TypeError) as exc:
        raise ValueError("Cutoff must be a valid HH:MM time.") from exc
    local_dt = datetime.combine(delivery_day - timedelta(days=1), local_time, tzinfo=LONDON)
    return local_dt.astimezone(UTC)


def fetch_actuals() -> list[dict[str, Any]]:
    def load() -> list[dict[str, Any]]:
        payload = _get_json(
            "/datasets/FUELHH/stream",
            {
                "settlementDateFrom": "2026-01-01",
                "settlementDateTo": "2026-01-31",
                "fuelType": "WIND",
            },
        )
        values = _rows(payload)
        return [row for row in values if row.get("fuelType") == "WIND" and str(row.get("startTime", "")).startswith("2026-01-")]

    return _cached("actuals:2026-01:WIND", load)


def fetch_forecast(delivery_day: date, cutoff: str) -> tuple[list[dict[str, Any]], str]:
    cutoff_dt = decision_cutoff(delivery_day, cutoff)
    query_time = _iso_utc(cutoff_dt)
    key = f"forecast:{delivery_day.isoformat()}:{cutoff}"

    def load() -> tuple[list[dict[str, Any]], str]:
        payload = _get_json(
            "/forecast/generation/wind/history",
            {"publishTime": query_time, "format": "json"},
        )
        rows = _rows(payload)
        cutoff_utc = cutoff_dt
        filtered: list[dict[str, Any]] = []
        publish_times: list[datetime] = []
        for row in rows:
            start_time = row.get("startTime")
            publish_time = row.get("publishTime")
            if not start_time or not publish_time:
                continue
            try:
                start_dt = datetime.fromisoformat(str(start_time).replace("Z", "+00:00")).astimezone(UTC)
                publish_dt = datetime.fromisoformat(str(publish_time).replace("Z", "+00:00")).astimezone(UTC)
            except ValueError:
                continue
            if start_dt.date().isoformat() != delivery_day.isoformat() or publish_dt > cutoff_utc:
                continue
            if row.get("generation") is None:
                continue
            filtered.append({**row, "startTime": _iso_utc(str(start_time)), "publishTime": _iso_utc(str(publish_time))})
            publish_times.append(publish_dt)
        selected_publish = max(publish_times).isoformat().replace("+00:00", "Z") if publish_times else ""
        return filtered, selected_publish

    return _cached(key, load)


def actual_hourly_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    buckets: dict[datetime, list[float]] = {}
    for row in rows:
        try:
            start = datetime.fromisoformat(str(row["startTime"]).replace("Z", "+00:00")).astimezone(UTC)
            value = float(row["generation"])
        except (KeyError, TypeError, ValueError):
            continue
        hour_start = start.replace(minute=0, second=0, microsecond=0)
        buckets.setdefault(hour_start, []).append(value)

    result: dict[str, dict[str, Any]] = {}
    for hour_start, values in buckets.items():
        key = hour_start.isoformat().replace("+00:00", "Z")
        result[key] = {
            "actual": sum(values) / 2 if len(values) == 2 else None,
            "actualIntervals": min(len(values), 2),
        }
    return result
