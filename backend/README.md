# Backend — India-Based Smart Location-Based Renewable Energy Advisor

FastAPI + SQLAlchemy + PostgreSQL + Alembic. Serves India-based location,
resource, tariff, and incentive data, and runs the India-Based Solar
Engine, the India Electricity Tariff Engine, and the India Renewable
Energy Incentive Engine — see the root README's
[India-Based Tariff & Incentive Architecture](../README.md#india-based-tariff--incentive-architecture),
[Solar Engine (Phase 4)](../README.md#solar-engine-phase-4),
[Electricity Tariff Engine (Phase 5)](../README.md#electricity-tariff-engine-phase-5),
and [Incentive Engine (Phase 6)](../README.md#incentive-engine-phase-6)
sections for the data model and calculation architecture this backend
implements.

`backend/app/data/tariffs/india/` and `backend/app/data/incentives/india/`
hold verified tariff/incentive seed data (none yet in either — see each
directory's own README for the investigation record) and
`backend/scripts/seed_tariffs.py` / `backend/scripts/seed_incentives.py`
load them into `electricity_tariffs` / `incentive_programs`; run with
`python -m scripts.seed_tariffs` / `python -m scripts.seed_incentives`
from `backend/`.

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

Solar Engine tests (`test_solar_generation.py`, `test_solar_sizing.py`,
`test_solar_validation.py`, `test_solar_engine.py`, `test_solar_api.py`)
are deterministic unit/fixture tests — no live network call, no real NASA
POWER data. Multi-location verification against real Indian coordinates
(Chennai, Mumbai, Jaipur, Bengaluru, Kochi, Coimbatore) was done manually
against the running API, not as part of the automated suite.

Tariff Engine tests (`test_tariff_consumer_category_mapping.py`,
`test_tariff_slab_validation.py`, `test_tariff_slab_calculation.py`,
`test_tariff_version_selection.py`, `test_tariff_bill_calculation.py`,
`test_tariff_engine.py`, `test_tariff_api.py`) are likewise deterministic —
the API tests use `tests/location_fakes.py`'s fake location service (with
a real `IndiaLocationResolver` wired to the test database) so DISCOM
resolution is exercised without a live geocoding call.

Incentive Engine tests (`test_incentive_capacity_slab_validation.py`,
`test_incentive_calculator.py`, `test_incentive_version_selection.py`,
`test_incentive_eligibility.py`, `test_incentive_stacking.py`,
`test_incentive_engine.py`, `test_incentive_api.py`,
`test_seed_incentives.py`) follow the same pattern — no live network call,
synthetic `TEST FIXTURE ONLY`-labeled programme data, and the seed
idempotency tests write to temporary files rather than
`backend/app/data/incentives/india/` (which has no real files yet).

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
[India-Based Tariff & Incentive Architecture](../README.md#india-based-tariff--incentive-architecture) /
[Solar Engine (Phase 4)](../README.md#solar-engine-phase-4) /
[Electricity Tariff Engine (Phase 5)](../README.md#electricity-tariff-engine-phase-5) /
[Incentive Engine (Phase 6)](../README.md#incentive-engine-phase-6)
for the schema, API, and provider/calculation architecture.
