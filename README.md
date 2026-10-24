# WindDesk — Day-Ahead Wind Forecast Intelligence

WindDesk is a pilot decision-support dashboard for reviewing historical GB wind forecasts at a day-ahead decision cutoff and comparing them with actual generation. The sample is limited to January 2026 and Elexon data. It is an analytical prototype, not a dispatch or procurement recommendation.

## Data and analytical definitions

The Python API reads forecast vintages from Elexon's WINDFOR historical wind forecast endpoint and actual generation from FUELHH with `fuelType=WIND`. The decision cutoff is configurable in `Europe/London`; the pilot default is 11:00 on the day before delivery. For each January delivery day, the API requests the historical forecast for that cutoff and uses the `publishTime` returned by Elexon. It rejects any returned vintage after the cutoff.

Elexon FUELHH reports average MW for each 30-minute interval. WINDFOR history is hourly in the inspected sample. WindDesk averages each pair of matching half-hour FUELHH readings into one hourly actual, then joins on exact UTC `startTime`. A missing half-hour pair remains unscored; it is never interpolated. The signed error is `forecast - actual`, so positive bias means over-forecast. MAE, RMSE and mean bias are calculated in MW from matched hourly points only. The dashboard shows coverage and unmatched counts next to the scores.

Elexon endpoints and definitions: [FUELHH stream](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream), [WINDFOR history](https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/history), and [Elexon API documentation](https://bmrs.elexon.co.uk/api-documentation). Source data is used under the [BMRS Data Licence Terms](https://www.elexon.co.uk/data/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/).

## Project files

- `frontend/` — React/TypeScript/Vite dashboard, styles, SVG chart and API client.
- `backend/app/main.py` — FastAPI health, dashboard and single-day routes; production static-file serving.
- `backend/app/elexon.py` — Elexon HTTP client, validation, bounded retries, 15-minute in-memory cache and actual conversion.
- `backend/app/analysis.py` — vintage/day assembly and matched-point MAE, RMSE and bias calculations.
- `backend/tests/` — unit tests for error definitions and half-hour-to-hour matching.
- `docs/` — implementation and architecture notes used for the technical review.
- `frontend/src/App.tsx` — dashboard selection controls, accuracy summary, day profile, daily error bars and record table.
- `frontend/src/api.ts` — response types, dashboard requests and CSV export.
- `frontend/src/styles.css` — responsive North Sea instrument-panel design system.
- `frontend/public/manus-routes.json` — declared dashboard route for the managed preview.
- `scripts/assemble_demo.py` — 720p scene, chapter and video assembly script for the narrated walkthrough.
- `docs/demo/` — reference dashboard capture; `docs/demo-script.md` — client and technical narration outline.
- `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml` — pinned JavaScript workspace and scripts.
- `pyproject.toml`, `pyrightconfig.json` — Python test and analysis tooling configuration.
- `requirements.txt` — Vercel Python runtime dependencies; `backend/requirements.txt` — local/Docker runtime and test dependencies.
- `vercel.json` — FastAPI function duration; `app.config.ts` — managed project logo metadata.
- `frontend/public/winddesk-logo.svg` — WindDesk mark used by the project.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore` — reproducible container build and local run.
- `plan.md`, `TODO.md`, `RESEARCH.md` — approved implementation/design plan, assignment outcome tracker and Elexon evidence notes.

## Run locally

Requirements: Python 3.11 or later, Node.js 22, pnpm 10 (Corepack can install the pinned version), and optionally Docker with the Compose plugin.

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -r backend/requirements.txt
corepack enable
pnpm install
pnpm dev
```

Open `http://localhost:3000`. Vite serves React and proxies `/api` to FastAPI on port 8000. The backend reads public Elexon API endpoints; no API key or secret is expected.

To run the complete production-shaped app in Docker:

```bash
docker compose up --build
```

Open `http://localhost:3000`. Stop the container with `Ctrl+C` and remove it with `docker compose down`.

Run backend unit tests from the repository root:

```bash
source backend/.venv/bin/activate
pytest backend/tests
```

## API routes

- `GET /health` — unauthenticated deployment health check.
- `GET /api/health` — API readiness.
- `GET /api/dashboard?cutoff=11:00` — all January delivery days and aggregate monthly metrics.
- `GET /api/day?date=2026-01-15&cutoff=11:00` — one day's chosen vintage and hourly comparison.

The API deliberately rejects delivery dates outside January 2026. Elexon responses are cached in memory for 15 minutes. A failed Elexon request is shown as an upstream error rather than replaced with sample market data.

## January 2026 reference replay

The real Elexon replay at an 11:00 Europe/London purchase cutoff matched 744 of 744 hourly forecast/actual points across the month. It returned MAE 2,122.8 MW, RMSE 2,616.7 MW and mean bias +1,840.3 MW. Bias is `forecast - actual`, so a positive value means over-forecasting. This is a historical reference result for the displayed cutoff, not a live forecast or a financial-loss estimate; changing the cutoff changes the selected vintages and scores. The actuals and historical forecast sources are [Elexon FUELHH](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream) and [Elexon wind forecast history](https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/history).

## Deployment

**Public app URL:** not yet deployed; no production URL is claimed.

The repository includes a Vercel FastAPI entrypoint/build configuration (`pyproject.toml`, `requirements.txt`, `vercel.json`) and a Docker/Compose container for Heroku. To deploy on Heroku, use an authorized Heroku account, Docker and the Heroku CLI, then run:

```bash
heroku container:login
heroku container:push web -a YOUR_HEROKU_APP
heroku container:release web -a YOUR_HEROKU_APP
heroku open -a YOUR_HEROKU_APP
```

The container honors Heroku's `PORT` and serves the unauthenticated `/health` route. Replace this section with the confirmed HTTPS URL after a successful release. The Vercel configuration is included as the assignment's other supported hosting option; no Vercel deployment is claimed.

## AI tools used

Manus AI assisted with domain/API research, implementation planning, code generation and development. Market actuals and forecast values are fetched from Elexon; no AI-generated or synthetic energy observations are used.

## Demo and submission

The two-part video renders to 5:59 total (2:45 client pilot and 3:13 technical walkthrough); its unlisted YouTube upload is pending. Public repository: https://github.com/yashi812/sihwednioq. The exact challenge-form URL was not present in the supplied assignment text, so form submission remains pending. No deployment or form submission is represented as completed until its URL is confirmed and checked without an authenticated session.
