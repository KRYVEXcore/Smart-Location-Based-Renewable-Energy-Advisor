# Frontend — India-Based Smart Location-Based Renewable Energy Advisor

React + TypeScript + Vite + Tailwind CSS + React Router. Icons from
`lucide-react`. Map from `react-leaflet` + OpenStreetMap tiles — no API key
needed.

`types/location.ts` mirrors the backend's India location resolution
(`district`, `IndiaLocationContext` with `state`/`union_territory`/
`discom`/`discom_status`) and `types/assessment.ts` includes `college` as
a `BuildingType` — both are additive type changes only. Tariff/incentive
data has no UI yet (the backend schema is preparation for Phase 4); once a
real tariff/incentive engine exists, the UI must show an honest
"not yet available" state rather than a fabricated number — never add a
placeholder tariff or subsidy value to a card.

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
