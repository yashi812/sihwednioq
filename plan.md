# WindDesk implementation plan

## Product and data approach

Build a React dashboard backed by a Python API for the January 2026 Great Britain wind-generation day-ahead use case. The dashboard will answer two questions: which Elexon wind forecast vintage was available by the decision cutoff for a delivery day, and how did that forecast compare with actual generation? The cutoff will be configurable and shown in `Europe/London`; the default is an explicit pilot assumption of 11:00 local time on the preceding day, not a claim that every utility's trading deadline is identical.

Use Elexon's historical WINDFOR forecast endpoint, requesting the vintage at the cutoff and retaining the returned `publishTime`, and FUELHH actuals filtered to `fuelType=WIND`. Elexon documents FUELHH as average MW over 30-minute periods. The historical WINDFOR sample is hourly. Aggregate the two matching half-hour actual values to hourly average MW, then join by exact hourly `startTime`. Do not interpolate missing actuals or forecasts. Show matched coverage and missing intervals. Define error as forecast minus actual, so positive bias means over-forecast. Report MAE, RMSE and mean bias in MW; also show daily values and a time series so operators can inspect misses rather than relying on one monthly score. Label the results as wind generation forecast evaluation, not total system procurement guidance: the scope excludes demand, prices and other generation sources.

The backend will call Elexon directly, validate the requested month/day/cutoff, use bounded concurrency and request timeouts, cache responses briefly, and expose normalized JSON to the frontend. Errors from the upstream API will be visible as a clear retryable service status rather than silently replaced with invented or synthetic market values. The application will contain no data beyond Elexon sources. Include Elexon attribution and API documentation links.

## Stack, serving and deployment

Use React + TypeScript + Vite for the front end and Python + FastAPI for the API. In development, Vite runs on port 3000 and proxies `/api` to FastAPI on port 8000. In production, a multi-stage Dockerfile builds the React bundle and runs FastAPI with the built assets served from the same container; Docker Compose provides a one-command local start. This keeps the deployment a single app and avoids a cross-origin API configuration. Target Heroku Container Registry/container deployment because the Dockerized full-stack service fits the requested deployment options. Also include Vercel-compatible FastAPI entrypoint, frontend build and static-asset configuration as the permitted provider alternative. Claim a public deployment URL only after a successful provider deployment is verified; if account authorization or provisioning is unavailable, document the exact release path and report the blocker rather than implying publication. No Elexon API key is expected.

## Main project structure

- `frontend/`: Vite, React/TypeScript UI, chart components, API client, styles and browser entry point.
- `backend/app/main.py`: FastAPI app, health/data routes and production static-file serving.
- `backend/app/elexon.py`: Elexon HTTP client, response validation, retry/timeouts and cache.
- `backend/app/analysis.py`: vintage selection, actual-to-hour conversion, exact timestamp join and metrics.
- `backend/tests/`: deterministic unit tests with mocked Elexon payloads; no test will write to a shared production database.
- `public/manus-routes.json`: route declaration required by the preview environment.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`: reproducible local and container deployment.
- `README.md`: setup, architecture, data definitions and attribution, test/run/deploy instructions, file guide, deployed link when confirmed, and explicit AI-tool disclosure.
- `docs/`: architecture diagram and short technical walkthrough notes used for the demo.
 

## Design direction

Three uncommon design directions considered: archival weather almanac (0.04), North Sea instrument-panel modernism (0.07), and high-contrast energy exchange terminal (0.09). Choose **North Sea instrument-panel modernism**.

**Design Movement:** North Sea maritime instrumentation translated into a modern energy operations console.

**Core Principles:** Put decision context before decoration; make forecast and actual visibly distinct; disclose vintage, units and coverage beside every score; keep the data dense but scannable.

**Color Philosophy:** Deep ink-blue signals a calm operating environment. Wind-teal identifies the forecast, pale limestone marks actuals and neutral content, and a restrained signal-lime accent calls attention to decision-ready status without suggesting that an error metric is a trading instruction.

**Layout Paradigm:** A slim persistent left rail anchors an asymmetric, wide working canvas. The top band is a selected delivery-day decision brief; below it, a broad forecast-versus-actual chart sits beside a narrow vintage/coverage rail. Monthly metrics and the delivery-day table follow as secondary layers.

**Signature Elements:** A thin wind-direction-like sweep across forecast charts; small timestamp chips that pin each view to its chosen publication vintage; quiet chart-grid rules inspired by instrument scales.

**Interaction Philosophy:** Every chart/table interaction must preserve traceability. Selecting a day updates the chart and detail; selecting the cutoff recomputes the chosen vintage and metrics; missing intervals stay visibly missing.

**Animation:** Use short, low-amplitude transitions when filters change; animate chart lines only on first reveal; avoid looping, pulsing or motion that could imply market urgency.

**Typography System:** Use DM Sans for interface and labels with DM Mono for values, timestamps and settlement periods. Reserve the largest type for wind MW and keep captions readable with clear unit labels.

**Brand Essence:** A day-ahead wind forecast review desk for UK utility portfolio teams; traceable, candid, operational.

**Brand Voice:** Direct and evidence-led. Example lines: “Forecast vintage selected: 10:30 GMT, before the 11:00 decision cutoff.” “Four hourly periods have no exact actual match; they are excluded from the error score.”

**Wordmark & Logo:** A custom compact wordmark paired with a three-stroke wind-vector mark; not a generic leaf or lightning bolt.

**Signature Brand Color:** North Sea teal.

## Delivery artifacts

Produce a short video with two clearly labeled sections: first a client-facing pilot pitch and dashboard walkthrough (no more than five minutes), then a technical-lead handoff covering architecture, analytical choices, repository structure and development practices (no more than five minutes). Keep the full video within ten minutes. Use the real app interface and source code in the walkthrough. Prepare a public GitHub repository under a random anonymous name and submit its URL, deployed-app URL and demo URL through the challenge form only when the appropriate account/form access is available. Verify submitted public URLs in a private/incognito session before submission. Do not represent unavailable external publication or submission as completed.
