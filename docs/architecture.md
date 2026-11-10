# Architecture

Status key: **Built** exists in `main` today. **Planned** is designed but not written.

## Components

| Component | What it does | Status |
|---|---|---|
| API (FastAPI) | Serves the frontend; `/health` today. | Built |
| Database | Schema in `backend/app/models.py`. SQLite locally, Postgres deployed. | Built (schema) |
| Rule engine | Pure functions that check invoices and budget mods against agency rules. | Started (`rules.py`: billing freeze) |
| Checkbook NYC ingestion | Fetches contracts and payments by vendor name or EIN on a schedule. | Planned |
| PASSPort CSV import | Parses uploaded exports and reports row-level errors. | Planned |
| Forecast | Weekly 90-day cash projection with credit-line interest and scenarios. | Planned |
| Frontend | Dashboard, uploads, alerts, forecast, PDF/CSV export. | Planned; stack not chosen |

## Data flow

1. A finance user uploads PASSPort CSVs; Checkbook NYC data is pulled for their EIN.
2. Ingestion normalizes both into `contract`, `invoice`, `payment` and
   `budget_modification` rows.
3. The rule engine runs on new or changed rows and writes `alert` rows with citations.
4. The forecast reads payments, expected payment lags, expenses and credit-line terms and
   writes one `forecast` row per week.
5. The frontend reads alerts and forecasts through the API.

## Decisions

| Decision | Why |
|---|---|
| Python + FastAPI | Fast to build, typed request models, automatic API docs at `/docs`. |
| SQLAlchemy 2 with typed models | One schema definition shared by the API, rules and tests. |
| Rules as pure functions | Easy to unit test with no database; each rule can carry its citation. |
| Money as `NUMERIC(14,2)` | Avoids float rounding errors in financial totals. |

## Open questions

- Frontend framework.
- Hosting (Render, Railway, Fly.io or similar) and Postgres provider.
- What the Checkbook NYC API can filter on (vendor code vs. name vs. EIN), its rate
  limits, and how often to refresh.
- PASSPort has no public API, so invoice and budget change status comes only from exports
  the nonprofit uploads.
- Where agency rules come from and how they're kept current.
