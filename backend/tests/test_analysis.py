from datetime import date

from app.analysis import evaluate_day, month_summary
from app.elexon import actual_hourly_map


def test_actuals_average_two_half_hour_periods_to_hourly_mw():
    rows = [
        {"startTime": "2026-01-15T00:00:00Z", "generation": 100},
        {"startTime": "2026-01-15T00:30:00Z", "generation": 140},
    ]
    actuals = actual_hourly_map(rows)
    assert actuals["2026-01-15T00:00:00Z"]["actual"] == 120
    assert actuals["2026-01-15T00:00:00Z"]["actualIntervals"] == 2


def test_incomplete_actual_hour_is_not_imputed():
    rows = [{"startTime": "2026-01-15T00:00:00Z", "generation": 100}]
    actuals = actual_hourly_map(rows)
    assert actuals["2026-01-15T00:00:00Z"]["actual"] is None


def test_error_metrics_use_forecast_minus_actual():
    forecasts = [
        {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T10:00:00Z", "generation": 150},
        {"startTime": "2026-01-15T01:00:00Z", "publishTime": "2026-01-14T10:00:00Z", "generation": 100},
    ]
    actuals = [
        {"startTime": "2026-01-15T00:00:00Z", "generation": 100},
        {"startTime": "2026-01-15T00:30:00Z", "generation": 100},
        {"startTime": "2026-01-15T01:00:00Z", "generation": 100},
        {"startTime": "2026-01-15T01:30:00Z", "generation": 100},
    ]
    result = evaluate_day(date(2026, 1, 15), "11:00", forecasts, "2026-01-14T10:00:00Z", actuals)
    assert result["mae"] == 25
    assert result["rmse"] == 35.35533905932738
    assert result["bias"] == 25
    assert result["scoredPoints"] == 2


def test_month_coverage_counts_only_exact_scored_hours():
    daily = {
        "forecastPoints": 2,
        "missingActuals": 1,
        "forecastError": None,
        "points": [
            {"forecast": 100, "actual": 100},
            {"forecast": 200, "actual": None},
        ],
    }
    summary = month_summary([daily])
    assert summary["scoredPoints"] == 1
    assert summary["forecastPoints"] == 2
    assert summary["coveragePct"] == 50
