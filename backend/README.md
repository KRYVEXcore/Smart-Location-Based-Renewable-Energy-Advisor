# Backend — India-Based Smart Location-Based Renewable Energy Advisor

FastAPI + SQLAlchemy + PostgreSQL + Alembic. Serves India-based location,
resource, tariff, and incentive data — see the root README's
[India-Based Tariff & Incentive Architecture](../README.md#india-based-tariff--incentive-architecture)
section for the data model this backend implements.

## Setup

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy ..\.env.example .env
python -m alembic upgrade head
uvicorn app.main:app --reload
```

The API is served at `http://localhost:8000`. Interactive docs are at
`http://localhost:8000/docs`.

## Migrations

Always run Alembic with `python -m alembic` (not the bare `alembic` command)
so `app` resolves on `sys.path`:

```bash
python -m alembic upgrade head        # apply all migrations
python -m alembic downgrade -1        # roll back one migration
python -m alembic current             # show the applied revision
python -m alembic revision --autogenerate -m "describe the change"
```

The migration URL always comes from `get_settings().database_url` (see
`alembic/env.py`) — never hard-coded in `alembic.ini`.

## Tests

```bash
pytest
```

Tests run against an isolated in-memory SQLite database (see
`tests/conftest.py`) — they never touch the real PostgreSQL dev database.
Location provider tests (`test_location_providers.py`) never make a live
network call either — they replay canned responses through mocked provider
classes in `tests/location_fakes.py` (never wired into production).

Tariff/incentive model tests (`test_tariff_and_incentive_models.py`) and
India location resolution tests (`test_india_geography.py`,
`test_india_resolver.py`) use only clearly-named `TEST-*` fixture rows in
that same isolated SQLite database — never real tariff, subsidy, or DISCOM
data, and never the production PostgreSQL database.

## Environment variables

Copy [`../.env.example`](../.env.example) to `.env` inside this `backend/`
directory (pydantic-settings loads `.env` relative to the process's working
directory). See the [repository root README](../README.md) for details.

## Structure

See the [repository root README](../README.md#repository-structure) for the
full architecture and directory layout, and
[Database Models](../README.md#database-models) /
[API Endpoints](../README.md#api-endpoints) /
[Location Intelligence](../README.md#location-intelligence-phase-3) /
[India-Based Tariff & Incentive Architecture](../README.md#india-based-tariff--incentive-architecture)
for the schema, API, and provider architecture.
