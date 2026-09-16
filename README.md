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
 +--> AI ADVISOR (future) --> structured requests --> engines --> explanation
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
│   │   ├── api/v1/routes/         health.py, assessments.py, locations.py
│   │   ├── core/                    config.py, security.py, constants.py,
│   │   │                              india_geography.py (static states/UTs list)
│   │   ├── database/
│   │   │   ├── connection.py          SQLAlchemy engine, session factory, Base
│   │   │   └── repositories/            assessment_repository.py,
│   │   │                                  location_resource_snapshot_repository.py,
│   │   │                                  discom_repository.py
│   │   ├── models/                   User, Building, Location, EnergyProfile,
│   │   │                                BuildingConstraints, Assessment,
│   │   │                                LocationResourceSnapshot, Discom,
│   │   │                                ElectricityTariff, IncentiveProgram, enums.py
│   │   ├── schemas/                   assessment.py, location.py
│   │   ├── services/
│   │   │   ├── assessment_service.py    Assessment persistence orchestration
│   │   │   ├── prototype_user.py         Centralized prototype-user resolution
│   │   │   ├── location/                  LocationService, cache, provider_factory,
│   │   │   │                                dependencies.py, providers/ (Phase 3),
│   │   │   │                                india_resolver.py (India architecture update)
│   │   │   ├── ai/                        AIAdvisorService interface (Phase 10)
│   │   │   └── voice/                      Speech-to-text / text-to-speech / voice advisor interfaces (Phase 11)
│   │   ├── engines/
│   │   │   ├── solar/                   Phase 4
│   │   │   ├── wind/                     Phase 5
│   │   │   ├── hybrid/                    Phase 6
│   │   │   ├── financial/                  Phase 8
│   │   │   └── recommendation/              Phase 7
│   │   └── ml/                             Prediction models (Phase 13)
│   ├── alembic/                    Database migrations (versions/, env.py)
│   └── tests/
│
├── docs/                          Reserved for future architecture/API docs
├── .env.example
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

This starts PostgreSQL, the backend (`http://localhost:8000`), and the
frontend dev server (`http://localhost:5173`). Stop everything with
`docker compose down` (add `-v` to also remove the PostgreSQL data volume).

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

Discom (id, name, short_code, state, union_territory, is_active)

ElectricityTariff (state, union_territory, discom_id, consumer_category,
                    tariff_name, slab_min_kwh, slab_max_kwh,
                    energy_charge_inr_per_kwh, fixed_charge_inr, demand_charge_inr,
                    effective_from, effective_to, source_url, source_document,
                    last_verified, active)

IncentiveProgram (scheme_name, level, state, union_territory, discom_id,
                   consumer_category, technology, min_system_size_kw, max_system_size_kw,
                   subsidy_type, subsidy_value, percentage_value, maximum_amount,
                   eligibility_rules, effective_from, effective_to, source_url,
                   source_document, last_verified, active)
```

- `building_type` (also used as `consumer_category` on tariffs/incentives):
  `home` | `school` | `college` | `office` | `shop` | `small_institution` | `other`
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
  tariff/incentive architecture added to prepare for the Solar Engine —
  see [India-Based Tariff & Incentive Architecture](#india-based-tariff--incentive-architecture)
  below. **No production rows are seeded in any of the three** — populating
  real tariff orders and scheme data, and the engine that resolves a user's
  exact tariff/incentives, are future work.

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

Prepares the data model the future India-Based Solar Engine (Phase 4) and
Financial Engine will read from — **no calculation engine exists yet**, and
**no production tariff or subsidy rows are seeded**. This section is
data-model preparation, not a working tariff/incentive resolver.

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
(nullable FK to `Discom`), `consumer_category` (the same `BuildingType`
enum used by assessments — home/school/**college**/office/shop/
small_institution/other), `tariff_name`, `slab_min_kwh`/`slab_max_kwh`,
`energy_charge_inr_per_kwh`, `fixed_charge_inr`, `demand_charge_inr`,
plus the versioning/source fields below. The table is empty in production;
only `tests/test_tariff_and_incentive_models.py`'s clearly-named `TEST-*`
fixtures ever populate it. **No tariff calculation/resolution engine is
implemented yet** — that's future work once real tariff orders are loaded.

### Incentive architecture (`app/models/incentive_program.py`)

One row per scheme. `level` separates **central** / **state** / **discom**
schemes — they are never combined into one number. `consumer_category` is
nullable (a scheme can be category-agnostic) but a future matching engine
must treat `null` as "check `eligibility_rules`", never as "applies to
everyone" — this is exactly what stops a residential central subsidy (e.g.
PM Surya Ghar) from being silently applied to a school, college, or office.
`technology` (solar/wind/hybrid/battery/other), `subsidy_type`
(percentage/fixed_amount/per_kw/other) with `subsidy_value` (generic,
meaning depends on `subsidy_type`), `percentage_value` +
`maximum_amount` (for a capped percentage scheme), `min_system_size_kw` /
`max_system_size_kw`, and a JSON `eligibility_rules` field for conditions
that don't fit a column. The table is empty in production, same as
tariffs.

The architecture supports every case the eligibility rules require: a
central-only scheme with no state top-up, a state scheme with no DISCOM
rule, multiple simultaneously-applicable schemes (multiple rows), no
additional incentive for a given state (simply no row), an expired scheme
(`active=false`, `effective_to` in the past), and "eligibility unknown"
(no row matches — the honest absence of data, not a guess).

### Data versioning & source traceability

Both `ElectricityTariff` and `IncentiveProgram` carry the same versioning
fields: `effective_from`, `effective_to`, `last_verified`, `source_url`,
`source_document`, `active`. A future engine must resolve the record valid
on the assessment's date and must never use an expired record when an
active one exists — this schema makes that check possible; it doesn't
perform it yet. The frontend can eventually show, for any tariff or
incentive: `Source: <source_document / source_url>`,
`Last verified: <last_verified>`, `Effective: <effective_from> – <effective_to or "ongoing">`.
No fake source URLs or verification dates are ever stored — an
unpopulated record simply doesn't exist yet.

### DISCOM registry (`app/models/discom.py`)

A simple, empty-by-default registry: `name`, `short_code`, `state` /
`union_territory` (exactly one expected per row), `is_active`. Real DISCOM
boundary data (which DISCOM serves which district/city) is out of scope
for this update — populating it from an authoritative source (each state's
electricity regulatory commission) is future work.

## Security Notes (Phase 2 & 3)

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

**CURRENT STATUS: Phase 3 — Location Intelligence, complete, plus the
India-Based Architecture Update (data-model preparation for Phase 4)**

Phase 1 established the monorepo, frontend UI, and backend foundation.
Phase 2 turned the assessment UI into a real backend-backed system with
PostgreSQL persistence. Phase 3 added a provider-agnostic location
intelligence layer: real geocoding, solar/wind/weather/elevation data from
free keyless providers, a map, and resource cards on both the standalone
Location page and the assessment Dashboard (using the assessment's saved
coordinates). See [Location Intelligence](#location-intelligence-phase-3)
above for that architecture.

Between Phase 3 and Phase 4, an **India-based architecture update** added
the data-model groundwork the India-Based Solar Engine will need: India
location resolution (state/UT/district/city/DISCOM — see
[India location resolution](#india-location-resolution)), and the
tariff/incentive schema (see
[India-Based Tariff & Incentive Architecture](#india-based-tariff--incentive-architecture)).
This is architecture preparation only — no solar/wind sizing, cost,
tariff/subsidy calculation, recommendation, AI, or voice behavior are
implemented yet.

## Future Roadmap

- Phase 1 — Foundation
- Phase 2 — User Assessment + Database
- Phase 3 — Location Intelligence
- *(India-based architecture update — DISCOM/tariff/incentive data model)*
- Phase 4 — India-Based Solar Engine
- Phase 5 — Wind Engine
- Phase 6 — Hybrid + Battery
- Phase 7 — Recommendation Engine
- Phase 8 — Financial + Subsidy Engine
- Phase 9 — Dashboard
- Phase 10 — AI Advisor
- Phase 11 — Voice Advisor
- Phase 12 — Electricity Bill Intelligence
- Phase 13 — ML Prediction
- Phase 14 — PDF Reports
- Phase 15 — Testing + Security
- Phase 16 — Deployment
