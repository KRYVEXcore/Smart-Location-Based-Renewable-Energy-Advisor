# Smart Location-Based Renewable Energy Advisor

A location-aware decision-support platform that helps individuals and small
institutions evaluate renewable energy options — Solar PV, Small Wind,
Solar+Wind Hybrid, Battery Storage, and combinations of these — based on
their own location, building, energy needs, and budget.

## Project Purpose

Choosing a renewable energy system is hard to do well without site-specific
data: local solar and wind resource, roof or land area, consumption
patterns, installation cost, and available incentives all matter. This
platform's goal is to turn that information into a clear, explainable
recommendation — sized and costed by deterministic engineering calculations,
never guessed by an AI model.

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
│   │   ├── core/                    config.py, security.py, constants.py
│   │   ├── database/
│   │   │   ├── connection.py          SQLAlchemy engine, session factory, Base
│   │   │   └── repositories/            assessment_repository.py,
│   │   │                                  location_resource_snapshot_repository.py
│   │   ├── models/                   User, Building, Location, EnergyProfile,
│   │   │                                BuildingConstraints, Assessment,
│   │   │                                LocationResourceSnapshot, enums.py
│   │   ├── schemas/                   assessment.py, location.py
│   │   ├── services/
│   │   │   ├── assessment_service.py    Assessment persistence orchestration
│   │   │   ├── prototype_user.py         Centralized prototype-user resolution
│   │   │   ├── location/                  LocationService, cache, provider_factory,
│   │   │   │                                dependencies.py, providers/ (Phase 3)
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
```

- `building_type`: `home` | `school` | `office` | `shop` | `small_institution` | `other`
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
| GET    | `/locations/profile`    | Normalized solar/wind/weather/elevation data for a coordinate (`?latitude=...&longitude=...`) |

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

**CURRENT PHASE: Phase 3 — Location Intelligence**

Phase 1 established the monorepo, frontend UI, and backend foundation.
Phase 2 turned the assessment UI into a real backend-backed system with
PostgreSQL persistence. Phase 3 adds a provider-agnostic location
intelligence layer: real geocoding, solar/wind/weather/elevation data from
free keyless providers, a map, and resource cards on both the standalone
Location page and the assessment Dashboard (using the assessment's saved
coordinates). See [Location Intelligence](#location-intelligence-phase-3)
above for the architecture. No solar/wind sizing, cost, subsidy,
recommendation, AI, or voice behavior are implemented yet — Phase 3 only
retrieves and normalizes resource data.

## Future Roadmap

- Phase 1 — Foundation
- Phase 2 — User Assessment + Database
- Phase 3 — Location Intelligence
- Phase 4 — Solar Engine
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
