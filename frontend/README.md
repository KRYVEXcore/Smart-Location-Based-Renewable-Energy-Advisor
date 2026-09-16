# Frontend — Smart Renewable Energy Advisor

React + TypeScript + Vite + Tailwind CSS + React Router. Icons from
`lucide-react`. Map from `react-leaflet` + OpenStreetMap tiles — no API key
needed.

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
