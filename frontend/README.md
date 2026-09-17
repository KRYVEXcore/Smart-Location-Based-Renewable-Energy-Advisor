# Frontend — India-Based Smart Location-Based Renewable Energy Advisor

React + TypeScript + Vite + Tailwind CSS + React Router. Icons from
`lucide-react`. Map from `react-leaflet` + OpenStreetMap tiles — no API key
needed.

`types/location.ts` mirrors the backend's India location resolution
(`district`, `IndiaLocationContext` with `state`/`union_territory`/
`discom`/`discom_status`) and `types/assessment.ts` includes `college` as
a `BuildingType` — both are additive type changes only. Incentive data has
no UI yet (the backend schema is preparation for a future phase); once a
real incentive engine exists, the UI must show an honest "not yet
available" state rather than a fabricated number — never add a placeholder
subsidy value to a card.

**Phase 5 — Electricity Tariff:** the Dashboard's "Electricity tariff"
section (`components/tariff/ElectricityTariffSection.tsx`) shows the
estimated baseline grid bill from `POST /api/v1/tariffs/calculate`, with
each charge component (energy, fixed, wheeling, demand, time-of-day)
labeled `included` / `not_included` / `not_calculated` — demand and
time-of-day are always `not_calculated` since the assessment doesn't
collect sanctioned load or interval consumption data. A location with no
verified tariff data shows an honest "No verified electricity tariff is
configured yet for this location" empty state, never a fabricated ₹0. It
never shows a subsidy, solar cost, saving, or payback figure. The tariff
fetch is sequenced after the location-intelligence fetch settles, the same
as the solar fetch, so both only run once the shared location cache is
warm.

**Phase 6 — Government Incentives:** the Dashboard's "Government
incentives" section (`components/incentive/GovernmentIncentivesSection.tsx`)
shows every candidate programme from `POST /api/v1/incentives/evaluate`
(technology `solar`, a fixed 3 kW reference capacity — Phase 4 never picks
a single "recommended" capacity, so this uses a common residential
reference point rather than inventing one) as an expandable card: a status
badge (✓ Eligible / × Not eligible / ? More information required /
⚠ Verification required / — Expired or not yet active), the calculated
amount only when the programme is actually eligible and calculable, and a
"Why?" expansion with the reason, missing fields, stacking notes, and the
official source link. Ineligible and unverified programmes are always
shown, never hidden. An amount is never shown for anything but a verified,
eligible, calculable programme. Sequenced after location settles, same as
solar and tariff.

**Phase 4 — Solar Analysis:** the Dashboard's "Solar analysis" section
(`components/solar/SolarAnalysisSection.tsx`) shows the technical solar
system options from `POST /api/v1/solar/calculate` — real generation, roof
area, and coverage numbers for 1-10 kW, each with a
`technically_feasible` / `technically_infeasible` / `insufficient_data`
status. It never shows a cost, subsidy, saving, or payback figure; it
states outright that "Financial analysis ... will be available in a later
phase." The location-intelligence fetch and the solar-calculation fetch
are deliberately sequenced (not fired concurrently) — both would otherwise
independently query the same backend location cache for the same
coordinate, and a flaky upstream provider could return success to one and
a transient failure to the other, showing contradictory data in the same
page.

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

## Scripts

- `npm run dev` — start the Vite dev server
- `npm run build` — type-check and build for production
- `npm run preview` — preview the production build locally
- `npm run lint` — run Oxlint

## Environment variables

See [.env.example](.env.example). `VITE_API_BASE_URL` must point to the backend
(e.g. `http://localhost:8000`) — Vite only exposes variables prefixed with `VITE_`
to client-side code.

See the [repository root README](../README.md) for full project documentation.
