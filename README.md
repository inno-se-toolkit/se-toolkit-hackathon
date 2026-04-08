# MenuMate — Restaurant Allergen Advisor

**One-line summary:** A web-first, Telegram-integrated system that lets restaurant guests instantly discover menu items safe for their allergies and dietary preferences (vegan, gluten-free, etc.), while providing staff a simple admin interface to keep the menu up to date.

---

## Context

- **Domain:** Hospitality / Restaurant technology
- **Intended end users:** Dining guests with food allergies or dietary preferences; restaurant managers/kitchen staff
- **Point in the user’s workflow:** Post-seating / pre-order — a guest inspects the menu, quickly flags what they can (and cannot) eat, and places an order with confidence
- **Problem:** Traditional menus list ingredients, but non-experts miss hidden allergens (e.g., “whey” = dairy) and cross-contamination cues; miscommunication risks health incidents and legal liability
- **Solution:** A shared digital menu where each dish is tagged with ingredients and allergens; a conversational search engine + quick-filter chips answer natural-language queries (“no milk or nuts”) and highlight safe choices real-time

---

## Architecture

```
 ┌─────────────────┐      ┌──────────────┐      ┌─────────────────┐
 │  Customer Web   │─────▶│  Reverse     │─────▶│  Backend FastAPI│
 │  (index.html)   │      │  Proxy Caddy │      │  (Python)       │
 │  Admin Web      │─────▶│  / /admin    │      │                 │
 │  (admin.html)   │      └──────────────┘      │  • /api/dishes  │
 └─────────────────┘                            │  • /api/check   │
         │                                      │  • / /admin     │
         │                                      └────────┬────────┘
         │                                                │
         │                                        PostgreSQL DB
         │                                                │
         ▼                                                ▼
 ┌─────────────────┐                            ┌──────────────────┐
 │ Telegram Bot    │────────────────────────────▶│  Dishes CRUD     │
 │ (@bot)          │   REST API (/api/… )        │  Allergen filter │
 └─────────────────┘                            └──────────────────┘
```

---

## Features

### Implemented
- Customer-facing web page with search box + quick-filter chips for milk, nuts, gluten, soy, vegan, gluten-free
- Admin page (`/admin`) for CRUD management of menu items (name, ingredients, allergens tag, vegan/GF flags)
- RESTful backend (FastAPI) with OpenAPI docs: `/docs`
  - `GET /` → customer UI
  - `GET /admin` → admin UI
  - `GET/POST /api/dishes` → list and create dishes
  - `PUT/DELETE /api/dishes/{id}` → update and delete a dish
  - `POST /api/check` → process an allergy/diet query and return safe dishes
- PostgreSQL persistence via SQLModel/SQLAlchemy 2.0 async; indexed search
- CORS-enabled frontend served either directly (dev) or through Caddy reverse proxy (prod)
- Dockerised development stack: `docker compose up -d`
- Telegram bot (`@your_bot`) with commands:
  - `/start` — welcome message
  - `/help` — usage summary
  - `/menu` — current menu listing
  - `/check <query>` — e.g. `/check no milk` or `/check vegan`
  - Plain-text messages are routed to the same natural language checker (LLM-backed if configured)
- LLM integration point for intent extraction / query expansion (optional)

### Not (Yet) Implemented
- Authentication / role-based admin login
- Audit log of who changed which menu item
- Real-time ingredient inventory and substitution suggestions
- On-call SMS/email escalation for critical allergen incidents
- Advanced filter combinations (e.g. “vegan AND gluten-free AND no soy” — technically supported but UI chips are single-toggle)

---

## Quick Start (Local Development, Ubuntu 24.04)

### Prerequisites
```bash
sudo apt update && sudo apt install -y docker.io docker-compose curl git
sudo usermod -aG docker $USER  # log out/in afterwards
```

### Clone and configure
```bash
git clone https://github.com/<your-org>/se-toolkit-hackathon.git
cd se-toolkit-hackathon
cp bot/.env.bot.example bot/.env.bot
# Edit bot/.env.bot and set BOT_TOKEN (from @BotFather)
# Optional: LLM_API_KEY and LLM_API_BASE_URL for smarter chat
echo "POSTGRES_USER=postgres"   >> .env
echo "POSTGRES_PASSWORD=postgres" >> .env
```

### Start the stack (non-root users in containers where applicable)
```bash
docker compose up -d
```

Verify:
```bash
docker compose ps
docker compose logs -f backend
```

Access:
- Customer UI: http://127.0.0.1:8000
- Admin UI: http://127.0.0.1:8000/admin
- API docs: http://127.0.0.1:8000/docs
- pgAdmin: http://127.0.0.1:8085 (user `admin@example.com`, pass `admin`) — connect to
  Host `postgres`, port `5432`, user `postgres`, password `postgres`

### Create your first menu item
1. Open Admin UI → fill the form and click **Save**.
2. Return to the customer page and run a query like `"no milk"`.

---

## Manual Setup Without Docker (Ubuntu 24.04)

> Use this when you want to run individually (e.g. staging).

```bash
# 1. PostgreSQL (system-wide)
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE DATABASE restaurant;"
# Adjust pg_hba.conf for local md5 auth if needed, then restart:
sudo systemctl restart postgresql

# 2. Backend
cd backend
pip install uv
uv sync  # installs to .venv
cp .env.example .env  # edit DATABASE_URL if needed
cp app/data/init.sql /tmp/seed.sql
sudo -u postgres psql -d restaurant -f /tmp/seed.sql
uv run app/run.py   # listens 0.0.0.0:8000

# 3. Frontend (static)
# No build step required — just serve the files with Caddy or Nginx.
# Example Caddy config in /infra/caddy/Caddyfile.json
caddy start --config infra/caddy/Caddyfile.json

# 4. Telegram Bot
cd bot
uv sync
cp .env.bot.example .env.bot
uv run bot.py
```

---

## Development Workflow

- Backend changes: edit files under `backend/app/`; run `uv run app/run.py` (reload with `uvicorn --reload …` for faster iteration)
- Frontend: iterate on `frontend/`. Caddy serves `/srv` directly; rebuild toggles required for Docker but no npm build needed for local changes
- Bot: `uv run bot.py --test "no milk"` to validate routing without a live Telegram connection
- DB migrations: currently schema is created on startup; for production state migrations, extend with Alembic (not yet wired)

---

## Testing

### Automated (backend unit tests)
```bash
cd backend
uv run pytest
```

### Manual smoke test (no Telegram required)
```bash
cd bot
uv run bot.py --test "/start"
uv run bot.py --test "I'm allergic to milk and gluten"
```

### End-to-end via API
```bash
# Health
curl -s http://127.0.0.1:8000/healthz | jq

# List dishes
curl -s http://127.0.0.1:8000/api/dishes | jq '.[] | {id, name, allergens}'

# Check allergies
curl -s -X POST http://127.0.0.1:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{"message": "vegan"}' | jq '.safe[] | {name, is_vegan}'
```

---

## Production Deployment

### Ubuntu 24.04 with Caddy + systemd

1. Set system timezone and static IP (if applicable).
2. Install Docker Engine + Compose plugin.
3. Clone repo and populate `.env`:
   ```bash
   cat > .env <<EOF
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=<strong-password>
   BASE_DOMAIN=<public-hostname-or-ip>
   BOT_TOKEN=<from @BotFather>
   LLM_API_KEY=<optional>
   LLM_API_BASE_URL=https://api.example.com/v1
   LLM_API_MODEL=qwen-coder
   EOF
   ```
4. `docker compose up -d`
5. Validate with the commands in the previous section.
6. (Optional) Set up SSL certificates via Caddy by ensuring DNS A record resolves to the host; HTTPS is automatic.

### Reverse-proxy note
Port 80 is exposed by the `caddy` service. If you already run another web server, change `ports:` mapping for `caddy` to, e.g., `"127.0.0.1:8080:80"` and reverse-proxy from your chosen public entry.

---

## Environment Variables

| Variable              | Scope   | Description                                       |
|-----------------------|---------|---------------------------------------------------|
| `POSTGRES_USER`       | Compose | DB superuser                                      |
| `POSTGRES_PASSWORD`   | Compose | DB password                                       |
| `BASE_DOMAIN`         | Compose | Public domain for Caddy certificates (optional)   |
| `BOT_TOKEN`           | Bot     | Telegram bot token (required)                     |
| `LMS_API_BASE_URL`    | Bot     | Override backend URL; defaults to `http://backend:8000` |
| `LLM_API_KEY`         | Bot     | LLM provider key for intent extraction            |
| `LLM_API_BASE_URL`    | Bot     | LLM provider base URL                             |
| `LLM_API_MODEL`       | Bot     | Model name (default: `qwen-coder`)                |

---

## Troubleshooting

- **Bot does not start:** Missing `BOT_TOKEN` in `bot/.env.bot`. Obtain one from [@BotFather](https://t.me/BotFather).
- **No dishes appear in frontend:** Backend returns 200 but empty list — ensure seed data loaded: `docker compose exec postgres psql -U postgres -d restaurant -c "SELECT * FROM dish;"`. If empty, run `docker compose exec backend python -c "from app.database import init_db, async_engine; import asyncio; asyncio.run(init_db())"` (fewer steps in prod: data is loaded on first start).
- **Port 80 already in use:** Change Caddy’s port mapping in `docker-compose.yml`.
- **CORS errors in browser:** Add your origin to `BACKEND_CORS_ORIGINS` in `backend/.env` or set `CORS_ORIGINS` in compose.
- **Caddy permissions errors on startup:** Ensure host folders have sufficient permissions. Alternatively set `RUN_AS=root` for Caddy for quick local testing (not recommended for production).

---

## API Reference

| Endpoint          | Method   | Purpose                                          | Example Request                                                 |
|-------------------|----------|--------------------------------------------------|-----------------------------------------------------------------|
| `/`               | GET      | Customer UI                                      | `curl http://localhost:8000`                                    |
| `/admin`          | GET      | Admin UI                                         | `curl http://localhost:8000/admin`                              |
| `/api/dishes`     | GET      | List all dishes                                  | `curl http://localhost:8000/api/dishes`                         |
| `/api/dishes`     | POST     | Create a dish                                    | `curl -X POST -H "Content-Type: application/json" -d '{"name":"Salmon","ingredients":"salmon, herbs, oil","allergens":"","is_vegan":false,"is_gluten_free":true}' http://localhost:8000/api/dishes` |
| `/api/dishes/{id}`| PUT      | Update a dish                                    | `curl -X PUT -H "Content-Type: application/json" -d '{"is_vegan":true}' http://localhost:8000/api/dishes/1` |
| `/api/dishes/{id}`| DELETE   | Delete a dish                                    | `curl -X DELETE http://localhost:8000/api/dishes/1`             |
| `/api/check`      | POST     | Allergy/diet query → safe dishes                 | `curl -X POST -H "Content-Type: application/json" -d '{"message":"no milk"}' http://localhost:8000/api/check` |
| `/docs`           | GET      | OpenAPI Swagger UI                                | `curl http://localhost:8000/docs`                               |
| `/healthz`        | GET      | Liveness probe                                   | `curl http://localhost:8000/healthz`                            |

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Maintainers

Restaurant Allergen Advisor project — adapted from the SE Toolkit Lab Assistant platform.
