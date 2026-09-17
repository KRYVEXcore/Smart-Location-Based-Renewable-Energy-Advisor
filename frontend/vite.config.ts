import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  // A GitHub Pages project site is served from a /<repo-name>/ subpath, not
  // the domain root — only relevant to the production build; the dev
  // server (Docker Compose, Codespaces, `npm run dev`) always serves from
  // "/". App.tsx reads this same value via import.meta.env.BASE_URL so
  // React Router's basename stays in sync automatically.
  base: command === 'build' ? '/Smart-Location-Based-Renewable-Energy-Advisor/' : '/',
  plugins: [react(), tailwindcss()],
  server: {
    // Only used when VITE_API_BASE_URL is unset, so apiClient.ts's requests
    // are relative (e.g. "/api/v1/health"). Lets the frontend reach the
    // backend by the Docker Compose service hostname without needing to
    // know its own externally-forwarded origin (e.g. in GitHub Codespaces,
    // where the browser can't reach "localhost:8000" on the host running
    // the container) — a same-origin request the dev server proxies
    // server-side, so no CORS/origin configuration is needed either. Local
    // `npm run dev` with VITE_API_BASE_URL set in .env is unaffected, since
    // an absolute URL never goes through this proxy.
    proxy: {
      '/api': {
        target: process.env.BACKEND_PROXY_TARGET ?? 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
}))
