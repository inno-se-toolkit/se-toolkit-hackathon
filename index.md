# MenuMate — Restaurant Allergen Advisor

Quick navigation:

- [`README.md`](README.md) — Product overview, architecture, deployment, API reference
- [`docker-compose.yml`](docker-compose.yml) — Orchestration for backend, Postgres, Caddy, bot
- [`backend/`](backend/) — FastAPI service (models, CRUD, allergen check)
  - Entry: `backend/app/main.py`
  - Settings: `backend/app/settings.py`
  - DB session: `backend/app/database.py`
  - Models: `backend/app/models/dish.py`
  - Routers: `backend/app/routers/dishes.py`, `backend/app/routers/check.py`
- [`frontend/`](frontend/) — Static HTML/CSS/JS
  - Customer UI: `index.html` + `static/style-customer.css`
  - Admin UI: `admin.html` + `static/style-admin.css`
- [`bot/`](bot/) — Telegram bot
  - Entry: `bot/bot.py`
  - Config: `bot/config.py`
  - Handlers: `bot/handlers/`
  - Services: `bot/services/backend_client.py`, `bot/services/llm_client.py`
- [`infra/caddy/`](infra/caddy/) — Reverse proxy config (Caddyfile.json)
- [`docs/screenshots/`](docs/screenshots/) — Placeholder screenshots (replace with real captures)
  - `customer-page.png` — Safe Dish Checker UI
  - `admin-page.png` — Admin CRUD page
  - `telegram-bot.png` — Bot conversation example
