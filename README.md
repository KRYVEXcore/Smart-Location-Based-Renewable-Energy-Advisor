# SHREA — Smart Location-Based Renewable Energy Advisor

**An India-specific decision-support platform that turns a location and an average monthly electricity bill into a verified, explainable renewable-energy recommendation.** The user-facing brand is **SHREA AI**; the repository keeps its descriptive name.

> **Deterministic engines calculate. AI explains.**

Built for the **Smart India Hackathon (SIH) 2026**.

| | |
| --- | --- |
| **Live app** | <https://kryvexcore.github.io/Smart-Location-Based-Renewable-Energy-Advisor/> (GitHub Pages) |
| **Live API** | <https://renewable-energy-advisor-api.onrender.com> (Render) — health check: `/api/v1/health` |
| **Documentation** | [`docs/`](docs/) — see [Documentation](#documentation) |
| **License** | GNU AGPL v3 — see [`LICENSE`](LICENSE) |

> The API runs on Render's free plan and sleeps when idle, so the first request after a pause can be slow.

## Contents

[Purpose](#purpose) · [Key Features](#key-features) · [Architecture](#architecture) · [How a Result Is Produced](#how-a-result-is-produced) · [Engines](#engines) · [SHREA AI Advisor](#shrea-ai-advisor) · [Voice](#voice) · [Financial Analysis](#financial-analysis) · [Data Coverage & Provenance](#data-coverage--provenance) · [Technology Stack](#technology-stack) · [Current Status](#current-status) · [Known Limitations](#known-limitations) · [Planned Work](#planned-work-not-implemented) · [Repository Structure](#repository-structure) · [Getting Started](#getting-started) · [Deployment](#deployment) · [Database Models](#database-models) · [API Endpoints](#api-endpoints) · [Engine & Data Reference](#location-intelligence-phase-3) · [Security](#security) · [Documentation](#documentation)

---

## Purpose

Choosing a renewable-energy system is hard to do well without site-specific data. In India almost everything that matters is local: solar and wind resource vary by region, electricity tariffs are set per state/UT and per DISCOM, and incentive schemes exist at the central, state/UT and DISCOM level, each with its own eligibility rules. Most customers also know what they *pay* (their monthly bill), not what they *use* (kWh).

SHREA turns India-based location and resource data into a clear, explainable recommendation that is **sized and costed by deterministic calculations and verified, dated, sourced data — never guessed by an AI model**, and never a single nationwide number applied everywhere.

### SIH purpose

SHREA was built for the Smart India Hackathon 2026 as a working, auditable prototype that shows:

- **A customer-friendly input** — location, building type and average monthly *bill*, with optional units.
- **India-specific accuracy** — state/UT → DISCOM → the tariff, incentives and renewable resource that apply there.
- **Explainability** — every recommendation carries its reason, rules, limitations and data sources.
- **A safe use of AI** — the AI receives validated results from the backend and explains them. It does not invent capacity, tariff, incentive, cost, savings or payback.
- **Safe failure** — missing data becomes a status and a reason ("Not available"), never a guess and never a fake zero.
- **Access for everyone** — a browser and internet only, by text or voice.

## Key Features

- **Bill-first assessment** — a five-step wizard (Location → Building type → Electricity bill → Constraints → Review). The kWh the engines need is *estimated from the bill* with the verified tariff, or entered directly.
- **Location intelligence** — place search and map, reverse geocoding, resolution to state/UT, district/city and DISCOM, plus solar, wind, weather and elevation data.
- **Deterministic engines** — solar generation and feasibility (1–10 kW), small-wind screening (0.5–10 kW), electricity tariff bill, incentive eligibility, recommendation, and financial analysis.
- **Recommendation** — the smallest technically feasible solar size that reaches the annual-coverage target, with reasons and the options that were excluded.
- **Estimated financials** — cost (official MNRE benchmark), verified incentive, net investment, savings and simple payback, labelled as estimates.
- **Verified data with provenance** — tariffs, incentives and cost data carry source, page, version and effective dates, shown in the dashboard.
- **SHREA AI chat** — questions about one assessment, answered from the backend's results (NVIDIA NIM).
- **Voice** — optional browser microphone and spoken replies on top of the same chat.
- **Responsive UI** — React app for desktop and mobile.

## Architecture

```
CUSTOMER (any browser)
   │  HTTPS
   ▼
FRONTEND   React + TypeScript + Vite ................ GitHub Pages
   │  REST / JSON
   ▼
BACKEND    FastAPI ................................... Render (Docker)
   ├─ Services    assessment · location intelligence · bill estimation
   │              recommendation · financial analysis · advisor context
   ├─ Engines     solar · wind · tariff · incentive · recommendation · financial   (pure calculation)
   ├─ PostgreSQL  assessments · verified DISCOMs / tariffs / incentives · snapshots (SQLAlchemy + Alembic)
   ├─ Data        Nominatim · NASA POWER · Open-Elevation   (called by the location service only)
   └─ SHREA AI    NVIDIA NIM — receives engine results, explains them
```

| Layer | What it contains |
| --- | --- |
| 1. Customer / presentation | React app: assessment wizard, dashboard/report, recommendation card, advisor chat, browser voice |
| 2. API / application | FastAPI REST API under `/api/v1`, Pydantic validation, thin routes and orchestrating services |
| 3. Deterministic engines | Pure-Python calculation in `backend/app/engines/` — no database, no HTTP, no AI |
| 4. AI / conversational | SHREA AI advisor: context builder, prompt rules, NVIDIA NIM adapter, reply validation, rate limits |
| 5. Data | PostgreSQL: assessment inputs, verified reference data (DISCOM, tariff, incentive), calculation snapshots |
| 6. External data | Nominatim, NASA POWER, Open-Elevation (keyless); NVIDIA NIM is the AI provider, not a data source |

**Architecture principles**

1. **Engines calculate, AI explains.** The model never sees the database, never calls a provider and has no tools. It receives a context built by the backend from the engines' outputs.
2. **Engines are pure.** They import no FastAPI, SQLAlchemy or HTTP client. Services fetch data and hand the engines plain values, so the same inputs always give the same output.
3. **Engines never call a data provider.** The location service fetches and normalises resource data first.
4. **Time-sensitive data is versioned.** Tariffs, incentives and cost data have effective dates and sources; the version valid on the calculation date is chosen deterministically.
5. **No layer invents another layer's value.** Missing data is reported with a status and reason.

## How a Result Is Produced

1. The customer enters **location, building type, monthly bill, roof area and constraints** (optionally units). The assessment is saved in PostgreSQL.
2. The location is resolved to **state/UT → district/city → DISCOM** (a DISCOM is never guessed) and the solar and wind resource is retrieved.
3. **Bill → kWh:** the existing Tariff Engine is evaluated at candidate consumptions until the modelled bill matches the entered bill (bounded bisection). This is *not* "bill ÷ a rate", and the result is labelled an estimate, not a meter reading. With no verified tariff, consumption stays unknown and the reason is recorded.
4. The **Solar** and **Wind** engines produce technical options; the **Tariff Engine** produces the baseline bill.
5. The **Recommendation Engine** picks a technology and size; the **Incentive Engine** is asked for that exact system.
6. The **Financial Analysis Engine** estimates cost, net investment, savings and payback — or reports what is unavailable.
7. The dashboard shows the results; **SHREA AI** explains them in text or voice.

Example (Chennai home, ₹7,500/month bill, 1,200 sq ft roof — a live run on 20 Sep 2026; estimates, not guarantees):

| Step | Result |
| --- | --- |
| Bill → consumption | ≈ 799.4 kWh/month (≈ 9,592.8 kWh/year), TNPDCL tariff |
| Recommendation | Solar **7 kW**, ≈ 10,007.4 kWh/year, 104.3 % annual coverage (wind: insufficient resource) |
| Cost / incentive / net | ₹3,25,000 (MNRE benchmark) − ₹78,000 (PM Surya Ghar) = ₹2,47,000 |
| Savings / payback | ≈ ₹88,486 per year (≈ ₹7,374 per month) · simple payback ≈ 2.8 years |

## Engines

| Engine | Purpose | Data source | Code |
| --- | --- | --- | --- |
| Location intelligence | Map point → state/UT, district/city, DISCOM status, solar/wind/weather/elevation | Nominatim, NASA POWER, Open-Elevation, DISCOM registry | `services/location/` |
| Bill / consumption estimator | Monthly bill → estimated kWh using the verified tariff | Verified tariff rows | `engines/tariff/bill_estimation.py` |
| Solar | Annual/monthly generation and roof feasibility for 1–10 kW | NASA POWER `ALLSKY_SFC_SW_DWN` | `engines/solar/` |
| Wind | Screening of 0.5–10 kW turbines: feasible / marginal / insufficient | NASA POWER wind climatology | `engines/wind/` |
| Tariff | Estimated baseline grid bill (slabs, fixed charges, version by date) | `electricity_tariffs` table | `engines/tariff/` |
| Incentive | Which verified schemes apply to a system, and the amount | `incentive_programs` table | `engines/incentive/` |
| Recommendation | Technology and size, with reasons and excluded options | Outputs of the engines above | `engines/recommendation/` |
| Financial analysis | Estimated cost, net investment, savings, simple payback | MNRE cost dataset + incentive + tariff + solar output | `engines/financial/` |

What the engines **do not** decide: the Solar and Wind engines choose no size; the Tariff engine applies no subsidy; the Incentive engine never sums schemes; the Recommendation engine never offers hybrid or battery systems (no engine exists for them).

### Recommendation rules

1. Options that are technically infeasible (for example the roof is too small), or cannot be checked (roof area missing), are excluded.
2. Wind is considered only when its screening is feasible; insufficient or marginal wind is excluded.
3. Solar: choose the **smallest** technically feasible size whose annual coverage reaches the target (`TARGET_ANNUAL_COVERAGE_PERCENT = 100`).
4. If none reaches it, choose the largest feasible size and say the target is not met.
5. Solar is preferred to wind; wind is recommended only when no solar size is feasible.
6. Hybrid and battery are never recommended.

Statuses: `recommended`, `no_suitable_option`, `insufficient_data`. Nothing is guessed — an unknown roof area gives `insufficient_data`.

## SHREA AI Advisor

`POST /api/v1/advisor/chat` answers questions about **one assessment**. The advisor is an explanation layer.

- **Provider:** NVIDIA NIM (OpenAI-compatible API) through one adapter; configured model `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`.
- **Context:** built on the server from the assessment and the engines' results (solar, wind, tariff, incentives, recommendation, financial analysis). Street address, coordinates and credentials are excluded. A section that cannot be produced is marked unavailable, not guessed.
- **Prompt rules:** the bill comes first; numbers in the data are authoritative and must not be recalculated; no derived figures; the recommendation is explained, never chosen; financial figures are quoted exactly and called *estimated*; no live monitoring; user messages are untrusted.
- **Safeguards:** replies must be non-empty, are rejected if they contain the API key, have `<think>` blocks removed and are capped at 4,000 characters. Message ≤ 1,000 characters; the last 6 history turns are sent; 10 requests/minute per assessment and 30/minute overall (in-memory limiter, per process); 800 output tokens; 30 s timeout.
- **Failure handling:** a single retry on HTTP 503 only; other provider failures return a safe status and code (`rate_limited`, `auth_failed`, `provider_error`, `invalid_response`, `timeout`, `network_error`) without provider bodies or headers. With no `NVIDIA_API_KEY` the chat reports it is not connected. The deterministic dashboard never depends on the AI.
- **Isolation:** context is built per assessment id and access is checked against the current (prototype) user. Logs contain provider, model, assessment id, outcome and latency only.
- **The key is backend-only** — set as `NVIDIA_API_KEY` on the server; never in the frontend, GitHub Pages variables or Git.

`GET /api/v1/advisor/overview/{id}` returns the assessment summary and suggested questions **without any AI call**, as do the recommendation and financial-analysis endpoints. Details: [`docs/ai-advisor.md`](docs/ai-advisor.md).

## Voice

Voice is an **input/output layer in the browser** around the same advisor chat. There is no separate backend voice service.

- Microphone → browser `SpeechRecognition` / `webkitSpeechRecognition` (`en-IN`) → final text → the normal chat request → reply → browser `speechSynthesis` (an English/India voice is preferred).
- States: `idle`, `requesting_permission`, `listening`, `processing`, `speaking`, `stopped`, `unsupported`, `error`.
- Exactly **one** advisor request per finished utterance; interim results are never sent; listening starts only when the user taps and ends on silence, error or Stop. Tapping the microphone while SHREA speaks interrupts the speech.
- Speech problems (unsupported browser, denied permission, playback failure) never break the text chat.
- **Privacy:** SHREA does not record, store or upload audio; it receives text only. The browser's own recognition service may process audio (in Chrome and Edge this is a cloud service). Behaviour depends on the browser and device; real-device behaviour needs manual testing.

The backend's `services/voice/` contains only empty interfaces and is not used.

## Financial Analysis

`GET /api/v1/financial-analysis/{assessment_id}` (deterministic, never calls an AI) returns, when supported:

| Output | Method |
| --- | --- |
| Gross cost | Official MNRE PM Surya Ghar **benchmark** for the exact recommended capacity: ₹50,000/kW for the first 2 kW and ₹45,000/kW after (special-category States/UTs ₹55,000 / ₹49,500). Residential systems only; a benchmark, not a market quote |
| Incentive | The Incentive Engine's verified result for that system; if several apply and combining them is unverified, only the largest is used |
| Net investment | Gross cost − incentive, never below zero; a range stays a range |
| Savings | Per month, the Tariff Engine bill for the consumption minus the bill after the solar offset (capped at what is used); surplus/export is **not** valued; not "bill ÷ kWh" |
| Simple payback | Net investment ÷ annual savings, only when both exist and savings are above zero |

Statuses: `complete`, `cost_unavailable`, `savings_unavailable`, `insufficient_data`, `not_applicable`. A value that cannot be supported is `null` and shown as **"Not available"** — never zero.

All figures are **estimates, not guarantees**. Excluded: export/net-metering income, financing/EMI, tariff escalation, maintenance savings, tax benefits, panel degradation, government bill subsidies, demand and time-of-day charges. The recommendation's `cost_context` is filled from the same result. Details: [`docs/financial-analysis.md`](docs/financial-analysis.md).

## Data Coverage & Provenance

Standing rule: **real data > no data > fake data.** A value is only loaded once it was read from a primary official document, with the page/table recorded. Where SHREA has no verified data, it says so.

| Data | Verified and loaded |
| --- | --- |
| Residential electricity tariffs | Tamil Nadu (TNPDCL), Andhra Pradesh, Karnataka, Maharashtra (MSEDCL), Rajasthan. Maharashtra locations resolve as DISCOM-*ambiguous* (several licensees), so no tariff is guessed. Every other State/UT reports `tariff_not_configured`. Kerala was verified but is not loaded (its billing cannot be represented by the engine) |
| DISCOM registry | TNPDCL, MSEDCL, BEST, AEML-D, TPC-D |
| Incentives | Central **PM Surya Ghar** CFA — standard and special-category rows, residential only. No state or DISCOM scheme is verified |
| Installed cost | MNRE PM Surya Ghar benchmark (guideline p. 8, clause g) — residential only |
| Non-residential tariffs | Not verified |

Every tariff and incentive row carries `source_name`, `source_url`, `source_document`, `source_order_number/date`, `source_page`, `source_table`, `source_section`, `source_excerpt`, `verification_status`, `verification_notes`, `last_verified`, `effective_from`/`effective_to`. The cost dataset records the same kind of provenance, plus scope, inclusions, exclusions and GST treatment ("not stated" where the source does not say). Research log and coverage: [`docs/data-verification/`](docs/data-verification/).

Data is loaded from JSON files in `backend/app/data/` by `python -m scripts.seed_all` (validates first; idempotent; never deletes).

## Technology Stack

| Area | Technologies |
| --- | --- |
| Frontend | React 19, TypeScript, Vite 8, Tailwind CSS 4, React Router 7, Leaflet / react-leaflet (OpenStreetMap tiles), Lucide icons, browser Web Speech APIs |
| Backend | Python (Docker image: 3.12), FastAPI, Uvicorn, Pydantic v2 + pydantic-settings, SQLAlchemy 2, Alembic, psycopg2, httpx |
| Database | PostgreSQL (Render managed database in production; `postgres:16-alpine` in Docker Compose) |
| AI | NVIDIA NIM (OpenAI-compatible API), model `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` |
| Data sources | NASA POWER, Nominatim (OpenStreetMap), Open-Elevation, OpenStreetMap tiles; official tariff orders and MNRE guidelines as verified JSON |
| Deployment | GitHub Pages (GitHub Actions), Render (Docker web service + PostgreSQL), Docker Compose and a devcontainer for local development |
| Testing / tooling | pytest (in-memory SQLite), Node's built-in test runner, oxlint, `tsc` |

## Current Status

Status as of 20 September 2026.

| Area | Status |
| --- | --- |
| Foundation, assessment + PostgreSQL persistence (Phases 1–2) | Done, deployed |
| Location intelligence and India resolution (Phase 3) | Done, deployed |
| Solar, Tariff and Incentive engines (Phases 4–6) with verified data (Phase 6.7) | Done, deployed |
| Wind screening engine (Phase 7) | Done, deployed |
| SHREA AI advisor (Phase 8) | Done, deployed |
| Voice (Phase 9) | Done, deployed (browser) |
| Recommendation Engine (Phase 10) and bill-first input (Phase 10.5) | Done, deployed |
| Financial Analysis Engine (Phase 11) | Deployed; API and advisor answers verified against the live system. **Pending:** visual check of the financial section of the dashboard on GitHub Pages |
| Monitoring page | UI only — no device or telemetry integration |
| Hybrid + battery, bill intelligence, ML prediction, reports, real authentication | **Planned** — not implemented |

Test suites at the last full run: **717** backend tests (`pytest`) and **87** frontend tests (`npm test`); `tsc`, lint and production build are clean.

## Known Limitations

- **Tariff coverage:** verified residential tariffs for five states only; non-residential categories and other states/UTs are unverified. Where absent, SHREA says so.
- **Incentives:** only the central PM Surya Ghar scheme is verified; no state or DISCOM scheme is loaded.
- **Wind** is a screening from regional climatology (10 m speed, generic reference turbine), not a site measurement or a structural assessment.
- **Cost** is an MNRE benchmark, not a market quotation; the guideline does not state inclusions or GST treatment; it is residential-only, and its per-kW rates are applied beyond the 3 kW subsidy cap.
- **Savings and payback** are estimates: export/net-metering income, financing, escalation, degradation and government bill subsidies are not modelled; consumption is treated as the same every month.
- **Bill → kWh** ignores taxes, duty, surcharges, demand and time-of-day charges, per-kW fixed charges, and bill subsidies.
- **No user authentication.** Every request is a single prototype user; an assessment is reached by its unguessable id, and the assessment-list endpoint is unauthenticated.
- **AI** replies depend on NVIDIA's availability; the advisor rate limiter is per process (fits one Render instance).
- **Voice** depends on the browser and device.
- Recommendation and financial results are recomputed on every request (only inputs and engine snapshots are stored).
- Render's free plan sleeps when idle and its free database has a time limit.

## Planned Work (not implemented)

Hybrid solar + wind and battery sizing (`engines/hybrid` is a placeholder) · financing/EMI and export compensation · electricity-bill intelligence · ML prediction (`app/ml` is a placeholder) · downloadable reports · device monitoring and live telemetry · real authentication · more verified states, categories and state/DISCOM incentives · server-side speech services (empty interfaces exist).

---

## Repository Structure

```
renewable-energy-advisor/
├── frontend/                      React + TypeScript + Vite + Tailwind + React Router
│   ├── src/
│   │   ├── pages/                   Home, Assessment, Dashboard, Location, Monitoring, Advisor
│   │   ├── components/              assessment/ recommendation/ solar/ wind/ tariff/ incentive/
│   │   │                              location/ advisor/ monitoring/ common/ cards/ metrics/
│   │   │                              navigation/ buttons/ layout/ (Footer) visualizations/
│   │   ├── hooks/                   One hook per API call, plus voice and advisor hooks
│   │   ├── services/                apiClient.ts and typed service calls per API group
│   │   ├── voice/                   speech.ts, voiceController.ts, speechOutput.ts, browserSpeech.ts
│   │   ├── utils/                   richText.ts (safe **bold**), reportView.ts, recommendationView.ts
│   │   ├── types/  layouts/  assets/
│   ├── tests/                     Node test runner (voice, rich text, bill-first, cost, financial)
│   └── .env.example
│
├── backend/                       FastAPI application
│   ├── app/
│   │   ├── main.py                  App, CORS, generic error handler, router wiring
│   │   ├── api/v1/routes/           health, assessments, locations, solar, wind, tariffs,
│   │   │                              incentives, recommendations, financial, advisor
│   │   ├── core/                    config.py, constants.py, india_geography.py, security.py (placeholder)
│   │   ├── database/                connection.py, repositories/
│   │   ├── models/                  14 SQLAlchemy models + enums.py
│   │   ├── schemas/                 Pydantic request/response models
│   │   ├── services/                assessment, solar, wind, tariff, incentive, consumption estimation,
│   │   │                              recommendation (also runs financial analysis), advisor,
│   │   │                              location/ (providers, cache, India resolver), ai/ (context, prompt,
│   │   │                              NVIDIA provider, rate limiter), voice/ (empty interfaces)
│   │   ├── engines/                 solar/ wind/ tariff/ incentive/ recommendation/ financial/
│   │   │                              (hybrid/ is a placeholder)
│   │   ├── data/                    Verified JSON: costs/ discoms/ incentives/ tariffs/ (india/)
│   │   ├── data_validation/         Validation of the JSON data before it is loaded
│   │   └── ml/                      Placeholder
│   ├── alembic/                   9 migrations
│   ├── scripts/                   seed_all.py (+ seed_discoms/tariffs/incentives), data_quality_report.py
│   ├── tests/                     pytest suite
│   └── Dockerfile, docker-entrypoint.sh
│
├── docs/                          ai-advisor.md, bill-first-assessment.md, financial-analysis.md,
│                                    wind-engine.md, data-verification/
├── .github/workflows/deploy-pages.yml   Builds and publishes the frontend to GitHub Pages
├── render.yaml                    Render blueprint (backend web service + PostgreSQL)
├── docker-compose.yml, .devcontainer/   Local / Codespaces development
├── .env.example
└── README.md
```

## Getting Started

### Requirements

- Node.js 20+ and npm
- Python 3.11+ (the Docker image uses 3.12). On Windows the `python` launcher may not be configured — use `py`.
- PostgreSQL 14+ (or Docker, below)
- Docker and Docker Compose (optional)

### Installation

Clone the repository, then set up the backend and frontend as below, or run everything with Docker Compose.

### Environment Configuration

Copy [`.env.example`](.env.example) to `backend/.env` and adjust it. **Never commit a real `.env` file** — it is excluded by [`.gitignore`](.gitignore).

| Variable | Used by | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | backend | SQLAlchemy PostgreSQL connection string |
| `APP_ENV` | backend | `development` \| `staging` \| `production` |
| `SECRET_KEY` | backend | Reserved for future authentication/session signing |
| `CORS_ALLOWED_ORIGINS` | backend | Comma-separated allowed browser origins (default `http://localhost:5173`; production: the GitHub Pages origin) |
| `RUN_DATA_SEED` | backend (container) | `true` loads the verified data on container start (idempotent) |
| `NVIDIA_API_KEY` | backend | SHREA AI key. **Backend only.** Empty → the advisor reports "not connected" |
| `AI_PROVIDER` / `AI_MODEL` | backend | Default `nvidia` and `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` |
| `AI_BASE_URL`, `AI_TIMEOUT_SECONDS`, `AI_MAX_OUTPUT_TOKENS`, `AI_HISTORY_LIMIT`, `AI_RATE_LIMIT_PER_MINUTE`, `AI_GLOBAL_RATE_LIMIT_PER_MINUTE` | backend | Optional AI tuning (defaults: NVIDIA endpoint, 30 s, 800 tokens, 6 turns, 10/min per assessment, 30/min overall) |
| `GEOCODING_PROVIDER`, `SOLAR_RESOURCE_PROVIDER`, `WIND_RESOURCE_PROVIDER`, `WEATHER_PROVIDER`, `ELEVATION_PROVIDER` (+ `*_API_KEY`) | backend | Default `nominatim`, `nasa_power` (×3), `open_elevation`; all keyless and optional |
| `LOCATION_CACHE_TTL_SECONDS`, `PROVIDER_REQUEST_TIMEOUT_SECONDS` | backend | Optional (defaults 86,400 s and 10 s) |
| `VITE_API_BASE_URL` | frontend | Backend base URL, in `frontend/.env` (see [`frontend/.env.example`](frontend/.env.example)). In CI it comes from the `API_BASE_URL` repository variable |

None of the provider or AI variables is required to run the app locally.

### PostgreSQL Setup

Use the `postgres` service in `docker-compose.yml` (recommended):

```bash
docker compose up -d postgres
```

It starts PostgreSQL on `localhost:5432` (defaults: user `postgres`, password `postgres`, database `renewable_energy_advisor`); update `DATABASE_URL` if you change them. With an existing PostgreSQL install, create a dedicated low-privilege role and database instead of using the superuser:

```sql
CREATE ROLE renewable_app WITH LOGIN PASSWORD 'choose-a-password';
CREATE DATABASE renewable_energy_advisor OWNER renewable_app;
```

### Database Migrations

Schema changes are managed with Alembic — the app never creates tables from startup code. From `backend/`, with `DATABASE_URL` set (use the venv's Python so `app` resolves on `sys.path`):

```bash
python -m alembic upgrade head        # apply all migrations
python -m alembic downgrade -1        # roll back one migration
python -m alembic current             # show the applied revision
python -m alembic revision --autogenerate -m "describe the change"   # after editing models
```

### Backend Setup

```bash
cd backend
py -m venv .venv                     # macOS/Linux: python3 -m venv .venv
.venv\Scripts\activate               # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy ..\.env.example .env            # macOS/Linux: cp ../.env.example .env
python -m alembic upgrade head
python -m scripts.seed_all           # loads the verified DISCOM / tariff / incentive data
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000` (interactive docs at `/docs`). See [`backend/README.md`](backend/README.md).

### Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env               # macOS/Linux: cp .env.example .env
npm run dev
```

The app runs at `http://localhost:5173`. See [`frontend/README.md`](frontend/README.md).

### Docker Setup

```bash
docker compose up --build
```

Starts PostgreSQL, the backend (`http://localhost:8000`, running `alembic upgrade head` on every start via `backend/docker-entrypoint.sh`) and the frontend dev server (`http://localhost:5173`, proxying `/api` to the backend through `BACKEND_PROXY_TARGET`). Stop with `docker compose down` (add `-v` to remove the database volume).

### Run in GitHub Codespaces

Open the repository on GitHub → **Code → Codespaces → Create codespace on main**. `.devcontainer/` reuses `docker-compose.yml`, so PostgreSQL, the backend and the frontend start automatically, migrations included.

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

```json
{ "status": "healthy" }
```

### Tests

```bash
cd backend && pytest                 # in-memory SQLite; no live network or AI calls
cd frontend && npm test              # Node's built-in test runner
cd frontend && npx tsc -b && npm run lint && npm run build
```

## Deployment

**Frontend — GitHub Pages.** `.github/workflows/deploy-pages.yml` builds `frontend/` and publishes it on every push to `main` that touches `frontend/**` (or manually). The API URL comes from the `API_BASE_URL` repository variable, passed to the build as `VITE_API_BASE_URL`. Pages has no server rewrites, so the build copies `index.html` to `404.html` for deep links. The site is served under `/Smart-Location-Based-Renewable-Energy-Advisor/`.

**Backend — Render.** [`render.yaml`](render.yaml) defines a Docker web service (`renewable-energy-advisor-api`, free plan, health check `/api/v1/health`) and a PostgreSQL database. Environment: `APP_ENV=production`, a generated `SECRET_KEY`, `RUN_DATA_SEED=true`, `CORS_ALLOWED_ORIGINS=https://kryvexcore.github.io`, `DATABASE_URL` from the database, and `NVIDIA_API_KEY` set manually in Render (never in the repository). On start the container runs `alembic upgrade head`, then (when `RUN_DATA_SEED=true`) the idempotent, validated data seed, then `uvicorn`. Backend changes are deployed from the Render dashboard.

**The customer's device needs only a browser and internet** — no Python, PostgreSQL or local backend.

## Database Models

14 tables (PostgreSQL, 9 Alembic migrations):

```
User (id, created_at)
 └── Building (id, user_id, building_type, name, created_at, updated_at)
       └── Assessment (id, building_id, status, created_at, updated_at)
             ├── Location (latitude, longitude, formatted_address, city, state, country, postal_code)
             ├── EnergyProfile (monthly_electricity_bill_inr, monthly_consumption_kwh, consumption_source,
             │                  consumption_estimate, annual_consumption_kwh)
             ├── BuildingConstraints (roof_area_sqft, land_area_sqft, budget_inr, backup_required)
             └── snapshots (ON DELETE CASCADE): SolarCalculationSnapshot, WindCalculationSnapshot,
                 TariffCalculationSnapshot, IncentiveEvaluationSnapshot
                 (assessment_id, calculation_version, [assumption_version,] input_snapshot, result_snapshot)

LocationResourceSnapshot (latitude, longitude, resource_type, provider, payload, retrieved_at)

Discom (id, name, short_code, state, union_territory, is_active)

ElectricityTariff (state, union_territory, discom_id, consumer_category, tariff_version, tariff_name,
                   slab_min_kwh, slab_max_kwh, energy_charge_inr_per_kwh, fixed_charge_inr, fixed_charge_basis,
                   demand_charge_inr, wheeling_charge_inr_per_kwh, effective_from, effective_to,
                   source_* fields, verification_status, verification_notes, last_verified, active)

IncentiveProgram (scheme_name, scheme_version, level, incentive_type, state, union_territory, discom_id,
                  consumer_category, technology, min/max_system_size_kw, subsidy_type, subsidy_value,
                  percentage_value, maximum_amount, calculation_rules, eligibility_rules,
                  application_requirements, stacking_rules, effective_from, effective_to,
                  verification_status, source_* fields, last_verified, active)
```

- **Recommendation and financial results have no tables** — they are recomputed on request from the tables above.
- `building_type` (assessment classification): `home` | `school` | `college` | `office` | `shop` | `small_institution` | `other`. Tariffs and incentives use the separate `TariffConsumerCategory` (`residential` | `commercial` | `educational_institution` | `public_service` | `industrial` | `agriculture` | `other`) through one explicit mapping — the two are never treated as equal.
- `EnergyProfile.consumption_source` is `user_kwh` (entered) or `user_bill_estimate` (derived from the bill); `monthly_consumption_kwh` is `NULL` when an estimate could not be made — it is never defaulted.
- `IncentiveProgram.level`: `central` | `state` | `discom`. `incentive_type`: `capital_subsidy`, `central_financial_assistance`, `state_subsidy`, `discom_incentive`, `rebate`, `interest_subvention`, `grant`, `performance_incentive`, `other`. `subsidy_type`: `percentage`, `fixed_amount`, `per_kw`, `slab_based`, `benchmark_cost_based`, `other`. Only `verified` rows are used for calculations (`verification_status` is distinct from `active`).
- `LocationResourceSnapshot` is a best-effort audit log keyed by coordinate, not a foreign key off `Location`.
- There is no authentication: every request is attributed to one prototype user (`services/prototype_user.py`).

## API Endpoints

All under `/api/v1` — 19 routes. Only `POST /advisor/chat` calls an AI provider.

| Group | Method | Path | Purpose |
| --- | --- | --- | --- |
| Health | GET | `/health` | Health check |
| Assessment | POST | `/assessments` | Create and persist an assessment (bill-first kWh estimate) |
| | GET | `/assessments` | List recent assessments (`?limit=`) |
| | GET | `/assessments/{id}` | Retrieve a saved assessment |
| | PUT | `/assessments/{id}` | Update an assessment |
| | POST | `/assessments/{id}/estimate-consumption` | Retry the bill-based kWh estimate |
| | DELETE | `/assessments/{id}` | Delete an assessment |
| Location | GET | `/locations/search` | Geocode a place name (`?q=…&limit=`) |
| | GET | `/locations/profile` | Solar/wind/weather/elevation and India resolution for a coordinate (`?latitude=…&longitude=…`) |
| Solar | POST | `/solar/calculate` | Solar system options `{"assessment_id": "…"}` |
| Wind | POST | `/wind/calculate` | Small-wind screening `{"assessment_id": "…"}` |
| Tariff | POST | `/tariffs/calculate` | Estimated baseline bill `{"assessment_id": "…", "calculation_date"?: "YYYY-MM-DD"}` |
| | GET | `/tariffs` | Filtered tariff-slab lookup (`state`, `union_territory`, `consumer_category`, `discom_id`) |
| Incentive | POST | `/incentives/evaluate` | Eligibility for a system `{"assessment_id", "technology", "proposed_capacity_kw", "calculation_date"?}` |
| | GET | `/incentives` | Filtered incentive-programme lookup |
| Recommendation | GET | `/recommendations/{assessment_id}` | Deterministic technology + size recommendation (no AI) |
| Financial | GET | `/financial-analysis/{assessment_id}` | Estimated cost, incentive, net investment, savings, payback (no AI) |
| Advisor | POST | `/advisor/chat` | Ask SHREA AI `{"assessment_id", "message", "history"?}` (one AI call) |
| | GET | `/advisor/overview/{assessment_id}` | Summary and suggested questions (no AI) |

Example `POST /api/v1/assessments` (bill-first — supply `monthly_electricity_bill_inr`, `monthly_consumption_kwh`, or both):

```json
{
  "building": { "building_type": "home", "name": "My Home" },
  "location": {
    "latitude": 13.0827,
    "longitude": 80.2707,
    "formatted_address": "Chennai, Tamil Nadu, India",
    "city": "Chennai",
    "state": "Tamil Nadu",
    "country": "India"
  },
  "energy": { "monthly_electricity_bill_inr": 7500 },
  "constraints": {
    "roof_area_sqft": 1200,
    "land_area_sqft": null,
    "budget_inr": null,
    "backup_required": false
  }
}
```

The response contains the generated `id`, `status`, timestamps and the saved nested objects; for a bill-first assessment `energy` includes the derived `monthly_consumption_kwh`, `consumption_source: "user_bill_estimate"` and the `consumption_estimate` (status, range, tariff used, limitations). See [`docs/bill-first-assessment.md`](docs/bill-first-assessment.md).

---

## Location Intelligence (Phase 3)

```
User → Frontend location search / map (react-leaflet)
     → FastAPI  GET /locations/search | GET /locations/profile
     → LocationService  (app/services/location/location_service.py)
     → Provider Factory → Geocoding | Solar | Wind | Weather | Elevation adapters
        └→ IndiaLocationResolver → state/UT → district → city → DISCOM
     → Normalized LocationProfile  (never a specific provider's raw shape)
```

`LocationService` and the routes depend only on the interfaces in `app/services/location/providers/base.py` and the normalized schemas in `app/schemas/location.py`. Swapping a provider means adding one class and one branch in `provider_factory.py`.

| Category | Provider | Data returned |
| --- | --- | --- |
| Geocoding | Nominatim (OSM) | Search and reverse geocoding |
| Solar | NASA POWER | Monthly + annual solar irradiance (`ALLSKY_SFC_SW_DWN`) |
| Wind | NASA POWER | Monthly + annual wind speed at 10 m and 50 m (`WS10M`, `WS50M`) |
| Weather | NASA POWER | Temperature, precipitation and irradiance (`T2M`, `PRECTOTCORR`, all-sky/clear-sky) |
| Elevation | Open-Elevation | Elevation at the point (shown in Location Intelligence; not used by the engines) |

- **Resilience:** each resource section degrades independently — if wind times out but solar succeeds, the response is still `200 OK` with `wind: null` and `errors.wind` — never a fabricated zero. `GET /locations/search` maps provider failures to 429 / 504 / 502 / 501.
- **Caching:** an in-memory cache with a 24 h TTL (`LOCATION_CACHE_TTL_SECONDS`); failed fetches are never cached. Successful fetches are also written to `location_resource_snapshots` as a best-effort audit log.
- **Freshness:** every populated section carries `source` and `retrieved_at`; solar/wind/weather also carry `period_represented` (NASA POWER climatology is a multi-year average, not real time).
- **Tests** use fake providers (`tests/location_fakes.py`) that are never imported by `provider_factory.py`; no test makes a live network call.

### India location resolution

Every `GET /locations/profile` response includes an `india` section (`app/services/location/india_resolver.py`): `latitude/longitude → state or union territory → district → city → DISCOM`.

- `state`/`union_territory` are normalized to the canonical spelling in `app/core/india_geography.py` (28 states and 8 UTs). A geocoder result that matches none comes back `null` — never a guessed nearest match.
- `district`/`city` come from the geocoder's normalized address components.
- `discom` is resolved from the `discoms` table (five DISCOMs are loaded). **A DISCOM is never guessed from a city name:** with zero matches, or several and no way to disambiguate, `discom` is `null` and `discom_status` is `not_identified` or `ambiguous`; `identified` only when exactly one active match exists.

## India-Based Tariff & Incentive Architecture

```
LOCATION INTELLIGENCE → India Location Resolver (state/UT, district, city, DISCOM)
                                   │
                                   ▼
                    TARIFF / INCENTIVE DATA
       (ElectricityTariff, IncentiveProgram — versioned, sourced, in PostgreSQL)
                                   │
                                   ▼
        Calculation engines: tariff · incentive · (recommendation · financial reuse them)
```

Location intelligence provides resource data; tariff/incentive data provides electricity economics and scheme eligibility; the engines combine them with deterministic formulas. No layer invents a value that belongs to another.

- **Tariffs** (`app/models/electricity_tariff.py`): one row per slab of a published schedule — `state`/`union_territory`, nullable `discom_id`, `consumer_category`, `tariff_version`, slab bounds, `energy_charge_inr_per_kwh`, `fixed_charge_inr` (+ `fixed_charge_basis`, what it is charged *per*), optional demand/wheeling charges, and the provenance fields below.
- **Incentives** (`app/models/incentive_program.py`): one row per scheme *version*. `level` separates **central / state / discom** schemes, which are never combined into one number. A `null` `consumer_category` means "check `eligibility_rules`", never "applies to everyone" — this is what stops a residential central subsidy such as PM Surya Ghar from being applied to a school, college or office.
- **Versioning and provenance:** both carry `effective_from`, `effective_to`, `last_verified`, `source_url`, `source_document`, `source_name`, `verification_status` and `active`; incentives also have `scheme_version`. Both engines resolve the record valid on the calculation date and never use an expired record when a current one exists. The dashboard shows *Source*, *Last verified* and *Effective* for every tariff and incentive.
- **DISCOM registry** (`app/models/discom.py`): `name`, `short_code`, `state`/`union_territory`, `is_active`. Five DISCOMs are loaded; boundary data (which DISCOM serves which district) is not — where several serve a state, the result is `ambiguous`, not guessed.

## Solar Engine (Phase 4)

Estimates technical solar generation and feasibility. **It chooses no size and computes no cost, subsidy, savings or payback** — later engines reuse its output.

```
Location Intelligence (India-based solar resource)
  → SolarCalculationService (only bridge: assessment + location profile → plain input)
  → Solar Engine (app/engines/solar/ — pure functions)
  → System options 1–10 kW, each independently evaluated
```

The engine never calls NASA POWER or any provider; the same formula applies everywhere — only the resource value varies by location:

```
Annual generation (kWh) = Capacity (kWp) × Daily solar resource (kWh/m²/day) × 365 × Performance ratio
```

`ALLSKY_SFC_SW_DWN` (kWh/m²/day) equals "peak sun hours per day", as the formula expects (the method behind tools such as NREL's PVWatts). Monthly generation uses each month's own daily value and real day count — never annual ÷ 12. Roof area required scales from panel wattage, panel footprint and a layout factor (`sizing.py`).

| Assumption (`assumptions.py`) | Default | Basis |
| --- | --- | --- |
| `performance_ratio` | 0.75 | Conservative default for Indian rooftop PV; covers inverter, wiring, soiling, temperature losses |
| `panel_wattage_w` | 400 W | Representative modern monocrystalline module |
| `panel_area_sqft` | 21 sq ft | Physical footprint of a ~400 W panel |
| `layout_factor` | 1.4 | Allowance for spacing, walkways, shading clearance |

`ASSUMPTION_VERSION` and `ENGINE_CALCULATION_VERSION` are returned with every response and recorded in `SolarCalculationSnapshot`. Each option reports annual/monthly generation, `roof_area_required_sqft`, `generation_coverage_percent` (generation ÷ annual consumption, **not capped at 100 %** and not a claim about the bill) and `technical_status` (`technically_feasible` | `technically_infeasible` | `insufficient_data`, e.g. no roof area). If the resource is unavailable, non-positive or in an unknown unit, the whole response is `status: "insufficient_data"` with a reason. 1 electricity unit = 1 kWh throughout.

`POST /api/v1/solar/calculate` — a 404 means the assessment does not exist; `status: "insufficient_data"` (still `200`) means the calculation could not run. The engine is a pure function: the same input and versions give identical output.

## Electricity Tariff Engine (Phase 5)

Estimates a **baseline grid bill** from the assessment's consumption and location. **It applies no subsidy and computes no solar cost, savings or payback** — the Financial Analysis Engine and the bill estimator reuse it.

```
Assessment → location profile (state/UT, DISCOM — never re-derived)
  → BuildingType → TariffConsumerCategory (explicit mapping)
  → TariffRepository (state/UT + DISCOM + category)
  → Tariff Engine (app/engines/tariff/): select version by date → progressive slabs (Decimal) → charge components
  → estimated bill + per-component included / not_included / not_calculated
```

| BuildingType | TariffConsumerCategory |
| --- | --- |
| `home` | `residential` |
| `school`, `college` | `educational_institution` |
| `office`, `shop` | `commercial` |
| `small_institution` | `public_service` |
| `other` | `other` |

- **DISCOM scoping:** `identified` → that DISCOM's tariff, falling back to a state-level tariff only if it has none; `ambiguous`/`not_identified` → only a state-level tariff may be used, otherwise `discom_ambiguous` / `tariff_not_configured`. A DISCOM-specific tariff is never guessed.
- **Slabs** (`slab_calculation.py`): cumulative/progressive billing with `Decimal` — never `float`. `validation.py` rejects (raises, never "fixes") empty, negative, overlapping, non-contiguous slabs, slabs not starting at 0, or more than one unlimited slab.
- **Version selection** (`version_selection.py`): the version whose `[effective_from, effective_to]` covers the calculation date, preferring the latest `effective_from`, ties broken by the version string — deterministic, never dependent on row order.
- **Charge components:** `energy` is always included; `fixed` when a flat monthly/per-connection charge is configured (per-kW/kVA/HP charges are `not_calculated`, and a charge with no recorded basis is never assumed monthly); `wheeling` only when the tariff configures it; `demand` and `tod` are **always** `not_calculated` (sanctioned load and interval data are not collected). `estimated_monthly_bill_inr` sums the included components; `is_partial_estimate` and `excluded_components` make that explicit.
- **Bill estimation** (`bill_estimation.py`): inverts this engine to estimate kWh from a bill (see [How a Result Is Produced](#how-a-result-is-produced)).

`POST /api/v1/tariffs/calculate` returns `status`: `ok`, `insufficient_data` (no coordinates or unresolved state/UT), `discom_ambiguous`, or `tariff_not_configured`. `GET /api/v1/tariffs` browses the configured slabs.

**Coverage:** see [Data Coverage & Provenance](#data-coverage--provenance). Only `verified` and `active` rows are ever used; per-kW fixed charges are never turned into a flat amount. Research log: [`docs/data-verification/`](docs/data-verification/); file format: [`backend/app/data/tariffs/india/README.md`](backend/app/data/tariffs/india/README.md). Every calculation is recorded in `TariffCalculationSnapshot`.

## Incentive Engine (Phase 6)

Evaluates which incentive programmes a system may be eligible for and calculates the amount when the programme's own documented formula allows it. **It computes no installation cost, savings, payback or ROI.**

```
Assessment → location profile → BuildingType → TariffConsumerCategory (same mapping as the tariff engine)
  → IncentiveProgramRepository (technology + central/state/UT/DISCOM candidates; NOT pre-filtered by category)
  → Incentive Engine (app/engines/incentive/): group into schemes → select version by date
       → eligibility → amount → stacking flags
  → every candidate programme's status (ineligible and unverified ones are never hidden)
```

- **Scoping:** technology and `consumer_category` must match exactly (or the programme is genuinely category-agnostic); a residential scheme is never applied to a commercial consumer. Regional variants (PM Surya Ghar's special-category rows) are separate rows chosen by `eligibility_rules`, so exactly one applies (`scope.py`). DISCOM-level schemes follow the same "never guess" rule.
- **Versioning:** exactly one `scheme_version` is selected for the calculation date; otherwise the scheme is reported `scheme_expired` or `scheme_not_active` — never silently dropped.
- **Eligibility** (`eligibility.py`), in order: `verification_status` (only `verified`), `active`, technology, category, `min_system_size_kw`, documented required fields (a field the app does not collect is always missing → `insufficient_information`), then the amount. A system **larger** than `max_system_size_kw` is still eligible; the cap only limits the capacity counted (PM Surya Ghar's CFA caps at 3 kW).
- **Calculation** (`calculator.py`, `Decimal`): `fixed_amount`, `per_kw`, `slab_based` (kW brackets), `percentage` (needs a real cost basis — otherwise `insufficient_information`), `benchmark_cost_based`.
- **Stacking** (`stacking.py`): eligible programmes are **never summed**; each stays a separate line. They are unflagged only if both sides' `stacking_rules` confirm combinability; otherwise `combination_requires_verification` or `mutually_exclusive_with_other_programme`.
- **Financial note:** the Incentive Engine itself uses no installation cost (`budget_inr` is the customer's own budget, not a quotation). The Financial Analysis Engine subtracts its verified result from the MNRE benchmark cost.

`POST /api/v1/incentives/evaluate` — the frontend submits only the assessment and system; the backend always selects the trusted, verified programme data. Programme statuses: `eligible`, `not_eligible`, `insufficient_information`, `scheme_expired`, `scheme_not_active`, `scheme_not_verified`, `discom_ambiguous`, `discom_not_identified`. `GET /api/v1/incentives` browses the configured programmes. Every evaluation is recorded in `IncentiveEvaluationSnapshot`.

**Coverage:** **PM Surya Ghar: Muft Bijli Yojana** — Central Financial Assistance for residential consumers (MNRE guideline OM No. 318/17/2024-GCRT): ₹30,000/kW for the first 2 kW and ₹18,000 for the third kW, nothing beyond 3 kW (maximum ₹78,000); ₹33,000 / ₹19,800 in the special-category States/UTs. Residential only (a college, shop or office is `not_eligible`), valid to the guideline's implementation end, 2027-03-31. No state or DISCOM incentive is verified. See [`docs/data-verification/`](docs/data-verification/) and [`backend/app/data/incentives/india/README.md`](backend/app/data/incentives/india/README.md).

## Wind Engine (Phase 7)

`POST /api/v1/wind/calculate` estimates annual generation for candidate 0.5 / 1 / 2 / 3 / 5 / 10 kW turbines from the wind resource (NASA POWER climatology, m/s; the 10 m reading is used, 50 m is shown only), a generic reference power curve and a Rayleigh speed distribution. Each candidate is `technically_feasible`, `marginal` or `insufficient_resource` by net capacity factor. Assumptions are versioned (`wind-assumptions-2026.1`) and results are snapshotted to `wind_calculation_snapshots`. With no wind resource the result is `wind_resource_unavailable` — never a default speed.

**Technical screening only — structural and site approval are required. This is a preliminary software screening model, not a certified wind-resource assessment or structural/site engineering assessment.** It computes no cost, subsidy, savings or payback. Method, curve, thresholds and limitations: [`docs/wind-engine.md`](docs/wind-engine.md).

## Security

- **AI key isolation:** `NVIDIA_API_KEY` is read from the backend environment only — never in the frontend, GitHub Pages build, a prompt, a response or a log; a reply containing it is rejected.
- **Input validation:** every request is validated by Pydantic (types, ranges, enums) before it reaches the database.
- **SQL:** SQLAlchemy's query builder throughout — no raw or interpolated SQL.
- **Errors:** unhandled exceptions return a generic `{"detail": "Internal server error"}`; details stay in server logs.
- **CORS:** allow-list from `CORS_ALLOWED_ORIGINS`.
- **Advisor:** rate limits, assessment isolation, no provider body/header leakage, logs without message text, untrusted-input rules in the prompt, and a frontend renderer that shows replies as text (only `**bold**`), never HTML.
- **Credentials** come from environment variables (`.env` is git-ignored); the map uses OpenStreetMap tiles directly with no key.
- **Known gap:** there is **no authentication** yet (`services/prototype_user.py` attributes every request to one prototype user; it must be replaced by real auth).

## Documentation

| Document | Contents |
| --- | --- |
| [`docs/ai-advisor.md`](docs/ai-advisor.md) | SHREA AI, prompt rules, cost controls, voice, recommendation engine |
| [`docs/bill-first-assessment.md`](docs/bill-first-assessment.md) | Bill-first input and the bill → kWh estimate |
| [`docs/financial-analysis.md`](docs/financial-analysis.md) | Cost source, methodology, incentive handling, savings, payback, limitations |
| [`docs/wind-engine.md`](docs/wind-engine.md) | Wind screening method and limitations |
| [`docs/data-verification/`](docs/data-verification/) | Research log, coverage report and data-quality report for tariffs and incentives |
| [`backend/README.md`](backend/README.md), [`frontend/README.md`](frontend/README.md) | Setup notes for each side |
| [`backend/app/data/tariffs/india/README.md`](backend/app/data/tariffs/india/README.md), [`backend/app/data/incentives/india/README.md`](backend/app/data/incentives/india/README.md) | Data file formats and how to add a state or scheme |

To add a verified state or scheme, follow the data READMEs above: read the value from a primary official document, record its page/table, keep one version per order, and never overwrite history.
