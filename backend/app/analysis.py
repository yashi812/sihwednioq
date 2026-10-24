from __future__ import annotations

from datetime import date, timedelta
from math import sqrt
from statistics import mean
from typing import Any

from .elexon import actual_hourly_map


def _metrics(points: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [point for point in points if point.get("actual") is not None and point.get("forecast") is not None]
    if not scored:
        return {"mae": None, "rmse": None, "bias": None, "scoredPoints": 0}
    errors = [float(point["forecast"]) - float(point["actual"]) for point in scored]
    return {
        "mae": mean(abs(error) for error in errors),
        "rmse": sqrt(mean(error * error for error in errors)),
        "bias": mean(errors),
        "scoredPoints": len(scored),
    }


def evaluate_day(
    delivery_day: date,
    cutoff: str,
    forecast_rows: list[dict[str, Any]],
    publish_time: str,
    actual_rows: list[dict[str, Any]],
    forecast_error: str | None = None,
) -> dict[str, Any]:
    actuals = actual_hourly_map(actual_rows)
    by_start: dict[str, dict[str, Any]] = {}
    for row in forecast_rows:
        try:
            start = str(row["startTime"])
            value = float(row["generation"])
        except (KeyError, TypeError, ValueError):
            continue
        if start not in by_start:
            by_start[start] = {"forecast": value, "publishTime": row.get("publishTime")}

    points: list[dict[str, Any]] = []
    for start in sorted(by_start):
        actual_info = actuals.get(start, {"actual": None, "actualIntervals": 0})
        forecast = by_start[start]["forecast"]
        actual = actual_info["actual"]
        points.append({
            "startTime": start,
            "forecast": forecast,
            "actual": actual,
            "error": forecast - actual if actual is not None else None,
            "actualIntervals": actual_info["actualIntervals"],
        })

    summary = _metrics(points)
    return {
        "date": delivery_day.isoformat(),
        "decisionDate": (delivery_day - timedelta(days=1)).isoformat(),
        "cutoff": cutoff,
        "publishTime": publish_time or None,
        "forecastPoints": len(points),
        "scoredPoints": summary["scoredPoints"],
        "missingActuals": sum(1 for point in points if point["actual"] is None),
        "forecastError": forecast_error,
        "mae": summary["mae"],
        "rmse": summary["rmse"],
        "bias": summary["bias"],
        "points": points,
    }


def month_summary(days: list[dict[str, Any]]) -> dict[str, Any]:
    points = [point for day in days for point in day["points"]]
    scored = _metrics(points)
    forecast_count = sum(day["forecastPoints"] for day in days)
    return {
        **scored,
        "forecastPoints": forecast_count,
        "missingActuals": sum(day["missingActuals"] for day in days),
        "coveragePct": (100 * scored["scoredPoints"] / forecast_count) if forecast_count else 0,
        "daysWithForecast": sum(1 for day in days if day["forecastPoints"]),
        "daysWithDataIssue": sum(1 for day in days if day["forecastError"]),
    }
