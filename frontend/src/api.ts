export interface HourPoint {
  startTime: string;
  forecast: number;
  actual: number | null;
  error: number | null;
  actualIntervals: number;
}

export interface DayRecord {
  date: string;
  decisionDate: string;
  cutoff: string;
  publishTime: string | null;
  forecastPoints: number;
  scoredPoints: number;
  missingActuals: number;
  forecastError: string | null;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  points: HourPoint[];
}

export interface DashboardData {
  month: string;
  timezone: string;
  cutoff: string;
  forecastSource: string;
  actualSource: string;
  unit: string;
  errorDefinition: string;
  actualAggregation: string;
  summary: {
    mae: number | null;
    rmse: number | null;
    bias: number | null;
    scoredPoints: number;
    forecastPoints: number;
    missingActuals: number;
    coveragePct: number;
    daysWithForecast: number;
    daysWithDataIssue: number;
  };
  days: DayRecord[];
  fetchedAt: string;
}

export async function getDashboard(cutoff: string): Promise<DashboardData> {
  const response = await fetch(`/api/dashboard?cutoff=${encodeURIComponent(cutoff)}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload?.detail || `Request failed (${response.status})`);
  }
  return payload as DashboardData;
}

export function downloadCsv(data: DashboardData): void {
  const rows = [
    ['delivery_date', 'decision_date', 'cutoff_local', 'forecast_publish_time_utc', 'target_start_utc', 'forecast_mw', 'actual_mw', 'error_forecast_minus_actual_mw', 'actual_half_hours_matched'],
  ];
  for (const day of data.days) {
    for (const point of day.points) {
      rows.push([
        day.date,
        day.decisionDate,
        `${day.cutoff} Europe/London`,
        day.publishTime ?? '',
        point.startTime,
        String(point.forecast),
        point.actual === null ? '' : String(point.actual),
        point.error === null ? '' : String(point.error),
        String(point.actualIntervals),
      ]);
    }
  }
  const csv = rows.map((row) => row.map((value) => `"${value.replace(/"/g, '""')}"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'winddesk-january-2026-wind-review.csv';
  link.click();
  URL.revokeObjectURL(url);
}
