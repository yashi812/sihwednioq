# WindDesk demo script

## Part 1 — Client pilot overview

### Scene 1 — Decision context

Part one: client pilot walkthrough. WindDesk is a historical replay for a UK utility day-ahead desk. The question is straightforward: before a delivery day, which wind forecast was available, and how far did the outturn later differ? The dashboard places the publication vintage, actual comparison and measured error together. It makes uncertainty visible when a buyer reviews the forecast. It does not choose a purchase volume or replace the trader’s judgement.

### Scene 2 — Delivery day and cutoff

Choose a delivery day and set the purchase decision cutoff. For Thursday the fifteenth of January, the pilot looks back to Wednesday the fourteenth at eleven in the morning, London time. Elexon returned a WINDFOR vintage published at nine thirty GMT. WindDesk keeps that actual publication timestamp beside the decision cutoff, so a reviewer can see which forecast is being scored instead of relying on a forecast that arrived later.

### Scene 3 — Forecast against actual

The profile chart follows all twenty-four hourly values for the selected day. The teal line is the WINDFOR forecast. The warm sand line is the FUELHH wind outturn. The forecast is above actual in this example, but the error varies by hour. This is why the chart sits beside the score: a single average can conceal when the difference was largest. Hover over a point to inspect forecast and actual megawatts.

### Scene 4 — Honest time alignment

The two Elexon series use different resolutions. FUELHH actuals are half-hour average megawatts; the historical WINDFOR sample is hourly. We average each pair of half-hour actual readings into its matching hour, then join on the exact target timestamp. All twenty-four hours match on this day. If either half-hour reading or the forecast is missing, WindDesk leaves that interval out of the score rather than filling it with a guess.

### Scene 5 — Monthly evidence and scope

Across the full month, the replay contains seven hundred and forty-four matched hourly observations across thirty-one delivery days. Mean absolute error is about two thousand one hundred and twenty-three megawatts. Root mean squared error is about two thousand six hundred and seventeen megawatts. Mean bias is positive by about one thousand eight hundred and forty megawatts, meaning the forecast was higher than actual on average. These are wind-forecast accuracy measures, not a calculation of total demand, price or the amount a utility should buy. The CSV export carries each date, cutoff, vintage and matched value for follow-up.

## Part 2 — Technical lead walkthrough

### Scene 6 — Architecture

Part two: technical lead handoff. The React and TypeScript client calls a same-origin FastAPI service. That service retrieves WINDFOR historical vintages and FUELHH actuals directly from the Elexon BMRS API. It normalizes the timestamps, joins the hourly observations, computes the scores and returns one auditable JSON response. The browser never calls Elexon directly. The system has no database or other energy-data provider, because neither is needed for this read-only January pilot.

### Scene 7 — Vintage and data handling

The Elexon client is in backend app elexon. It filters FUELHH to wind and requests each January delivery day’s history using the selected cutoff on the preceding London-local date. The response’s publish time is retained and checked against the cutoff. Upstream requests have timeouts, bounded retries and an in-memory fifteen-minute cache. A failed request is shown as an issue; the app does not silently substitute generated data. January is GMT, while the date conversion still uses the Europe London timezone.

### Scene 8 — Analysis and metrics

The analysis module creates an hourly actual only when both half-hour values exist. For each complete pair, actual megawatts are their arithmetic mean. Forecast-minus-actual is the signed error. MAE averages its absolute value; RMSE takes the square root of the mean squared error; bias averages the signed error. Each metric uses matched points only. The response includes target start time, forecast, actual, signed error and match count, which lets a reviewer trace summary scores back to individual periods.

### Scene 9 — Code and verification

The frontend folder contains the responsive React dashboard, an SVG profile chart and the CSV export. Backend app main exposes health, monthly dashboard and single-day routes. Backend app analysis owns the calculations. Tests cover half-hour averaging, incomplete-pair handling, error sign and coverage. Four backend tests pass, and the TypeScript production build completes. The README maps the directories, gives the local commands and documents the field and score conventions so the next engineer can reproduce the analysis.

### Scene 10 — Container and handoff

The Dockerfile uses a Node build stage for the Vite assets and a Python runtime stage for FastAPI. The same container serves the compiled dashboard and API, honors the platform’s PORT value and exposes an unauthenticated health route. Docker Compose is the local production-shaped run. The intended release path is a Heroku container web process. The pilot remains intentionally narrow: no account system, persisted customer data, load forecasting or automated bidding. The result is small enough to review, rerun and extend without hiding its assumptions.
