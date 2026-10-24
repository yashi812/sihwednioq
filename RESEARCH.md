# Elexon data research

## Official endpoint behavior

- FUELHH stream: `GET https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream` supports `settlementDateFrom`, `settlementDateTo`, and `fuelType`; examples use `WIND`. Response records include `publishTime`, `startTime`, `settlementDate`, `settlementPeriod`, `fuelType`, and `generation`. The official docs describe average MW over 30 minutes, updated at 30-minute intervals. Source: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
- WINDFOR stream: `GET https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream` supports publish datetime filters, but a direct query for 2026-01-01 returned an empty array in October 2026; historical vintage analysis should use the dedicated forecast history/view endpoints, not assume stream retains all history. Source: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream
- Historical wind forecast history endpoint: `/forecast/generation/wind/history` requires a single `publishTime` and supports JSON/XML/CSV. Elexon states forecasts are published up to eight times daily at 03:30, 05:30, 08:30, 10:30, 12:30, 16:30, 19:30 and 23:30. Source: https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/history
- Earliest and latest historic forecast endpoints accept `from`/`to` delivery-time ranges and return `publishTime`, `startTime`, `settlementPeriod`, and `generation`. Sources: https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/earliest and https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/latest
- Elexon's API base used in live checks: `https://data.elexon.co.uk/bmrs/api/v1`.

## Live API observations (2026-10-24)

- FUELHH query for Jan 1 actuals returned HTTP 200 and 48 half-hourly WIND records for 2026-01-01.
- WINDFOR dataset stream query for publish times on Jan 1 returned HTTP 200 and `[]`; historical endpoint family is therefore needed.
- The day-ahead aggregated forecast endpoint `DGWS/B1440` is a different dataset, provides both wind and solar, and has a maximum 7-day data output range. It uses `processType`, `businessType`, `psrType`, `quantity`, and `publishTime`. Source: https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind-and-solar/day-ahead

## Key product interpretation

Use Elexon WINDFOR historical vintages to represent the latest forecast available by a configurable cutoff before each delivery day, and compare it to exact matching FUELHH actual timestamps. Do not invent/interpolate forecast values for intervals not supplied by WINDFOR. Surface the cutoff, chosen forecast publish time, data timestamp coverage and missing matches. Show MAE/RMSE/bias in MW and include forecast-error direction convention in the UI.

Live API checks for 2026-01-01 show hourly WINDFOR `startTime` values (settlement periods 1, 3, 5, ...) and 30-minute actual records in FUELHH. The `history` API requires a single `publishTime`; querying a timestamp returned a historical forecast vintage with a returned `publishTime` one hour earlier than the queried timestamp in this check. Therefore use the returned `publishTime` rather than assuming the requested value is the actual publication time, and select only vintage data at or before the user-visible cutoff.

## Vercel deployment option (checked 2026-10-24)

Vercel's official Python runtime supports ASGI applications, including FastAPI, and allows a custom module entrypoint through `tool.vercel.entrypoint` in `pyproject.toml`. Its FastAPI guide says `StaticFiles` mounts can be promoted to the CDN when the frontend build output exists at build time; API routes declared before a root static mount take precedence. The repository contains configuration using these documented mechanisms. This is deployment configuration only; no Vercel production URL is claimed without a successful deployment.

Sources:
- https://vercel.com/docs/functions/runtimes/python
- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/git
