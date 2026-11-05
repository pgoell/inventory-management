# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory inventory dashboard, forked from a Claude Code workshop demo. Runs at inventory-management.pgoell.com.

> **This repo is public.** Never commit credentials, internal hostnames or private registry URLs. `client/.npmrc` pins the public npm registry and `client/package-lock.json` stays gitignored so a local registry never leaks into a commit. Leave both in place.

## Layout

- `server/`: FastAPI on port 8001. Every route lives in `main.py`; `mock_data.py` loads `server/data/*.json` into memory at startup. No database, nothing persists.
- `client/`: Vue 3 and Vite on port 3000. Views in `src/views/`, every API call in `src/api.js`, shared state in `src/composables/` (filters, auth, i18n).
- `tests/backend/`: pytest with FastAPI's `TestClient`; `conftest.py` puts `server/` on the path.

## Commands

```sh
./scripts/start.sh                             # backend and frontend; ./scripts/stop.sh ends both
cd server && uv run python main.py             # backend alone
cd client && npm install && npm run dev        # frontend alone
cd tests && uv run --project ../server pytest  # all backend tests
cd tests && uv run --project ../server pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory
cd client && npm run build                     # client/dist/
```

There is no linter and no frontend test suite. Test a UI change in the browser with the Chrome DevTools MCP tools (`mcp__chrome-devtools__*`): start both servers, open your own page with `new_page` on `http://localhost:3000`, check the views you touched with `take_snapshot` and `list_console_messages`, and close the page when done.

## How it fits together

- Four filters (time period, warehouse, category, order status) live in `useFilters.js` and go to the API as query params. The value `all` means no filter, and the client leaves it out. The server filters lists in Python (`apply_filters`, `filter_by_month` in `main.py`); `month` takes `2025-01` or a quarter such as `Q1-2025`.
- Inventory has no time dimension, so `/api/inventory` ignores `month`. `/api/demand`, `/api/backlog`, `/api/spending/*` and `/api/reports/*` take no filters.
- A change to the shape of a JSON file in `server/data/` needs the matching Pydantic model in `main.py` changed too.
- UI text goes through `t()` from `useI18n.js`, with a key in both `src/locales/en.js` and `src/locales/ja.js`. `Reports.vue` and `Backlog.vue` still hardcode English.
- Server dependencies live twice: `pyproject.toml` for uv, `requirements.txt` for the Docker image. Change both.

## Deploy

A push to `main` deploys to prod; a manual run of the `Deploy` workflow sends any ref to dev. `.github/workflows/deploy.yml` builds both images on GitHub, pushes them to GHCR and hands the tag to a script on the VPS. In the image, Caddy serves the built client and the client calls `/api` on the same origin (`VITE_API_BASE_URL=/api`); locally it calls `http://localhost:8001/api`. Every `uses:` pins a full commit SHA with the version as a comment.

## Conventions

- One change, one branch, one pull request into `main`.
- Delegate new or heavily changed `.vue` files to the `vue-expert` subagent. Use the `backend-api-test` skill for tests in `tests/backend/`.
- UI design: slate and gray (`#0f172a`, `#64748b`, `#e2e8f0`), green/blue/yellow/red for status, hand-written SVG charts, CSS Grid layouts, no emojis.
- `v-for` keys use a real id (`sku`, `month`), never the index.
