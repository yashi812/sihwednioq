# WindDesk — Day-Ahead Wind Forecast Intelligence

WindDesk is a decision-support pilot for a UK utility desk reviewing national GB wind forecasts at a day-ahead purchase cutoff and comparing them with actual generation. It is a historical replay for January 2026, not a live forecast, dispatch recommendation, or automated bidding system.

**Live Vercel app:** [https://sihwednioq.vercel.app](https://sihwednioq.vercel.app)

**Public source repository:** [github.com/yashi812/sihwednioq](https://github.com/yashi812/sihwednioq)

## Data and analytical definitions

The Python API reads forecast vintages from Elexon's WINDFOR historical wind forecast endpoint and actual generation from FUELHH with `fuelType=WIND`. The decision cutoff is configurable in `Europe/London`; the pilot default is 11:00 on the day before delivery. For each January delivery day, the API requests the historical forecast for that cutoff, keeps Elexon's returned `publishTime`, and rejects any vintage after the cutoff.

Elexon FUELHH reports average MW for each 30-minute interval. WINDFOR history is hourly in the inspected sample. WindDesk averages each pair of matching half-hour FUELHH readings into one hourly actual, then joins on exact UTC `startTime`. A missing half-hour pair remains unscored; it is never interpolated. The signed error is `forecast - actual`, so positive bias means over-forecast. MAE, RMSE and mean bias are calculated in MW from matched hourly points only. The dashboard shows coverage and unmatched counts beside the scores.

Official sources: [FUELHH stream](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream), [WINDFOR history](https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/history), [Elexon API documentation](https://bmrs.elexon.co.uk/api-documentation), and the [BMRS Data Licence Terms](https://www.elexon.co.uk/data/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/).

## Project files

- `frontend/` — React, TypeScript and Vite dashboard.
- `frontend/src/App.tsx` — cutoff/date selection, monthly and daily scores, profile chart, sidebar navigation, retry/refresh behavior, and CSV export.
- `frontend/src/api.ts` — typed API calls and CSV serialization.
- `frontend/src/styles.css` — responsive North Sea instrument-panel design and keyboard-focus states.
- `frontend/public/manus-routes.json` — declared homepage route; `frontend/public/winddesk-logo.svg` — product mark.
- `backend/app/main.py` — FastAPI health, monthly dashboard and single-day routes; production static-file serving.
- `backend/app/elexon.py` — Elexon HTTP client, validation, bounded retries, 15-minute in-memory cache and actual conversion.
- `backend/app/analysis.py` — vintage/day assembly and matched-point MAE, RMSE and bias calculations.
- `backend/tests/` — deterministic tests for metric definitions and half-hour-to-hour matching.
- `scripts/assemble_demo.py` — 720p scene, chapter and video assembly.
- `scripts/build_captions.py` — readable English SRT generation from timed transcripts.
- `docs/demo/dashboard-jan15.png` — January dashboard reference capture; `docs/demo-script.md` — client and technical narration outline; `docs/architecture.md` — system structure.
- `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml` — pinned JavaScript workspace and scripts.
- `pyproject.toml`, `pyrightconfig.json` — Python runtime metadata, Vercel entrypoint and test/type-check settings.
- `requirements.txt` — Vercel Python runtime dependencies; `backend/requirements.txt` — local/container runtime and test dependencies.
- `vercel.json` — Vercel function configuration; `app.config.ts` — managed project logo metadata.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore` — reproducible one-container build and local run.
- `plan.md`, `TODO.md`, `RESEARCH.md` — approved implementation/design plan, assignment outcomes and source evidence.

## Run locally

Requirements: Python 3.11 or later, Node.js 22, pnpm 10 (Corepack can install the pinned version). Docker with the Compose plugin is optional for the container workflow.

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

Run the backend unit tests from the repository root:

```bash
source backend/.venv/bin/activate
pytest backend/tests
```

## API routes

- `GET /health` — unauthenticated container deployment health check.
- `GET /api/health` — API readiness.
- `GET /api/dashboard?cutoff=11:00` — all January delivery days and aggregate monthly metrics.
- `GET /api/day?date=2026-01-15&cutoff=11:00` — one day's chosen vintage and hourly comparison.

The API deliberately rejects delivery dates outside January 2026. Elexon responses are cached in memory for 15 minutes. An upstream error is shown as an issue rather than replaced with sample market data.

## January 2026 reference replay

At an 11:00 Europe/London purchase cutoff, the real Elexon replay matched 744 of 744 hourly forecast/actual points across 31 delivery days. It returned MAE 2,122.8 MW, RMSE 2,616.7 MW and mean bias +1,840.3 MW. Bias is `forecast - actual`, so a positive value means over-forecasting. This is a historical reference result for the displayed cutoff, not a financial-loss estimate; changing the cutoff changes selected vintages and scores.

## Deployment

The public production deployment is [WindDesk on Vercel](https://sihwednioq.vercel.app). It is connected to the public GitHub repository's `main` branch. Anonymous no-cookie checks returned HTTP 200 for `/`, `/api/health`, and `/api/dashboard?cutoff=11:00`; the monthly response contains 31 January days and 744 scored hourly points. The FastAPI entrypoint and pinned runtime dependencies are declared in `pyproject.toml`, `requirements.txt`, and `vercel.json`.

The project also includes a Dockerfile and Compose configuration for a portable one-container deployment. The Dockerfile-backed managed container build completed successfully; this sandbox did not have a local Docker engine.

## Demo deliverable

A narrated two-part 720p walkthrough is delivered separately from this source repository. The client pilot overview is approximately 2:46, the technical-lead walkthrough approximately 3:00, and the combined cut approximately 5:46. English captions are supplied as sidecar SRT files and embedded as a selectable MP4 subtitle track. Each chapter is under five minutes, and the combined video is under ten minutes.

To regenerate the visual scenes, install Pillow and provide `ffmpeg`/`ffprobe`; use `scripts/assemble_demo.py --audio /path/to/narration-wavs --output /path/to/output`. The ten WAV clips are generated narration assets and are not stored in Git.

## AI tools used

Manus AI assisted with Elexon/API research, implementation planning, code generation and code review. The demo narration was generated with Manus text-to-speech using an English (UK) library voice. Manus speech-to-text and video-analysis tools were used for caption preparation and audiovisual review. Scene graphics were composed programmatically. All energy observations, forecasts and score values come from Elexon data; no AI-generated or synthetic market data are used.
