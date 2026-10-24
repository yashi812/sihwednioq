import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  CalendarDays,
  ChevronDown,
  CircleAlert,
  CloudSun,
  Download,
  ExternalLink,
  Info,
  LayoutDashboard,
  LoaderCircle,
  RefreshCw,
  Wind,
} from 'lucide-react';
import { DashboardData, DayRecord, downloadCsv, getDashboard, HourPoint } from './api';

const DEFAULT_DAY = '2026-01-15';
const nf = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 1, minimumFractionDigits: 1 });

function mw(value: number | null | undefined): string {
  return value === null || value === undefined ? '—' : nf.format(value);
}

function mw1(value: number | null | undefined): string {
  return value === null || value === undefined ? '—' : nf1.format(value);
}

function prettyDay(value: string, long = false): string {
  if (!value) return '—';
  return new Intl.DateTimeFormat('en-GB', {
    weekday: long ? 'short' : undefined,
    day: '2-digit',
    month: long ? 'long' : 'short',
    timeZone: 'UTC',
  }).format(new Date(`${value}T12:00:00Z`));
}

function prettyTime(value: string | null): string {
  if (!value) return 'No vintage found';
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZoneName: 'short',
    timeZone: 'Europe/London',
  }).format(new Date(value));
}

function TinyTrend({ bias }: { bias: number | null }) {
  if (bias === null) return <span className="trend neutral">No score</span>;
  const positive = bias >= 0;
  const Icon = positive ? ArrowUpRight : ArrowDownRight;
  return <span className={`trend ${positive ? 'positive' : 'negative'}`}><Icon size={14} /> {positive ? 'Over' : 'Under'} forecast</span>;
}

function MetricCard({ label, value, hint, tone = 'plain' }: { label: string; value: number | null; hint: string; tone?: 'plain' | 'teal' | 'lime' }) {
  return (
    <article className={`metric-card ${tone}`}>
      <div className="metric-head"><span>{label}</span><span className="metric-unit">MW</span></div>
      <div className="metric-value">{mw1(value)}</div>
      <div className="metric-hint">{hint}</div>
    </article>
  );
}

function EmptyChart() {
  return <div className="empty-chart"><Wind size={28} /><strong>No hourly forecast available</strong><span>There is no usable Elexon forecast vintage for this delivery day and cutoff.</span></div>;
}

function ForecastChart({ points }: { points: HourPoint[] }) {
  const width = 920;
  const height = 285;
  const left = 62;
  const right = 18;
  const top = 18;
  const bottom = 44;
  const chartW = width - left - right;
  const chartH = height - top - bottom;
  const finiteValues = points.flatMap((point) => [point.forecast, point.actual].filter((n): n is number => n !== null && Number.isFinite(n)));
  if (!points.length || !finiteValues.length) return <EmptyChart />;
  const max = Math.max(5000, Math.ceil(Math.max(...finiteValues) / 5000) * 5000);
  const x = (index: number) => left + (index / Math.max(1, points.length - 1)) * chartW;
  const y = (value: number) => top + chartH - (value / max) * chartH;
  const path = (field: 'forecast' | 'actual') => {
    let open = false;
    return points.map((point, index) => {
      const value = point[field];
      if (value === null) { open = false; return ''; }
      const command = open ? 'L' : 'M';
      open = true;
      return `${command}${x(index).toFixed(1)},${y(value).toFixed(1)}`;
    }).filter(Boolean).join(' ');
  };
  const ticks = [0, 1, 2, 3, 4];
  const timeIndices = [0, 4, 8, 12, 16, 20].filter((index) => index < points.length);
  return (
    <div className="chart-frame">
      <div className="chart-legend">
        <span><i className="legend-line forecast" /> WINDFOR forecast</span>
        <span><i className="legend-line actual" /> FUELHH actual</span>
        <span className="chart-resolution">Hourly · MW</span>
      </div>
      <svg className="forecast-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Hourly wind generation forecast and actual comparison">
        <defs>
          <linearGradient id="forecastFade" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#62c1b1" stopOpacity=".18" />
            <stop offset="100%" stopColor="#62c1b1" stopOpacity="0" />
          </linearGradient>
        </defs>
        {ticks.map((tick) => {
          const yy = top + (tick / 4) * chartH;
          const value = max - (tick / 4) * max;
          return <g key={tick}><line x1={left} x2={width - right} y1={yy} y2={yy} className="gridline" /><text x={left - 12} y={yy + 4} textAnchor="end" className="axis-label">{nf.format(value / 1000)}k</text></g>;
        })}
        {timeIndices.map((index) => <g key={index}><line x1={x(index)} x2={x(index)} y1={top} y2={height - bottom} className="gridline vertical" /><text x={x(index)} y={height - 16} textAnchor="middle" className="axis-label">{new Intl.DateTimeFormat('en-GB', { hour: '2-digit', timeZone: 'UTC' }).format(new Date(points[index].startTime))}</text></g>)}
        <path d={`${path('forecast')} L${x(points.length - 1)},${top + chartH} L${x(0)},${top + chartH} Z`} fill="url(#forecastFade)" />
        <path d={path('forecast')} className="line forecast-path" />
        <path d={path('actual')} className="line actual-path" />
        {points.map((point, index) => point.actual !== null ? <circle key={point.startTime} cx={x(index)} cy={y(point.actual)} r="3.2" className="actual-dot"><title>{`${new Date(point.startTime).toISOString().slice(11, 16)} UTC · Forecast ${mw(point.forecast)} MW · Actual ${mw(point.actual)} MW`}</title></circle> : null)}
      </svg>
      <div className="chart-footnote"><Info size={13} /> Half-hourly actuals are averaged to the hourly forecast interval. Missing actual pairs are left unscored.</div>
    </div>
  );
}

function DailyBars({ days, selectedDate, onSelect }: { days: DayRecord[]; selectedDate: string; onSelect: (value: string) => void }) {
  const scored = days.filter((day) => day.mae !== null);
  if (!scored.length) return <div className="mini-empty">Daily error scores appear when forecasts and actuals align.</div>;
  const max = Math.max(1, ...scored.map((day) => day.mae ?? 0));
  return (
    <div className="bars-scroll">
      <div className="daily-bars" role="list" aria-label="January daily mean absolute error in megawatts">
        {days.map((day) => {
          const value = day.mae ?? 0;
          const active = day.date === selectedDate;
          const height = day.mae === null ? 3 : Math.max(5, (value / max) * 76);
          return <button key={day.date} className={`bar-cell ${active ? 'active' : ''} ${day.mae === null ? 'no-score' : ''}`} onClick={() => onSelect(day.date)} title={`${prettyDay(day.date, true)} · MAE ${day.mae === null ? 'not scored' : `${mw1(value)} MW`}`} aria-label={`${prettyDay(day.date, true)}, MAE ${day.mae === null ? 'not scored' : `${mw1(value)} megawatts`}`}><span className="bar-value">{day.mae === null ? '' : nf.format(value)}</span><span className="bar-track"><i style={{ height: `${height}px` }} /></span><span className="bar-day">{day.date.slice(-2)}</span></button>;
        })}
      </div>
      <div className="bars-axis"><span>01 Jan</span><span>Daily MAE · MW</span><span>31 Jan</span></div>
    </div>
  );
}

function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [selectedDate, setSelectedDate] = useState(DEFAULT_DAY);
  const [cutoff, setCutoff] = useState('11:00');
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);
  const [activeSection, setActiveSection] = useState<'decision' | 'accuracy'>('decision');

  useEffect(() => {
    let active = true;
    setBusy(true);
    setError('');
    getDashboard(cutoff)
      .then((response) => { if (active) setData(response); })
      .catch((reason: unknown) => { if (active) setError(reason instanceof Error ? reason.message : 'Unable to load Elexon data.'); })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [cutoff, reload]);

  const day = useMemo(() => data?.days.find((item) => item.date === selectedDate) ?? null, [data, selectedDate]);
  const scoredMonth = data?.summary.scoredPoints ?? 0;
  const timeLabel = day?.publishTime ? prettyTime(day.publishTime) : 'No matching publish time';
  const localDecisionDate = day?.decisionDate ? prettyDay(day.decisionDate, true) : 'preceding day';
  const navigateTo = (id: string, section: 'decision' | 'accuracy') => {
    setActiveSection(section);
    const behavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
    document.getElementById(id)?.scrollIntoView({ behavior, block: 'start' });
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup"><div className="brand-mark"><Wind size={22} strokeWidth={2.1} /></div><div className="brand-name">wind<span>desk</span><small>FORECAST INTELLIGENCE</small></div></div>
        <div className="workspace-label">WORKSPACE</div>
        <button type="button" className={`nav-item ${activeSection === 'decision' ? 'active' : 'muted'}`} onClick={() => navigateTo('decision-review', 'decision')} aria-current={activeSection === 'decision' ? 'location' : undefined}><LayoutDashboard size={17} /><span>Decision review</span>{activeSection === 'decision' ? <i /> : null}</button>
        <button type="button" className={`nav-item ${activeSection === 'accuracy' ? 'active' : 'muted'}`} onClick={() => navigateTo('forecast-accuracy', 'accuracy')} aria-current={activeSection === 'accuracy' ? 'location' : undefined} title="View monthly accuracy scores and daily performance"><BarChart3 size={17} /><span>Forecast accuracy</span>{activeSection === 'accuracy' ? <i /> : null}</button>
        <div className="sidebar-divider" />
        <div className="workspace-label">DATA SOURCES</div>
        <div className="source-item"><span className="source-dot teal" /><span>WINDFOR</span><span className="source-state">FORECAST</span></div>
        <div className="source-item"><span className="source-dot cream" /><span>FUELHH · WIND</span><span className="source-state">ACTUAL</span></div>
        <div className="sidebar-spacer" />
        <div className="sidebar-scope"><span className="scope-glyph"><CloudSun size={16} /></span><div><strong>GB national wind</strong><small>Elexon-only pilot scope</small></div></div>
        <div className="sidebar-footer">WIND DESK <span>·</span> PILOT 01</div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb"><span>Portfolio operations</span><span className="crumb-slash">/</span><strong>Wind balance</strong></div>
          <div className="topbar-right"><span className="replay-pill"><span className="pulse-dot" /> HISTORICAL REPLAY <b>JAN ’26</b></span><span className="top-separator" /><span className="avatar">UK</span><span className="team-name">Trading desk</span></div>
        </header>

        <div className="page-content">
          <section className="page-heading" id="decision-review">
            <div>
              <div className="eyebrow"><span className="eyebrow-line" /> DAY-AHEAD WIND REVIEW <span className="eyebrow-dot">·</span> GB NATIONAL</div>
              <h1>Forecast readiness</h1>
              <p>See the wind vintage available at decision time — and how it measured against outturn.</p>
            </div>
            <div className="heading-actions">
              <label className="cutoff-control"><span>DECISION CUTOFF</span><div><input type="time" value={cutoff} onChange={(event) => setCutoff(event.target.value || '11:00')} aria-label="Decision cutoff in Europe London time" /><ChevronDown size={13} /></div><small>Europe / London · day before delivery</small></label>
              <button className="icon-button" onClick={() => setReload((value) => value + 1)} disabled={busy} aria-label="Refresh Elexon data" title="Refresh data"><RefreshCw size={17} className={busy ? 'spin' : ''} /></button>
            </div>
          </section>

          {error && <div className="error-banner" role="alert"><CircleAlert size={18} /><div><strong>Elexon data could not be loaded</strong><span>{error}</span></div><button onClick={() => setReload((value) => value + 1)}>Retry</button></div>}

          <section className="decision-strip">
            <div className="decision-copy"><span className="decision-icon"><Wind size={19} /></span><div><span className="decision-label">DELIVERY-DAY DECISION BRIEF</span><strong>{day ? prettyDay(day.date, true) : 'January 2026'}</strong></div></div>
            <div className="decision-meta"><span className="decision-meta-label">SELECTED FORECAST VINTAGE</span><strong>{busy && !day ? 'Loading vintage…' : timeLabel}</strong></div>
            <div className="decision-meta cutoff-meta"><span className="decision-meta-label">PURCHASE DECISION CUTOFF</span><strong>{localDecisionDate} · {cutoff} GMT</strong></div>
            <div className={`decision-status ${day?.publishTime ? 'ready' : ''}`}><span className="status-dot" />{day?.publishTime ? 'VINTAGE FOUND' : busy ? 'FETCHING' : 'NO VINTAGE'}</div>
          </section>

          <section className="metric-grid" id="forecast-accuracy" aria-label="January forecast accuracy metrics">
            <MetricCard label="MAE" value={data?.summary.mae ?? null} hint="Mean absolute forecast error · month" tone="teal" />
            <MetricCard label="RMSE" value={data?.summary.rmse ?? null} hint="Root mean squared error · month" />
            <article className="metric-card plain"><div className="metric-head"><span>MEAN BIAS</span><span className="metric-unit">MW</span></div><div className="metric-value">{mw1(data?.summary.bias)}</div><div className="metric-hint"><TinyTrend bias={data?.summary.bias ?? null} /></div></article>
            <article className="metric-card coverage-card"><div className="coverage-top"><div><div className="metric-head"><span>SCORING COVERAGE</span></div><div className="metric-value">{busy && !data ? '—' : `${nf.format(data?.summary.coveragePct ?? 0)}%`}</div></div><div className="coverage-icon"><Activity size={20} /></div></div><div className="coverage-track"><i style={{ width: `${Math.max(0, Math.min(100, data?.summary.coveragePct ?? 0))}%` }} /></div><div className="metric-hint">{nf.format(scoredMonth)} matched hourly intervals <span className="hint-dot">·</span> {nf.format(data?.summary.missingActuals ?? 0)} unmatched</div></article>
          </section>

          {data?.summary.daysWithDataIssue ? <div className="partial-note"><Info size={14} /> {data.summary.daysWithDataIssue} day(s) had an upstream forecast issue. They remain visible and are not silently imputed.</div> : null}

          <section className="analysis-grid">
            <article className="panel chart-panel">
              <div className="panel-heading"><div><div className="panel-kicker">DELIVERY PROFILE <span className="panel-period">· {day ? prettyDay(day.date, true).toUpperCase() : 'SELECT A DAY'}</span></div><h2>Forecast vs actual</h2></div><label className="day-select"><CalendarDays size={15} /><input type="date" min="2026-01-01" max="2026-01-31" value={selectedDate} onChange={(event) => event.target.value && setSelectedDate(event.target.value)} aria-label="Select a January 2026 delivery day" /><ChevronDown size={13} /></label></div>
                <div className="chart-stat-row"><span><b>{day?.scoredPoints ?? 0}</b> of {day?.forecastPoints ?? 0} forecast hours scored</span><span className="chart-stat-divider" /><span>Daily MAE <b>{mw1(day?.mae)} MW</b></span><span className="chart-stat-divider" /><span>Bias <b>{mw1(day?.bias)} MW</b></span></div>
                {busy && !data ? <div className="chart-loading"><LoaderCircle size={20} className="spin" /><span>Retrieving January vintages from Elexon…</span></div> : <ForecastChart points={day?.points ?? []} />}
                <div className="vintage-line"><span className="vintage-label">VINTAGE TRACE</span><span>{day?.publishTime ? `${timeLabel} · selected at/before ${cutoff} Europe/London on the preceding day` : 'No eligible vintage returned for this day and cutoff.'}</span><Info size={14} /></div>
            </article>

            <article className="panel vintage-panel">
              <div className="panel-heading"><div><div className="panel-kicker">SOURCE & METHOD</div><h2>Vintage record</h2></div><span className="vintage-seal"><Wind size={17} /></span></div>
              <div className="vintage-record"><span className="record-label">ELEXON PUBLISH TIME</span><strong>{day?.publishTime ? prettyTime(day.publishTime) : '—'}</strong><span className="record-sub">Actual timestamp returned by the historical WINDFOR endpoint</span></div>
              <div className="record-row"><span><i className="record-dot teal" /> Forecast</span><strong>WINDFOR</strong></div>
              <div className="record-row"><span><i className="record-dot cream" /> Actual outturn</span><strong>FUELHH · WIND</strong></div>
              <div className="record-row"><span>Target intervals</span><strong>{day?.forecastPoints ?? 0} hourly</strong></div>
              <div className="record-row"><span>Matched to actuals</span><strong>{day?.scoredPoints ?? 0} / {day?.forecastPoints ?? 0}</strong></div>
              <div className="method-note"><Info size={15} /><span>Hourly WINDFOR is compared with the mean of two matching half-hour FUELHH average-MW readings. No interpolation.</span></div>
              <a className="source-link" href="https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/history" target="_blank" rel="noreferrer">Elexon endpoint details <ExternalLink size={13} /></a>
            </article>
          </section>

          <section className="panel monthly-panel">
            <div className="panel-heading monthly-heading"><div><div className="panel-kicker">JANUARY 2026 <span className="panel-period">· DAILY PERFORMANCE</span></div><h2>Accuracy across the month</h2></div><div className="month-summary"><span>MONTHLY MATCHED SAMPLE</span><strong>{nf.format(scoredMonth)} <small>hourly observations</small></strong></div></div>
            {busy && !data ? <div className="chart-loading compact"><LoaderCircle size={18} className="spin" /> Building historical comparison…</div> : <DailyBars days={data?.days ?? []} selectedDate={selectedDate} onSelect={setSelectedDate} />}
            <div className="month-legend"><span className="legend-box" /> Daily MAE <span className="month-legend-note">Select a bar to inspect that delivery day</span></div>
          </section>

          <section className="panel table-panel">
            <div className="panel-heading table-heading"><div><div className="panel-kicker">VINTAGE REGISTER</div><h2>Daily decision record</h2></div><button className="export-button" onClick={() => data && downloadCsv(data)} disabled={!data}><Download size={15} /> Export CSV</button></div>
            <div className="table-scroll"><table><thead><tr><th>Delivery day</th><th>Forecast vintage</th><th>Hours matched</th><th>MAE · MW</th><th>RMSE · MW</th><th>Bias · MW</th><th>Status</th></tr></thead><tbody>
              {(data?.days ?? []).map((item) => (
                <tr key={item.date} className={item.date === selectedDate ? 'selected' : ''} onClick={() => setSelectedDate(item.date)}>
                  <td><button type="button" className="table-row-select" aria-pressed={item.date === selectedDate} aria-label={`Select ${prettyDay(item.date, true)} delivery day`}><span className="table-date">{prettyDay(item.date, true)}</span></button></td>
                  <td className="mono">{item.publishTime ? prettyTime(item.publishTime) : '—'}</td>
                  <td className="mono">{item.scoredPoints} / {item.forecastPoints}</td>
                  <td className="mono">{mw1(item.mae)}</td>
                  <td className="mono">{mw1(item.rmse)}</td>
                  <td className={`mono ${item.bias === null ? '' : item.bias > 0 ? 'bias-positive' : 'bias-negative'}`}>{mw1(item.bias)}</td>
                  <td><span className={`table-status ${item.forecastError ? 'issue' : item.publishTime ? 'complete' : 'empty'}`}><i />{item.forecastError ? 'API issue' : item.publishTime ? 'Vintage found' : 'No vintage'}</span></td>
                </tr>
              ))}
              {!data && busy ? <tr><td colSpan={7} className="table-loading"><LoaderCircle size={16} className="spin" /> Loading daily register from Elexon…</td></tr> : null}
            </tbody></table></div>
            <div className="table-footnote"><Info size={13} /> Bias is forecast minus actual. Positive means over-forecast; negative means under-forecast. Only complete hourly pairs are scored.</div>
          </section>

          <footer className="page-footer"><span><span className="footer-mark"><Wind size={13} /></span> WindDesk <span className="footer-separator">/</span> January 2026 historical replay</span><span>Source data: <a href="https://bmrs.elexon.co.uk/api-documentation" target="_blank" rel="noreferrer">Elexon BMRS <ExternalLink size={11} /></a><span className="footer-separator">·</span> All generation values in MW</span></footer>
        </div>
      </main>
    </div>
  );
}

export { App };
