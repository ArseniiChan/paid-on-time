# Paid on Time

**Cash forecasting and compliance checks for NYC-contracted nonprofits.**

[![CI](https://github.com/ArseniiChan/paid-on-time/actions/workflows/ci.yml/badge.svg)](https://github.com/ArseniiChan/paid-on-time/actions/workflows/ci.yml)

New York City pays the nonprofits that run its human services late. On April 15, 2025,
about 4,000 nonprofit invoices worth $861 million were waiting on review in PASSPort
([NYC Comptroller, April 2025](https://comptroller.nyc.gov/reports/nonprofit-nonpayment)).
The Comptroller reports that these delays are forcing providers to take on debt to cover
the gap.

Some of the delay is set off by the nonprofit's own timing. At the Department of Youth and
Community Development, once a provider starts a budget change request in PASSPort, it
cannot submit invoices or be paid on that contract until the change is approved
([DYCD FY27 Fiscal Manual](https://www.nyc.gov/assets/dycd/downloads/pdf/FY27_DYCD_Fiscal_Manual_for_PASSPort_Users_07_30_2026.pdf), p. 43).

Paid on Time gives a nonprofit finance team one place to see what the city owes them, what
could slow it down, and what their cash will look like over the next 90 days.

## What it does

| | Feature | Status |
|---|---|---|
| 1 | **Data ingestion.** Pull the organization's contracts and payments from [Checkbook NYC](https://www.checkbooknyc.com), and import PASSPort exports of invoices and budget modifications, with row-level errors for anything that fails to parse. | Planned |
| 2 | **Rule and freeze alerts.** Check invoices and budget changes against agency billing rules, flag problems with a citation, and warn before a change triggers a billing freeze. | Started: freeze check in `backend/app/rules.py` |
| 3 | **90-day cash forecast.** Project weekly cash from agency payment lags, payroll and credit-line terms, compare scenarios, and export a board-ready PDF or CSV. | Planned |

Full requirements, persona and journey map: [docs/requirements.md](docs/requirements.md).

## Architecture

```
PASSPort CSV upload ──┐
                      ├──► Ingestion ──► Postgres ──► Rule engine ──► Alerts
Checkbook NYC data ───┘                     │
                                            └──────► Forecast ──► Dashboard / PDF export
```

- **Backend:** Python, FastAPI, SQLAlchemy 2. SQLite locally, Postgres when deployed.
- **Frontend:** to be decided by the team.
- **CI:** GitHub Actions runs lint and tests on every pull request.

More detail: [docs/architecture.md](docs/architecture.md). Database schema:
[docs/data-model.md](docs/data-model.md).

## Getting started

Requires Python 3.11 or newer.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest                          # run the tests
uvicorn app.main:app --reload   # start the API at http://127.0.0.1:8000
```

Then open http://127.0.0.1:8000/docs for the interactive API docs.

## Project layout

```
backend/
  app/
    main.py      FastAPI app and routes
    db.py        database engine and sessions
    models.py    database schema
    rules.py     billing rule checks
  tests/
docs/            requirements, architecture, data model
.github/         CI, pull request and issue templates
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: branch off `main`, open a pull request,
get one review, and keep CI green.

## Team

Built as a senior design project at The City College of New York (CSC 59866, Fall 2026).

| Name | Role |
|---|---|
| Arsenii Chan | Project lead, backend |

Teammates add themselves here in their first pull request.

## License

[MIT](LICENSE)
