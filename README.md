# Smart Location-Based Renewable Energy Advisor

**An India-based decision-support platform** that helps individuals and
small institutions evaluate renewable energy options — Solar PV, Small
Wind, Solar+Wind Hybrid, Battery Storage, and combinations of these — using
India-based resources and data for their own location, building, energy
needs, and budget.

## Project Purpose

Choosing a renewable energy system is hard to do well without site-specific
data: local solar and wind resource, roof or land area, consumption
patterns, installation cost, and available incentives all matter — and in
India, all of these are genuinely local: solar/wind resource varies by
region, electricity tariffs are set per state/UT and per DISCOM, and
incentive schemes exist at the central, state/UT, and DISCOM level, each
with its own eligibility rules. This platform's goal is to turn
India-based location and resource data into a clear, explainable
recommendation — sized and costed by deterministic engineering calculations,
never guessed by an AI model, and never a single nationwide number applied
everywhere.

## Architecture

```
USER
 |
 v
FRONTEND (React + TypeScript)
 |
 v
BACKEND API (FastAPI)
 |
 +--> DETERMINISTIC CALCULATION ENGINES (solar, wind, hybrid, financial, recommendation)
 |
 +--> DATABASE (PostgreSQL via SQLAlchemy)
 |
 +--> AI ADVISOR (SHREA AI, Phase 8) --> engine results as context --> explanation
 |
 +--> VOICE ADVISOR (future) --> speech-to-text --> AI Advisor --> text-to-speech
```

A core architectural principle carries through every future phase: the AI
and voice layers convert conversation into **structured requests** and
explain **validated results** — they never invent system sizes, costs,
savings, or subsidies themselves. All such numbers come from the
deterministic engines in `backend/app/engines/`.

## Technology Stack

**Frontend:** React, TypeScript, Vite, Tailwind CSS

**Backend:** Python, FastAPI, Pydantic, SQLAlchemy, PostgreSQL

**Development:** Git, Docker Compose

**Future AI/ML:** interfaces only in this phase — no LLM, speech-to-text, or
text-to-speech provider is integrated yet.

## Repository Structure

```
renewable-energy-advisor/
├── frontend/                    React + TypeScript + Vite + Tailwind + React Router
│   ├── src/
│   │   ├── components/
│   │   │   ├── navigation/         Navbar (desktop + mobile menu)
│   │   │   ├── buttons/             Reusable Button (link/anchor/button variants)
│   │   │   ├── cards/                SelectableCard, TechnologyCard, ComparisonCard
│   │   │   ├── metrics/               MetricCard (value + empty/pending states)
│   │   │   ├── assessment/             Multi-step assessment form pieces
│   │   │   ├── location/                Map, search dropdown, resource cards (Phase 3)
│   │   │   ├── solar/                     SolarOptionCard, SolarAnalysisSection (Phase 4)
│   │   │   ├── advisor/                   AI advisor UI shell (panel, floating button)
│   │   │   ├── visualizations/             Hero illustration
│   │   │   └── layout/                      Section, Footer
│   │   ├── pages/                Home, Assessment, Dashboard, Location, Advisor
│   │   ├── layouts/              Page shell (MainLayout: nav + advisor panel)
│   │   ├── services/              API client and typed service calls
│   │   ├── hooks/                 Reusable React hooks
│   │   ├── types/                  Shared TypeScript types
│   │   ├── utils/                   Small helpers
│   │   └── assets/
│   └── .env.example
│
├── backend/                      FastAPI application
│   ├── app/
│   │   ├── main.py                FastAPI app instance, CORS, error handling, router wiring
│   │   ├── api/v1/routes/         health.py, assessments.py, locations.py, solar.py,
│   │   │                            tariffs.py, incentives.py
│   │   ├── core/                    config.py, security.py, constants.py,
│   │   │                              india_geography.py (static states/UTs list)
│   │   ├── database/
│   │   │   ├── connection.py          SQLAlchemy engine, session factory, Base
│   │   │   └── repositories/            assessment_repository.py,
│   │   │                                  location_resource_snapshot_repository.py,
│   │   │                                  solar_calculation_snapshot_repository.py,
│   │   │                                  discom_repository.py, tariff_repository.py,
│   │   │                                  tariff_calculation_snapshot_repository.py,
│   │   │                                  incentive_program_repository.py,
│   │   │                                  incentive_evaluation_snapshot_repository.py
│   │   ├── data/
│   │   │   └── incentives/india/         Verified incentive seed data (none yet — see its README.md)
│   │   ├── models/                   User, Building, Location, EnergyProfile,
│   │   │                                BuildingConstraints, Assessment,
│   │   │                                LocationResourceSnapshot, Discom,
│   │   │                                ElectricityTariff, IncentiveProgram,
│   │   │                                SolarCalculationSnapshot, TariffCalculationSnapshot,
│   │   │                                IncentiveEvaluationSnapshot, enums.py
│   │   ├── schemas/                   assessment.py, location.py, solar.py, tariff.py, incentive.py
│   │   ├── services/
│   │   │   ├── assessment_service.py    Assessment persistence orchestration
│   │   │   ├── prototype_user.py         Centralized prototype-user resolution
│   │   │   ├── solar_calculation_service.py  Assessment + LocationProfile -> Solar Engine (Phase 4)
│   │   │   ├── solar_dependencies.py      FastAPI wiring for the above
│   │   │   ├── tariff_calculation_service.py  Assessment + LocationProfile -> Tariff Engine (Phase 5)
│   │   │   ├── tariff_dependencies.py     FastAPI wiring for the above
│   │   │   ├── incentive_evaluation_service.py  Assessment + LocationProfile -> Incentive Engine (Phase 6)
│   │   │   ├── incentive_dependencies.py  FastAPI wiring for the above
│   │   │   ├── location/                  LocationService, cache, provider_factory,
│   │   │   │                                dependencies.py, providers/ (Phase 3),
│   │   │   │                                india_resolver.py (India architecture update)
│   │   │   ├── ai/                        AIAdvisorService interface (Phase 11)
│   │   │   └── voice/                      Speech-to-text / text-to-speech / voice advisor interfaces (Phase 12)
│   │   ├── engines/
│   │   │   ├── solar/                   assumptions.py, generation.py, sizing.py,
│   │   │   │                              validation.py, solar_engine.py (Phase 4 — done)
│   │   │   ├── tariff/                   consumer_category_mapping.py, slab_calculation.py,
│   │   │   │                              version_selection.py, bill_calculation.py,
│   │   │   │                              tariff_engine.py (Phase 5 — done)
│   │   │   ├── incentive/                 eligibility.py, calculator.py, version_selection.py,
│   │   │   │                               stacking.py, validation.py, incentive_engine.py
│   │   │   │                               (Phase 6 — done; reuses tariff's category mapping)
│   │   │   ├── wind/                     Phase 7
│   │   │   ├── hybrid/                    Phase 8
│   │   │   ├── recommendation/             Phase 9
│   │   │   └── financial/                  Phase 10
│   │   └── ml/                             Prediction models (Phase 14)
│   ├── alembic/                    Database migrations (versions/, env.py)
│   ├── scripts/                    seed_all.py (seed_discoms/tariffs/incentives), data_quality_report.py —
│   │                                 reviewed, idempotent data loading; RUN_DATA_SEED=true runs it on start
│   └── tests/
│
├── docs/                          Reserved for future architecture/API docs
├── .devcontainer/                 GitHub Codespaces config (reuses docker-compose.yml)
├── .env.example
├── .gitattributes                 Forces LF line endings on *.sh (Docker/Codespaces need this on Windows)
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Requirements

- Node.js 20+ and npm
- Python 3.11+ (Windows: the `python` launcher may not be configured — use `py` instead)
- PostgreSQL 14+ (or Docker, see below)
- Docker and Docker Compose (optional, for containerized setup)

## Installation

Clone or open the repository, then set up the frontend and backend as
described below. You can run each natively, or run everything through
Docker Compose.

## Environment Configuration

Copy [`.env.example`](.env.example) and fill in real values for any
non-local environment. **Never commit a real `.env` file** — it is already
excluded in [`.gitignore`](.gitignore).

| Variable       | Used by  | Purpose                                             |
| -------------- | -------- | ---------------------------------------------------- |
| `DATABASE_URL` | backend  | SQLAlchemy PostgreSQL connection string               |
| `API_BASE_URL` | frontend | Backend base URL (as `VITE_API_BASE_URL`, see below)   |
| `APP_ENV`      | backend  | `development` \| `staging` \| `production`              |
| `SECRET_KEY`   | backend  | Reserved for future authentication/session signing       |
| `GEOCODING_PROVIDER` / `GEOCODING_API_KEY`             | backend | Default `nominatim`, keyless. Optional. |
| `SOLAR_RESOURCE_PROVIDER` / `SOLAR_RESOURCE_API_KEY`   | backend | Default `nasa_power`, keyless. Optional. |
| `WIND_RESOURCE_PROVIDER` / `WIND_RESOURCE_API_KEY`     | backend | Default `nasa_power`, keyless. Optional. |
| `WEATHER_PROVIDER` / `WEATHER_API_KEY`                 | backend | Default `nasa_power`, keyless. Optional. |
| `ELEVATION_PROVIDER` / `ELEVATION_API_KEY`             | backend | Default `open_elevation`, keyless. Optional. |

The frontend needs its own copy at `frontend/.env` with the `VITE_` prefix
Vite requires — see [`frontend/.env.example`](frontend/.env.example).

None of the location-provider variables are required to run the app
locally — see [Location Intelligence](#location-intelligence-phase-3) for
what each provider does and how to swap one out.

## PostgreSQL Setup

Install PostgreSQL locally and create a database and a dedicated role for
the app, or use the `postgres` service in `docker-compose.yml` (recommended
for local development):

```bash
docker compose up -d postgres
```

This starts PostgreSQL on `localhost:5432` with the credentials in
`docker-compose.yml` (defaults: user `postgres`, password `postgres`,
database `renewable_energy_advisor`). Update `DATABASE_URL` in your `.env`
to match if you change these.

If you're using a PostgreSQL install you already have running instead of
Docker, create a dedicated low-privilege role and database for this project
rather than using the superuser account:

```sql
CREATE ROLE renewable_app WITH LOGIN PASSWORD 'choose-a-password';
CREATE DATABASE renewable_energy_advisor OWNER renewable_app;
```

Then point `DATABASE_URL` in `backend/.env` at that role.

## Database Migrations

Schema changes are managed with Alembic — the app never creates tables from
startup code. From `backend/`, with `DATABASE_URL` set in `.env`:

```bash
alembic upgrade head        # apply all migrations
alembic downgrade -1        # roll back one migration
alembic revision --autogenerate -m "describe the change"   # after editing models
alembic current             # show the applied revision
```

Run these with the venv's Python so `app` resolves on `sys.path`:

```bash
python -m alembic upgrade head
```

## Backend Setup

```bash
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy ..\.env.example .env
python -m alembic upgrade head
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000` (interactive docs at
`http://localhost:8000/docs`). See [`backend/README.md`](backend/README.md)
for more detail.

## Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

The app runs at `http://localhost:5173`. See
[`frontend/README.md`](frontend/README.md) for more detail.

## Docker Setup

With Docker and Docker Compose installed:

```bash
docker compose up --build
```

This starts PostgreSQL, the backend (`http://localhost:8000`, running
`alembic upgrade head` automatically on every start — see
`backend/docker-entrypoint.sh` — before `uvicorn`, so migrations never need
a separate manual step here), and the frontend dev server
(`http://localhost:5173`). Stop everything with `docker compose down` (add
`-v` to also remove the PostgreSQL data volume).

The frontend container talks to the backend container over the Docker
network (`BACKEND_PROXY_TARGET`, proxied by Vite's dev server — see
`frontend/vite.config.ts`) rather than a hard-coded `localhost:8000`, so
the same `docker-compose.yml` also works unmodified in GitHub Codespaces,
where the browser and the containers aren't on the same machine (see
below).

## Run in GitHub Codespaces

No local install at all: open this repository on GitHub, click **Code →
Codespaces → Create codespace on main**, and wait for it to build (a
couple of minutes the first time). `.devcontainer/` reuses the same
`docker-compose.yml` above — PostgreSQL, the backend, and the frontend all
start automatically, migrations included. A preview of the frontend
(port `5173`) opens automatically once it's ready; the backend
(port `8000`) is forwarded too. Nothing needs to be run manually.

## Health Check

Once the backend is running:

```bash
curl http://localhost:8000/api/v1/health
```

```json
{ "status": "healthy" }
```

## Database Models

```
User (id, created_at)
 └── Building (id, user_id, building_type, name, created_at, updated_at)
       └── Assessment (id, building_id, status, created_at, updated_at)
             ├── Location (latitude, longitude, formatted_address, city, state, country, postal_code)
             ├── EnergyProfile (monthly_consumption_kwh, annual_consumption_kwh)
             └── BuildingConstraints (roof_area_sqft, land_area_sqft, budget_inr, backup_required)

LocationResourceSnapshot (latitude, longitude, resource_type, provider, payload, retrieved_at)

SolarCalculationSnapshot (assessment_id, calculation_version, assumption_version,
                           input_snapshot, result_snapshot, created_at)

Discom (id, name, short_code, state, union_territory, is_active)

ElectricityTariff (state, union_territory, discom_id, consumer_category,
                    tariff_version, tariff_name, slab_min_kwh, slab_max_kwh,
                    energy_charge_inr_per_kwh, fixed_charge_inr, demand_charge_inr,
                    wheeling_charge_inr_per_kwh, effective_from, effective_to,
                    source_url, source_document, source_name, last_verified, active)

IncentiveProgram (scheme_name, scheme_version, description, level, incentive_type,
                   state, union_territory, discom_id, consumer_category, technology,
                   min_system_size_kw, max_system_size_kw, subsidy_type, subsidy_value,
                   percentage_value, maximum_amount, calculation_rules, eligibility_rules,
                   application_requirements, stacking_rules, effective_from, effective_to,
                   verification_status, source_name, source_url, source_document,
                   last_verified, active)

TariffCalculationSnapshot (assessment_id, calculation_version,
                            input_snapshot, result_snapshot, created_at)

IncentiveEvaluationSnapshot (assessment_id, calculation_version,
                              input_snapshot, result_snapshot, created_at)
```

- `building_type` (the app's own assessment classification):
  `home` | `school` | `college` | `office` | `shop` | `small_institution` | `other`.
  `ElectricityTariff.consumer_category` and `IncentiveProgram.consumer_category`
  both instead use the separate `TariffConsumerCategory` enum below (Phase 6
  reuses Phase 5's mapping rather than creating a second, incompatible one —
  see [Incentive Engine (Phase 6)](#incentive-engine-phase-6)).
- `consumer_category` on `ElectricityTariff`/`IncentiveProgram` (`TariffConsumerCategory`):
  `residential` | `commercial` | `educational_institution` | `public_service` |
  `industrial` | `agriculture` | `other`
- `incentive_type` on `IncentiveProgram` (what kind of instrument, distinct
  from `level` = who offers it, and `subsidy_type` = how it's calculated):
  `capital_subsidy` | `central_financial_assistance` | `state_subsidy` |
  `discom_incentive` | `rebate` | `interest_subvention` | `grant` |
  `performance_incentive` | `other`
- `subsidy_type` on `ElectricityTariff`/`IncentiveProgram` — Phase 6 added
  `slab_based` and `benchmark_cost_based` to the existing
  `percentage` | `fixed_amount` | `per_kw` | `other`.
- `verification_status` on `IncentiveProgram` — distinct from `active`; only
  `verified` rows are used for automatic eligibility/calculation:
  `verified` | `pending_review` | `expired` | `superseded` | `unavailable`
- `status`: `draft` | `submitted` | `completed` — Phase 2 always saves `submitted`
- `User` has no authentication yet. Every request is attributed to a single
  deterministic prototype user (`app/services/prototype_user.py`) — see the
  Security note below.
- `Location`, `EnergyProfile`, and `BuildingConstraints` store only
  user-provided or browser-derived values persisted with an assessment — no
  renewable-energy calculations happen here.
- `LocationResourceSnapshot` is a Phase 3 write-through audit log of what a
  resource provider returned and when, keyed by coordinate rather than a
  specific assessment (see [Location Intelligence](#location-intelligence-phase-3)
  below) — it is not a foreign key relation off `Location`.
- `Discom`, `ElectricityTariff`, and `IncentiveProgram` are the India-based
  tariff/incentive architecture — see
  [India-Based Tariff & Incentive Architecture](#india-based-tariff--incentive-architecture)
  below. Both `ElectricityTariff` (Phase 5) and `IncentiveProgram` (Phase 6)
  now have working calculation engines, but **no production rows are seeded
  in either** — populating real tariff orders and scheme data is honestly
  unfinished, not unbuilt (see each phase's data-coverage notes for why).
- `SolarCalculationSnapshot` is a Phase 4 write-through audit log (same
  pattern as `LocationResourceSnapshot`) recording the exact input and
  result of every solar calculation, tagged with the engine/assumption
  versions that produced it — see
  [Solar Engine (Phase 4)](#solar-engine-phase-4) below. Deleting an
  assessment cascades to its snapshots (`ON DELETE CASCADE`).
- `TariffCalculationSnapshot` is the same write-through audit pattern for
  Phase 5's tariff calculations (`ON DELETE CASCADE` from day one — see the
  Phase 4 fix note in [Security Notes](#security-notes-phases-2-6) for why
  that matters).
- `IncentiveEvaluationSnapshot` is the same pattern again for Phase 6's
  incentive evaluations (`ON DELETE CASCADE` from day one).

## API Endpoints

All under `API_V1_PREFIX` (`/api/v1`):

| Method | Path                    | Purpose                          |
| ------ | ----------------------- | --------------------------------- |
| GET    | `/health`               | Health check                       |
| POST   | `/assessments`          | Create and persist an assessment    |
| GET    | `/assessments`          | List recent assessments (newest first) |
| GET    | `/assessments/{id}`     | Retrieve a saved assessment           |
| PUT    | `/assessments/{id}`     | Update an assessment (partial, per-section) |
| DELETE | `/assessments/{id}`     | Delete an assessment                   |
| GET    | `/locations/search`     | Geocode a place name (`?q=...`)          |
| GET    | `/locations/profile`    | Normalized solar/wind/weather/elevation data, plus India location resolution (state/UT/district/city/DISCOM), for a coordinate (`?latitude=...&longitude=...`) |
| POST   | `/solar/calculate`      | Technical solar system options for an assessment (`{"assessment_id": "..."}`) |
| POST   | `/assessments/{id}/estimate-consumption` | Retry the bill-based kWh estimate (bill-first assessments) |
| GET    | `/recommendations/{id}` | Deterministic technology + size recommendation built from the existing engines (no AI) |
| POST   | `/wind/calculate`       | Technical wind screening for an assessment (`{"assessment_id": "..."}`) |
| POST   | `/tariffs/calculate`    | Estimated baseline electricity bill for an assessment (`{"assessment_id": "...", "calculation_date": "YYYY-MM-DD"}`, date optional) |
| GET    | `/tariffs`              | Filtered tariff slab lookup (`?state=...&union_territory=...&consumer_category=...&discom_id=...`) |
| POST   | `/incentives/evaluate`  | Incentive eligibility for an assessment (`{"assessment_id": "...", "technology": "solar", "proposed_capacity_kw": 3, "calculation_date": "YYYY-MM-DD"}`, date optional) |
| GET    | `/incentives`           | Filtered incentive programme lookup (`?state=...&union_territory=...&discom_id=...&technology=...&consumer_category=...&level=...`) |

Example `POST /api/v1/assessments` payload:

```json
{
  "building": { "building_type": "home", "name": "My Home" },
  "location": {
    "latitude": 13.114,
    "longitude": 80.154,
    "formatted_address": "Chennai, Tamil Nadu, India",
    "city": "Chennai",
    "state": "Tamil Nadu",
    "country": "India"
  },
  "energy": { "monthly_consumption_kwh": 950 },
  "constraints": {
    "roof_area_sqft": 2500,
    "land_area_sqft": null,
    "budget_inr": 300000,
    "backup_required": true
  }
}
```

The response includes the generated `id`, `status: "submitted"`, timestamps,
and the saved nested `building` / `location` / `energy` / `constraints`
objects — this is the same shape `GET /assessments/{id}` returns.

## Location Intelligence (Phase 3)

```
User
 v
Frontend location search / map (react-leaflet)
 v
FastAPI  GET /locations/search | GET /locations/profile
 v
LocationService  (app/services/location/location_service.py)
 v
Provider Factory  ->  Geocoding | Solar | Wind | Weather | Elevation adapters
 |
 +--> IndiaLocationResolver  ->  state/UT -> district -> city -> DISCOM
 v
Normalized LocationProfile  (never a specific provider's raw shape)
```

`LocationService` and the routes only ever depend on the interfaces in
`app/services/location/providers/base.py` and the normalized schemas in
`app/schemas/location.py` — never on a specific provider's response shape.
Swapping a provider means adding one class and one branch in
`provider_factory.py`; nothing else changes.

**Providers (all free, keyless, real — no mock data reaches production):**

| Category  | Provider       | Data returned                                    |
| --------- | -------------- | ------------------------------------------------- |
| Geocoding | Nominatim (OSM) | Search + reverse geocoding, scoped to India         |
| Solar     | NASA POWER      | Monthly + annual global horizontal irradiance (GHI)  |
| Wind      | NASA POWER      | Monthly + annual wind speed at 10m **and** 50m         |
| Weather   | NASA POWER      | Monthly + annual temperature, precipitation, cloud index (derived from all-sky/clear-sky irradiance) |
| Elevation | Open-Elevation  | Elevation at the queried point                          |

Every provider is independently swappable via `*_PROVIDER` / `*_API_KEY` env
vars (see [Environment Configuration](#environment-configuration)) — a
provider that requires a key simply isn't wired into `provider_factory.py`
yet in Phase 3, and requesting one raises a clear "not configured" error
rather than silently falling back to fake data.

**Resilience:** each of the four resource sections in a `LocationProfile`
degrades independently. If wind times out but solar succeeds, the response
is still `200 OK` with `wind: null` and `errors.wind: {"code": "timeout", ...}`
— never a fabricated zero. `GET /locations/search` is the exception: if
geocoding itself fails there's no partial result to return, so it responds
with a mapped HTTP status (429 rate-limited, 504 timeout, 502 upstream
failure, 501 not configured).

**Caching:** `app/services/location/cache.py` defines a minimal
`LocationCache` protocol. The default `InMemoryLocationCache` needs no
infrastructure — Redis is deliberately not required to run this app
locally. A Redis-backed implementation could be dropped in behind the same
interface later. Cache keys include the resource type and rounded
coordinate; entries expire after `LOCATION_CACHE_TTL_SECONDS` (default 24h,
since climatology and elevation data barely change) and failed fetches are
never cached, so a transient error is retried on the next request.
`LocationResourceSnapshot` additionally persists every successful fetch to
PostgreSQL as a best-effort audit log (survives restarts; not on the
request's critical path).

**Data freshness:** every populated section carries `source` and
`retrieved_at`; solar/wind/weather also carry `period_represented` (NASA
POWER's climatology is a 2001-2020 average, not real-time). The frontend
distinguishes real retrieved data, "unavailable" (with the specific reason:
timeout/rate-limited/not-configured/etc.), and "not yet requested" — never
zero-as-unavailable, and it never shows a made-up suitability score.

**Mock testing:** `backend/tests/location_fakes.py` defines fake providers
used only by tests (`test_location_providers.py`, `test_location_service.py`,
`test_locations_api.py`). They are never imported by
`provider_factory.py`, so the production path can't accidentally select a
mock. Provider-normalization tests replay real, previously-captured response
shapes through `monkeypatch`ed `httpx.get` calls — no test makes a live
network call.

### India location resolution

Every `GET /locations/profile` response includes an `india` section
(`app/services/location/india_resolver.py`), resolving the reverse-geocoded
address to India's administrative hierarchy for future tariff/incentive
matching:

```
latitude/longitude -> state or union territory -> district -> city -> DISCOM
```

- `state`/`union_territory` are normalized to the canonical spelling in
  `app/core/india_geography.py` (a static, universally-known list of India's
  28 states and 8 union territories — not a sourced/versioned policy value,
  unlike tariffs and incentives below). A geocoder result that doesn't match
  any known state/UT (typos, a location outside India, an unrecognized
  alias) comes back `null` — never a guessed nearest match.
- `district`/`city` come directly from the geocoder's normalized
  `GeocodingCandidate` (Nominatim's `state_district`/`county` and
  `city`/`town`/`village` address components).
- `discom` is resolved from the `Discom` table by matching the normalized
  state/UT. **The app never guesses a DISCOM from a city name.** If zero
  DISCOM rows match, or if more than one DISCOM serves that state and
  there's no way to disambiguate further, `discom` is `null` and
  `discom_status` explains why (`"not_identified"` or `"ambiguous"` — only
  `"identified"` when exactly one active match exists). The `discoms` table
  ships empty; nothing is guessed or seeded as if it were real.

## India-Based Tariff & Incentive Architecture

Prepared the data model the India-Based Solar Engine (Phase 4), the India
Electricity Tariff Engine (Phase 5), and the Incentive Engine (Phase 6,
below) all read from. **Both the tariff and incentive sides now have
working calculation engines** (see
[Electricity Tariff Engine (Phase 5)](#electricity-tariff-engine-phase-5)
and [Incentive Engine (Phase 6)](#incentive-engine-phase-6)) — but **no
production tariff or incentive rows are seeded in either**; see each
section's honest-data-coverage note for why.

```
LOCATION INTELLIGENCE  ------->  India Location Resolver
   (solar/wind/weather/            (state/UT, district, city, DISCOM)
    elevation — real-time
    lookup, cached)                        |
                                            v
                              TARIFF / INCENTIVE DATA
                        (ElectricityTariff, IncentiveProgram —
                         versioned, sourced, DB-only, no calculation)
                                            |
                                            v
                         Future Calculation Engines (Phase 4+)
```

This is a deliberate separation: **location intelligence provides
environmental/resource data; tariff/incentive data provides electricity
economics and scheme eligibility; calculation engines combine both with
deterministic formulas.** No layer invents a value that belongs to another.

### Tariff architecture (`app/models/electricity_tariff.py`)

One row per tariff slab (a real tariff order typically has several, e.g.
0–100 kWh, 101–300 kWh, ...): `state` / `union_territory`, `discom_id`
(nullable FK to `Discom`), `consumer_category` (`TariffConsumerCategory` —
a real Indian DISCOM tariff category, distinct from `BuildingType`; see
[Electricity Tariff Engine (Phase 5)](#electricity-tariff-engine-phase-5)),
`tariff_version` (groups the slab rows of one published schedule),
`tariff_name`, `slab_min_kwh`/`slab_max_kwh`, `energy_charge_inr_per_kwh`,
`fixed_charge_inr`, `demand_charge_inr`, `wheeling_charge_inr_per_kwh`,
plus the versioning/source fields below. The table is empty in production;
only `tests/test_tariff_and_incentive_models.py`'s clearly-named `TEST-*`
fixtures ever populate it — see the Phase 5 section for why no state's real
data has been seeded yet.

### Incentive architecture (`app/models/incentive_program.py`)

One row per scheme *version* (see
[Incentive Engine (Phase 6)](#incentive-engine-phase-6) for the full
architecture). `level` separates **central** / **state** / **discom**
schemes — they are never combined into one number. `consumer_category`
(`TariffConsumerCategory`, same enum and mapping as `ElectricityTariff` —
never a second, incompatible category concept) is nullable (a scheme can
be category-agnostic) but the eligibility engine treats `null` as "check
`eligibility_rules`", never as "applies to everyone" — this is exactly
what stops a residential central subsidy (e.g. PM Surya Ghar) from being
silently applied to a school, college, or office. `technology`
(solar/wind/hybrid/battery/other), `incentive_type` (what kind of
instrument — capital subsidy, CFA, rebate, etc.), `subsidy_type` (how the
amount is calculated — percentage/fixed_amount/per_kw/slab_based/
benchmark_cost_based/other) with `subsidy_value`/`percentage_value`/
`calculation_rules` (meaning depends on `subsidy_type`), `maximum_amount`
(a cap), `min_system_size_kw`/`max_system_size_kw`, `eligibility_rules` +
`application_requirements` + `stacking_rules` (JSON, for conditions that
don't fit a column), and `verification_status` (distinct from `active` —
only `verified` rows are used for eligibility/calculation). The table is
empty in production, same as tariffs.

The architecture supports every case the eligibility rules require: a
central-only scheme with no state top-up, a state scheme with no DISCOM
rule, multiple simultaneously-applicable schemes (multiple rows, each
independently evaluated — never auto-summed), no additional incentive for
a given state (simply no row), an expired scheme (`effective_to` in the
past), and "eligibility unknown" (no row matches, or a row exists but
isn't `verified` — the honest absence of usable data, not a guess).

### Data versioning & source traceability

`ElectricityTariff` and `IncentiveProgram` carry the same versioning
fields: `effective_from`, `effective_to`, `last_verified`, `source_url`,
`source_document`, `source_name`, `active` (`IncentiveProgram` additionally
has `verification_status` and a `scheme_version` string, since a
government scheme's version history matters more than a tariff schedule's
— see [Incentive Engine (Phase 6)](#incentive-engine-phase-6)). Both
engines resolve the record valid on the calculation date and never use an
expired record when a current one exists — this is implemented and tested,
not just modeled. The frontend shows, for any tariff or incentive:
`Source: <source_name>`, `Last verified: <last_verified>`,
`Effective: <effective_from> – <effective_to or "ongoing">`. No fake
source URLs or verification dates are ever stored — an unpopulated record
simply doesn't exist yet.

### DISCOM registry (`app/models/discom.py`)

A simple, empty-by-default registry: `name`, `short_code`, `state` /
`union_territory` (exactly one expected per row), `is_active`. Real DISCOM
boundary data (which DISCOM serves which district/city) is out of scope
for this update — populating it from an authoritative source (each state's
electricity regulatory commission) is future work.

## Solar Engine (Phase 4)

**Phase 4 estimates technical solar generation and system feasibility. It
does NOT determine a final recommendation, subsidy, tariff-based savings,
payback, or final purchase price** — those are later phases (see
[Financial Boundary](#financial-boundary) below).

```
Location Intelligence (Phase 3, India-based resource data)
        v
Normalized Solar Resource (app.schemas.location.SolarResourceProfile)
        v
Solar Engine (app/engines/solar/ — pure functions, no FastAPI/DB/API import)
        v
System Options (1-10 kW, each independently evaluated)
        v
Future Financial Engine
```

`app/engines/solar/` never imports FastAPI, SQLAlchemy, or an HTTP client.
`SolarCalculationService` (`app/services/solar_calculation_service.py`)
is the only thing that bridges the two worlds: it loads the Assessment,
calls the existing Phase 3 `LocationService.get_profile()` — **the Solar
Engine never calls NASA POWER or any provider directly** — and hands the
engine a plain `SolarEngineInput`.

### Formula

Standard rooftop-PV yield estimation, applied uniformly to every Indian
location — there is no per-state branching; the only thing that varies by
location is the resource value itself:

```
Annual Generation (kWh) = Capacity (kWp) x Daily Solar Resource (kWh/m^2/day) x 365 x Performance Ratio
```

The daily solar resource value is NASA POWER's `ALLSKY_SFC_SW_DWN`
(kWh/m²/day), which is numerically equivalent to "peak sun hours per day"
— exactly what this formula expects (the same method underlying
widely-used tools like NREL's PVWatts). Monthly generation uses each
month's own average daily value and its real calendar day-count (28-31),
never a naive annual-divided-by-12 split. See
`app/engines/solar/generation.py`.

Roof area required scales from panel wattage, panel footprint, and a
layout/shading-clearance factor — see `app/engines/solar/sizing.py`.

### Assumptions (`app/engines/solar/assumptions.py`)

Every non-measured constant is named, versioned, and sourced — never
inline in a calculation function:

| Assumption | Default | Basis |
| --- | --- | --- |
| `performance_ratio` | 0.75 | Conservative default for Indian rooftop PV (typical published range 0.70-0.85); covers inverter, wiring, soiling, temperature losses |
| `panel_wattage_w` | 400 W | Representative modern monocrystalline PERC module |
| `panel_area_sqft` | 21 sq ft | Physical footprint of a ~400W panel |
| `layout_factor` | 1.4 | Typical allowance for mounting spacing, walkways, shading clearance |

`ASSUMPTION_VERSION` and `ENGINE_CALCULATION_VERSION` are returned in
every response and recorded in `SolarCalculationSnapshot`, so a past
result stays interpretable even after these values are later revised.

### Units

1 electricity unit = 1 kWh throughout — the field is always
`monthly_consumption_kwh`/`annual_consumption_kwh`, never a bare `units`.

### Candidate evaluation and technical feasibility

Every request evaluates all of 1, 2, 3, ..., 10 kW independently — **the
engine never picks or labels a "best", "recommended", "optimal", or
"cheapest" option**; that comparison is the future Recommendation Engine's
job. Each option reports:

- `estimated_annual_generation_kwh` / `estimated_monthly_generation_kwh`
- `roof_area_required_sqft`
- `generation_coverage_percent` — generation ÷ annual consumption, **not
  capped at 100%** and **not a claim about the electricity bill** (see
  Financial Boundary below)
- `technical_status`: `technically_feasible` | `technically_infeasible` |
  `insufficient_data` (e.g. roof area wasn't provided — generation numbers
  are still shown even then, since they don't depend on roof area)

If the location's solar resource is unavailable, non-positive, or in an
unrecognized unit, the whole response is `status: "insufficient_data"`
with a `reason` — never a fabricated result.

### Financial boundary

Generation is not the same as a lower electricity bill. Actual savings
depend on tariff, self-consumption, export/net-metering rules, fixed
charges, and applicable incentives — none of which are calculated in
Phase 4. The response includes no cost, subsidy, saving, or payback field,
and the frontend explicitly states "Financial analysis ... will be
available in a later phase" rather than implying it already exists.

### API

`POST /api/v1/solar/calculate` — `{"assessment_id": "..."}`. Flow:
retrieve the assessment, retrieve its Phase 3 location profile, validate
solar-resource availability, run the engine, record a
`SolarCalculationSnapshot`, return the structured result. A 404 means the
assessment doesn't exist; `status: "insufficient_data"` (still `200 OK`)
means the assessment/location exists but the calculation couldn't run
(missing coordinates, unavailable resource, invalid input) — the frontend
distinguishes these.

### Reproducibility

Given the same input, `calculation_version`, and `assumption_version`, the
engine is a pure function and returns identical `options` and
`annual_consumption_kwh` — verified directly (`test_solar_engine.py`) and
live against the real API.

## Electricity Tariff Engine (Phase 5)

**Phase 5 estimates a baseline grid-electricity bill from an assessment's
existing consumption and location data. It does NOT calculate subsidies,
solar cost, payback, ROI, or savings** — those remain later-phase
boundaries (see [Financial boundary](#tariff-financial-boundary) below).

```
Assessment (energy.monthly_consumption_kwh, building.building_type)
        v
Phase 3 LocationService.get_profile() -> IndiaLocationContext
        (state/UT, DISCOM, discom_status — never re-derived)
        v
BuildingType -> TariffConsumerCategory (explicit mapping, never assumed equal)
        v
TariffRepository (state/UT + DISCOM + category candidates)
        v
Tariff Engine (app/engines/tariff/ — pure functions, no FastAPI/DB/API import)
   - select the tariff_version covering the calculation date
   - cumulative/progressive slab calculation (Decimal, never float)
   - charge components: energy, fixed, demand, wheeling, time-of-day
        v
Estimated baseline bill + per-component included/not_included/not_calculated status
```

`app/engines/tariff/` never imports FastAPI, SQLAlchemy, or an HTTP client
— the same rule as `app/engines/solar/`. `TariffCalculationService`
(`app/services/tariff_calculation_service.py`) is the only bridge: it loads
the Assessment, calls the existing Phase 3 `LocationService.get_profile()`
(the tariff engine never re-runs geocoding or DISCOM resolution itself),
maps `BuildingType` to `TariffConsumerCategory`, queries candidate tariff
rows, and hands the engine a plain list of slab DTOs.

### Consumer category mapping (`app/engines/tariff/consumer_category_mapping.py`)

A real DISCOM tariff category is not the same thing as the app's
`BuildingType`, so the two are never treated as interchangeable. The
mapping is one explicit, testable dict:

| BuildingType | TariffConsumerCategory |
| --- | --- |
| `home` | `residential` |
| `school`, `college` | `educational_institution` |
| `office`, `shop` | `commercial` |
| `small_institution` | `public_service` |
| `other` | `other` |

### DISCOM scoping

Never guesses which DISCOM's tariff applies:

- `discom_status: "identified"` — prefers that exact DISCOM's tariff rows;
  falls back to a state-level tariff (`discom_id IS NULL`) only if that
  DISCOM has none configured.
- `discom_status: "ambiguous"` or `"not_identified"` — only a state-level
  tariff (no specific DISCOM) may be used; a DISCOM-specific tariff is
  never guessed. If no state-level tariff exists either, the response is
  `discom_ambiguous` (ambiguous case) or `tariff_not_configured`.

### Slab calculation (`app/engines/tariff/slab_calculation.py`)

Cumulative/progressive ("telescoping") billing using `Decimal` throughout
— never `float` — for exact money math. Each slab covers
`[slab_min_kwh, slab_max_kwh)`; the final slab's `slab_max_kwh` is `None`
and extends indefinitely. Consumption landing exactly on a boundary is
billed entirely within the lower slab. `app/engines/tariff/validation.py`
rejects (raises `ValueError`, never silently "fixes") slabs that are
empty, negative, overlapping, non-contiguous, don't start at 0, or have
more than one unlimited slab — a malformed tariff dataset must never
silently produce a wrong number.

### Tariff version selection (`app/engines/tariff/version_selection.py`)

A state/DISCOM/category can have multiple `tariff_version` schedules on
file over time (superseded orders kept for reproducibility). Exactly one
is selected for the requested `calculation_date`: the version whose
`[effective_from, effective_to]` range covers that date, preferring the
latest `effective_from`, with ties broken by the version string itself —
deterministic, never random, never dependent on database row order.

### Charge components

Each component is reported as `included` (with an amount), `not_included`
(the tariff data itself has no such charge), or `not_calculated` (this app
doesn't collect the input needed) — never fabricated as zero:

| Component | When `included` | When `not_calculated` |
| --- | --- | --- |
| `energy` | Always (the slab calculation) | — |
| `fixed` | `fixed_charge_inr` is configured on the tariff | — |
| `wheeling` | `wheeling_charge_inr_per_kwh` is configured | — |
| `demand` | — | Always — requires sanctioned load/kVA, which this app's assessment does not collect |
| `tod` (time-of-day) | — | Always — requires interval consumption data, which this app's assessment does not collect |

`estimated_monthly_bill_inr` sums only the `included` components;
`is_partial_estimate` and `excluded_components` make it explicit whenever
`demand`/`tod` were skipped (i.e. always, today).

<a id="tariff-financial-boundary"></a>

### Financial boundary

The response contains no subsidy, solar cost, saving, payback, ROI, or
recommendation field. `app.engines.tariff.calculate_bill_for_grid_consumption`
is written to be reusable by a future engine that needs a grid-only bill
estimate (e.g. comparing grid cost against a solar-offset scenario)
without recomputing tariff resolution — but Phase 5 itself never performs
that comparison.

### API

`POST /api/v1/tariffs/calculate` — `{"assessment_id": "...", "calculation_date": "YYYY-MM-DD"}`
(date optional, defaults to today). Response `status` is one of:

- `ok` — a tariff was found and a bill was calculated (possibly partial —
  see `is_partial_estimate`)
- `insufficient_data` — no coordinates, or the location couldn't be
  resolved to an Indian state/UT
- `discom_ambiguous` — multiple DISCOMs match and no state-level fallback
  tariff is configured
- `tariff_not_configured` — the state/category/date is understood, but no
  verified tariff data exists for it

`GET /api/v1/tariffs?state=...&union_territory=...&consumer_category=...&discom_id=...`
— a filtered raw-slab lookup for browsing/debugging what's configured.

### India tariff data coverage (verified in Phase 6.7)

Per this project's standing rule — **real data > no data > fake data** — a
tariff is only seeded once its slabs, rates and charges were read from a
primary official document (state regulator order or DISCOM publication)
and the exact page/table is recorded. Verified and seeded (residential
only): **Tamil Nadu** (TNPDCL), **Andhra Pradesh** (all three DISCOMs,
FY 2026-27), **Karnataka** (all ESCOMs), **Rajasthan** (all three DISCOMs)
and **Maharashtra** (MSEDCL — verified, but Maharashtra
locations resolve as DISCOM-`ambiguous` because Mumbai has other licensees,
so it is reported as blocked, never guessed). Kerala was verified but is
**not seeded**: its non-telescopic billing above 250 units/month cannot be
represented by the engine. Every other State/UT is unconfigured and answers
`tariff_not_configured`.

Every row carries `source_name`, `source_url`, `source_document`,
`source_order_number`, `source_order_date`, `source_page`, `source_table`,
`source_section`, `source_excerpt`, `verification_status`,
`verification_notes` and `last_verified`; the dashboard shows them under
"Verified against an official source". Only `verified` + `active` rows are
ever used for a bill. Fixed charges record what they are charged *per*
(`fixed_charge_basis`): a per-kW charge is never turned into a flat monthly
amount. See [`docs/data-verification/`](docs/data-verification/) for the
research log, coverage report and the generated data-quality report, and
[`backend/app/data/tariffs/india/README.md`](backend/app/data/tariffs/india/README.md)
for the file format.

Seeding: `python -m scripts.seed_all [--dry-run] [--expect-database NAME]`
(from `backend/`) validates every data file, then upserts DISCOMs, tariffs
and incentives in one transaction. It is idempotent and never deletes a row.
On Render the container runs it on start when `RUN_DATA_SEED=true`.

### Reproducibility

Given the same input, candidate rows, and `calculation_date`, the engine
is a pure function and returns identical charges and totals — verified
directly (`test_tariff_engine.py`) and live against the real API. Every
calculation is also recorded to `TariffCalculationSnapshot`
(`ON DELETE CASCADE` on the owning assessment, same pattern as
`SolarCalculationSnapshot`).

## Incentive Engine (Phase 6)

**Phase 6 evaluates which renewable-energy incentive programmes an
assessment may be eligible for, and calculates their amount when the
programme's own documented formula allows it from data this app actually
collects. It does NOT calculate final installation cost, final savings,
payback, ROI, or a wind/hybrid/battery recommendation** — see
[Financial boundary](#incentive-financial-boundary) below.

```
Assessment (building.building_type, energy.monthly_consumption_kwh, constraints)
        v
Phase 3 LocationService.get_profile() -> IndiaLocationContext
        (state/UT, DISCOM, discom_status — never re-derived)
        v
BuildingType -> TariffConsumerCategory (Phase 5's mapping, reused — never a second one)
        v
IncentiveProgramRepository (technology + state/UT/DISCOM candidates,
                             NOT pre-filtered by category — see below)
        v
Incentive Engine (app/engines/incentive/ — pure functions, no FastAPI/DB/API import)
   - group candidate rows into distinct schemes (scheme_name + level + technology)
   - select the scheme_version covering the calculation date
   - evaluate eligibility (verification status, technology, category, capacity, rules)
   - calculate the amount when the documented formula and available data allow it
   - flag stacking/combinability uncertainty across simultaneously-eligible programmes
        v
Every candidate programme's eligibility status — eligible ones never hidden,
ineligible/unverified/uncertain ones never hidden either
```

`app/engines/incentive/` never imports FastAPI, SQLAlchemy, or an HTTP
client — the same rule as `app/engines/tariff/` and `app/engines/solar/`.
`IncentiveEvaluationService` (`app/services/incentive_evaluation_service.py`)
is the only bridge: it loads the Assessment, calls the existing Phase 3
`LocationService.get_profile()` (DISCOM resolution is never re-run), maps
`BuildingType` to `TariffConsumerCategory` via
`app.engines.tariff.consumer_category_mapping` (imported directly — Phase 6
has no category-mapping file of its own), queries candidate programme rows,
and hands the engine a plain list of programme DTOs.

The repository deliberately does **not** filter by consumer category (only
by technology and state/UT/central scope): a programme that doesn't match
the assessment's category still needs to come back so the engine can
report it `not_eligible` — filtering it out at the query level would hide
it entirely, which section 25's "never hide an ineligible or uncertain
programme" rule forbids.

### Consumer category & DISCOM scoping

Identical rules to Phase 5, applied here too: **never** assume a solar
incentive applies to wind/battery, or a residential scheme applies to a
commercial consumer — technology and `consumer_category` must match
exactly (or the programme's category is `null`, meaning genuinely
category-agnostic). DISCOM scoping mirrors Phase 5's:

- `discom_status: "identified"` — prefers that exact DISCOM's programmes;
  falls back to a state-level programme only if that DISCOM has none.
- `discom_status: "ambiguous"` or `"not_identified"` — a DISCOM-specific
  programme is never guessed. Each blocked DISCOM-level scheme is still
  reported explicitly, as `discom_ambiguous` or `discom_not_identified` —
  never silently omitted.

### Scheme versioning (`app/engines/incentive/version_selection.py`)

A distinct scheme (identified by `scheme_name` + `level` + `technology`)
can have several `scheme_version` rows on file over time — e.g. PM Surya
Ghar's guidelines have been amended more than once since 2024. Exactly one
version is selected for the requested calculation date: the version whose
`[effective_from, effective_to]` range covers it, preferring the latest
`effective_from`, ties broken by the version string — deterministic, never
random. If no version covers the date, the scheme is reported
`scheme_expired` (every version is in the past) or `scheme_not_active`
(every version is in the future) — never silently dropped.

### Eligibility (`app/engines/incentive/eligibility.py`)

Checks, per candidate scheme version, in order: `verification_status`
(only `verified` proceeds — anything else is `scheme_not_verified`),
`active`, technology match, `consumer_category` match, `min_system_size_kw`
(a smaller system is genuinely `not_eligible`), documented
`eligibility_rules.requires_fields` (any field this app doesn't collect at
all — e.g. income level, ownership status, sanctioned load/kVA — always
resolves as missing, never invented, giving `insufficient_information`
with the exact field names), and finally the amount calculation itself. A
system **larger** than `max_system_size_kw` is still eligible — the cap
just limits how much capacity counts toward the calculation (e.g. PM Surya
Ghar's CFA caps at 3 kW even for a bigger system), matching how the real
schemes actually work.

### Calculation (`app/engines/incentive/calculator.py`)

Decimal throughout — never float. Supports:

| `subsidy_type` | Formula | Needs |
| --- | --- | --- |
| `fixed_amount` | A flat amount | `subsidy_value` |
| `per_kw` | Rate × eligible capacity | `subsidy_value` |
| `slab_based` | Telescoping capacity brackets (same algorithm shape as Phase 5's consumption slabs, applied to kW instead of kWh) | `calculation_rules.slabs` |
| `percentage` | Percentage × eligible installation cost | `percentage_value` **and** a real cost basis |
| `benchmark_cost_based` | Percentage × a published benchmark cost per kW | `calculation_rules.benchmark_cost_per_kw_inr` + `eligible_percentage` |

<a id="incentive-financial-boundary"></a>

### Financial boundary

**This app collects no verified installation cost anywhere** —
`BuildingConstraints.budget_inr` is the user's own aspirational budget, not
a vendor quotation. `percentage`-type incentives are therefore always
`insufficient_information` today, honestly, rather than computed against
an invented cost — `fixed_amount`, `per_kw`, and `slab_based` (which only
need capacity) can be calculated in full. The response never contains a
final installation cost, savings, payback, or ROI figure.

### Stacking (`app/engines/incentive/stacking.py`)

Multiple eligible programmes are **never summed into one total** — each
stays its own line item in the response. Two simultaneously-eligible
programmes are only left unflagged if **both** sides' `stacking_rules`
explicitly confirm combinability; an explicit
`mutually_exclusive_with_levels` entry on either side flags both as
`mutually_exclusive_with_other_programme`; anything else (including
silence on one or both sides) flags both `combination_requires_verification`
— absence of a documented rule is never treated as permission to combine.

### API

`POST /api/v1/incentives/evaluate` —
`{"assessment_id": "...", "technology": "solar", "proposed_capacity_kw": 3, "calculation_date": "YYYY-MM-DD"}`
(date optional, defaults to today). The frontend only ever submits
assessment/context — the backend always selects the trusted, verified
programme data itself; the frontend can never submit a subsidy rate or
amount and get it echoed back as a calculation. Top-level `status` is
`ok` or `insufficient_data` (no coordinates, or the location couldn't be
resolved to an Indian state/UT); each entry in `programmes` carries its
own status (`eligible` | `not_eligible` | `insufficient_information` |
`scheme_expired` | `scheme_not_active` | `scheme_not_verified` |
`discom_ambiguous` | `discom_not_identified`) — ineligible and unverified
programmes are always included, never hidden.

`GET /api/v1/incentives?state=...&union_territory=...&discom_id=...&technology=...&consumer_category=...&level=...`
— a filtered raw-programme lookup for browsing/debugging what's
configured.

### India incentive data coverage (verified in Phase 6.7)

A scheme is only seeded once its rates, capacity limits and conditions
were read from a primary official document. Verified and seeded: **PM
Surya Ghar: Muft Bijli Yojana** — Central Financial Assistance to
residential consumers (MNRE guideline OM No. 318/17/2024-GCRT): Rs 30,000
per kW for the first 2 kW and Rs 18,000 for the third kW, nothing beyond
3 kW (max Rs 78,000), and Rs 33,000 / Rs 19,800 for the special-category
States/UTs (a separate row, chosen by region via `eligibility_rules`, see
`app.engines.incentive.scope`). It is residential-only, so a college, shop
or office is reported `not_eligible`. Valid until the guideline's
implementation end, 2027-03-31.

**State and DISCOM incentives: none verified.** The five priority states
were checked in official pages and no state amount was found; nothing is
seeded for them. See [`docs/data-verification/`](docs/data-verification/)
and [`backend/app/data/incentives/india/README.md`](backend/app/data/incentives/india/README.md).

### Reproducibility

Given the same input and candidate rows, the engine is a pure function and
returns identical eligibility results and amounts — verified directly
(`test_incentive_engine.py`) and live against the real API. Every
evaluation is recorded to `IncentiveEvaluationSnapshot` (`ON DELETE
CASCADE` on the owning assessment, same pattern as `SolarCalculationSnapshot`
and `TariffCalculationSnapshot`).

## Wind Engine (Phase 7)

`POST /api/v1/wind/calculate` estimates annual generation for candidate
0.5 / 1 / 2 / 3 / 5 / 10 kW turbines from the Phase 3 wind resource
(NASA POWER 2001-2020 climatology, m/s, 10 m reading used, 50 m shown only),
a generic reference power curve and a Rayleigh speed distribution. Assumptions
are versioned (`wind-assumptions-2026.1`); results are snapshotted to
`wind_calculation_snapshots`. No wind resource -> `wind_resource_unavailable`,
never a default speed. **Technical screening only — structural/site approval is
required. This is a preliminary software screening model, not a certified wind
resource assessment or structural/site engineering assessment.** No cost,
subsidy, savings or payback. Full method, curve, thresholds and limitations:
[docs/wind-engine.md](docs/wind-engine.md).

## SHREA AI (branding, AI Advisor, monitoring UI)

The user-facing brand is **SHREA AI** (the repository keeps its descriptive name).

**AI Advisor (Phase 8).** `POST /api/v1/advisor/chat` answers questions about one assessment.
The backend builds the context itself from the existing Solar, Wind, Tariff and Incentive
services and sends it, with a fixed system prompt, to NVIDIA NIM (Nemotron). The API key
(`NVIDIA_API_KEY`) is backend-only; without it the chat says "SHREA AI isn't connected yet".
**SHREA AI explains application results but does not replace the deterministic
renewable-energy calculation engines**, and it never invents tariffs, incentives, wind or solar
values, costs, savings or live readings. Details, limits and cost controls:
[docs/ai-advisor.md](docs/ai-advisor.md).

**Bill-first input (Phase 10.5).** Customers enter their average monthly electricity bill (rupees), not kWh. The kWh the
engines need is an estimate derived by inverting the verified tariff with the existing Tariff Engine (never a bill / rate
division), or the optional units the customer enters. Estimates are labelled, and unavailable when no verified tariff exists.
See [docs/bill-first-assessment.md](docs/bill-first-assessment.md).

**Recommendation (Phase 10).** `GET /api/v1/recommendations/{id}` picks a technology and size with deterministic rules over the
existing engines' outputs (smallest technically feasible solar size that reaches the 100% annual coverage target; wind only when
its screening is feasible; no hybrid or battery; cost, savings and payback come from the Phase 11 financial analysis). The dashboard shows it, and SHREA AI explains it without
choosing anything itself. See [docs/ai-advisor.md](docs/ai-advisor.md).

**Financial analysis (Phase 11).** `GET /api/v1/financial-analysis/{id}` returns an estimated gross cost (the official MNRE benchmark for the
exact recommended capacity), the verified incentive, net investment, savings (the Tariff Engine applied month by month to the solar offset)
and simple payback. It is deterministic, never calls an AI, and leaves anything unsupported unavailable. Export income and financing are not
modelled. See [docs/financial-analysis.md](docs/financial-analysis.md).

**Voice (Phase 9).** The chat has an opt-in microphone: speech is turned into text for the same advisor
request, and replies are spoken back with the browser's speech synthesis. It is an input/output layer only;
see the voice section of the same document. Frontend logic tests: `npm test` in `frontend/`.

**Monitoring.** `/monitoring` and the homepage "Monitor Your Existing Renewable System" section
have no device integration or telemetry store: they show an honest "No monitoring system
connected" state, and the homepage dashboard is an explicitly labelled **UI Preview** with
example values.

## Security Notes (Phases 2-6)

- No authentication yet. `app/services/prototype_user.py` centralizes a
  single well-known prototype user id so no user id is hard-coded elsewhere
  in the app — this must be replaced by real auth in a future phase.
- All input is validated by Pydantic (types, ranges, enum membership) before
  it reaches the database.
- SQLAlchemy's query builder is used throughout — no raw/interpolated SQL.
- Unhandled exceptions return a generic `{"detail": "Internal server error"}`
  (see the exception handler in `app/main.py`) instead of leaking tracebacks.
- All credentials come from environment variables (`.env`, gitignored) —
  never hard-coded.
- No provider API key is committed or required by default (Phase 3's
  providers are all keyless). If you configure a commercial provider that
  needs one, it goes in `.env` like every other secret here.
- The map (`components/location/LocationMap.tsx`) uses OpenStreetMap tiles
  directly — no API key, no token exposed to the client.

## Current Development Phase

**CURRENT PHASE: Phase 7 — India-Based Wind Engine, complete** (see
[Wind Engine (Phase 7)](#wind-engine-phase-7); the Phase 6 description below is
unchanged, except that wind *technical screening* now exists — no
hybrid/battery, recommendation, or financial engine yet)

**Phase 6 — India Renewable Energy Incentive Engine**

Phase 1 established the monorepo, frontend UI, and backend foundation.
Phase 2 turned the assessment UI into a real backend-backed system with
PostgreSQL persistence. Phase 3 added a provider-agnostic location
intelligence layer: real geocoding, solar/wind/weather/elevation data from
free keyless providers, a map, and resource cards on both the standalone
Location page and the assessment Dashboard. An India-based architecture
update between Phase 3 and Phase 4 added India location resolution
(state/UT/district/city/DISCOM — see
[India location resolution](#india-location-resolution)) and the
tariff/incentive schema (see
[India-Based Tariff & Incentive Architecture](#india-based-tariff--incentive-architecture)).
Phase 4 estimated technical solar generation and system feasibility for an
assessment (see [Solar Engine (Phase 4)](#solar-engine-phase-4)). Phase 5
estimated a baseline grid-electricity bill from an assessment's consumption
and location/DISCOM data (see
[Electricity Tariff Engine (Phase 5)](#electricity-tariff-engine-phase-5)).

**Phase 6 evaluates which renewable-energy incentive programmes an
assessment may be eligible for, and calculates the amount when a
programme's documented formula and this app's own data allow it (see
[Incentive Engine (Phase 6)](#incentive-engine-phase-6)). It does NOT
calculate final installation cost, final savings, payback, or ROI** — and,
per this project's own investigation record, **no central or state
incentive scheme has yet been confidently verified from an official
source**, so every location currently reports an empty, honest
`programmes` list in practice (the architecture, eligibility engine,
calculation engine, and stacking rules are complete and tested; the data
is honestly absent — see
[`backend/app/data/incentives/india/README.md`](backend/app/data/incentives/india/README.md)).
No wind/hybrid/battery calculation, recommendation engine, financial
engine, AI, voice, or ML is implemented yet.

## Future Roadmap

- Phase 1 — Foundation
- Phase 2 — User Assessment + Database
- Phase 3 — Location Intelligence
- *(India-based architecture update — DISCOM/tariff/incentive data model)*
- Phase 4 — India-Based Solar Engine ✅
- Phase 5 — India Electricity Tariff Engine ✅
- Phase 6 — India Renewable Energy Incentive Engine ✅
- Phase 7 — India-Based Wind Engine ✅
- Phase 8 — Hybrid + Battery
- Phase 9 — Recommendation Engine
- Phase 10 — Financial Engine
- Phase 11 — AI Advisor
- Phase 12 — Voice Advisor
- Phase 13 — Electricity Bill Intelligence
- Phase 14 — ML Prediction
- Phase 15 — Reports
- Phase 16 — Testing + Deployment
