# Hermes Agent — Web UI

Browser-based dashboard for managing Hermes Agent configuration, API keys, and monitoring active sessions.

## Stack

- **Vite** + **React 19** + **TypeScript**
- **Tailwind CSS v4** with custom dark theme
- **shadcn/ui**-style components (hand-rolled, no CLI dependency)

## Development

```bash
# Pin a shared dev token so Vite (5173) and FastAPI (9119) agree.
# Without this, the SPA can't authenticate against the backend in dev mode.
export HERMES_DASHBOARD_DEV_TOKEN="dev-$(openssl rand -hex 16)"

# Terminal 1 — backend on :9119
hermes dashboard --no-open

# Terminal 2 — Vite dev server on :5173 with HMR + /api proxy
cd web/
npm run dev
# then open http://localhost:5173
```

The Vite dev server proxies `/api` and `/api/ws` (WebSocket) requests to `http://127.0.0.1:9119` (the FastAPI backend). The dev token is injected into the served `index.html` so the SPA's `window.__HERMES_SESSION_TOKEN__` matches what the backend expects.

For a one-shot demo without HMR, skip the env var and just run `hermes dashboard` — it builds and serves the SPA directly on :9119 with a fresh random token injected.

## Build

```bash
npm run build
```

This outputs to `../hermes_cli/web_dist/`, which the FastAPI server serves as a static SPA. The built assets are included in the Python package via `pyproject.toml` package-data.

## Structure

```
src/
├── components/ui/   # Reusable UI primitives (Card, Badge, Button, Input, etc.)
├── lib/
│   ├── api.ts       # API client — typed fetch wrappers for all backend endpoints
│   └── utils.ts     # cn() helper for Tailwind class merging
├── pages/
│   ├── StatusPage   # Agent status, active/recent sessions
│   ├── ConfigPage   # Dynamic config editor (reads schema from backend)
│   └── EnvPage      # API key management with save/clear
├── App.tsx          # Main layout and navigation
├── main.tsx         # React entry point
└── index.css        # Tailwind imports and theme variables
```
