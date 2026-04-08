# SE Toolkit LMS Assistant

A lightweight, AI-powered Learning Management System assistant that provides both a Telegram bot and a web dashboard for accessing lab information, scores, and analytics. Built for educators and students to quickly retrieve course data via chat or a visual interface.

---

## Demo

Screenshots of the deployed product (to be added):

### Web Dashboard — Items Page
<!--
Replace with a screenshot of the Items page showing the table of labs/tasks.
Example: a browser window with the LMS Items table visible.
-->
![Items page](docs/screenshots/items-page.png)

### Web Dashboard — Analytics Dashboard
<!--
Replace with a screenshot of the Dashboard showing charts (score distribution, timeline, group performance, pass rates).
Example: a browser window with the four charts visible.
-->
![Dashboard](docs/screenshots/dashboard.png)

### Telegram Bot — Commands
<!--
Replace with a screenshot of a Telegram conversation showing /start, /labs, /scores responses.
Example: Telegram chat with bot responses and inline keyboard.
-->
![Telegram bot](docs/screenshots/telegram-bot.png)

> **Note:** Place the actual screenshots in `docs/screenshots/` and update the paths above.

---

## Product Context

- **End users**
  - Students and instructors in the SE Toolkit lab course who need quick access to lab assignments, submission scores, and class performance metrics.

- **Problem**
  - Course data lives in a backend API, but there is no user-friendly way to explore it. Students must manually query endpoints or wait for instructor replies to know which labs are available, how they scored, or how the class performed.

- **Solution**
  - Two complementary clients:
    1. A Telegram bot that understands natural language and slash commands, powered by an LLM to route intents to backend tools.
    2. A React web dashboard with interactive charts (Chart.js) for visual analytics.
  Both are backed by a FastAPI + PostgreSQL service and are fully containerized for easy deployment.

---

## Features

### Implemented
- **Backend (FastAPI + PostgreSQL)**
  - REST endpoints for items, interactions, learners, analytics, and ETL pipeline
  - API key authentication
  - CORS enabled for frontend
  - Database initialization with sample data

- **Telegram Bot**
  - Slash commands: `/start`, `/help`, `/health`, `/labs`, `/scores <lab>`
  - Natural language intent routing via LLM tool calling (9 backend endpoints exposed as tools)
  - Inline keyboard buttons for common actions
  - Offline `--test` mode for local testing without Telegram
  - Comprehensive error handling and fallback responses

- **Web Dashboard**
  - API key connection flow (localStorage)
  - Items page: table view of all labs/tasks
  - Analytics dashboard with 4 charts:
    - Submissions timeline (line chart)
    - Score distribution (bar chart)
    - Group performance (bar chart)
    - Task pass rates (doughnut chart)
  - Lab selector to switch between labs

- **Infrastructure**
  - Full Docker support (multi-stage builds, non-root runtime)
  - `docker-compose.yml` with services: backend, postgres, pgadmin, caddy (reverse proxy + static file server), bot
  - Caddy configuration serves frontend and routes API paths to backend
  - Environment-variable-driven configuration

### Not Yet Implemented (Future Work)
- Rich formatting (tables, charts as images) in Telegram responses
- Response caching for faster LLM and API replies
- Conversation context for multi-turn dialogs
- User authentication/authorization (OAuth, sessions)
- Mobile app (React Native / Flutter)
- Admin panel for data management

---

## Usage

### Quick start with Docker Compose

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/se-toolkit-hackathon.git
cd se-toolkit-hackathon

# 2. Create a `.env.docker.secret` file (see Deployment section for required variables)
cp .env.docker.example .env.docker.secret
# Edit .env.docker.secret with your real values (bot token, API keys, etc.)

# 3. Start all services
docker compose --env-file .env.docker.secret up --build -d

# 4. Verify services are running
docker compose --env-file .env.docker.secret ps
```

#### Access points
- **Web dashboard**: `http://<LMS_API_HOST_ADDRESS>:<LMS_API_HOST_PORT>` (default from `.env.docker.example`)
- **Backend API docs (Swagger)**: `http://<LMS_API_HOST_ADDRESS>:<LMS_API_HOST_PORT>/docs`
- **Telegram bot**: open Telegram and interact with your bot (set `BOT_TOKEN` in `.env.docker.secret`)
- **pgAdmin**: `http://<PGADMIN_HOST_ADDRESS>:<PGADMIN_HOST_PORT>` (email/password from `.env.docker.secret`)

#### Stopping
```bash
docker compose --env-file .env.docker.secret down
```

### Using the Telegram bot

```bash
# Test a command locally (no Telegram token required)
cd bot
uv run bot.py --test "/start"
uv run bot.py --test "/labs"
uv run bot.py --test "/scores lab-04"
uv run bot.py --test "what labs are available?"

# Run the bot in production (requires BOT_TOKEN, LMS_API_KEY, LLM_API_KEY, etc.)
cp .env.bot.example .env.bot.secret
# Edit .env.bot.secret with your secrets
uv run bot.py
```

---

## Deployment

### Target OS
- Ubuntu 24.04 LTS (matches university VM images)

### Prerequisites on the VM
- Docker Engine (latest)
- Docker Compose plugin (`docker compose`)
- Git
- Internet access to pull base images (or a local mirror configured via `REGISTRY_PREFIX` in `.env.docker.secret`)

### Environment variables

Create `.env.docker.secret` with at least:

| Variable | Description |
|----------|-------------|
| `BACKEND_HOST_ADDRESS` | Host IP to bind backend (e.g., `0.0.0.0`) |
| `BACKEND_HOST_PORT` | Host port for backend API (e.g., `42002`) |
| `BACKEND_CONTAINER_PORT` | Container port (fastAPI) — usually `8000` |
| `BACKEND_NAME` | Service name displayed in health checks |
| `BACKEND_DEBUG` | `true` or `false` |
| `BACKEND_CONTAINER_ADDRESS` | Container IP/hostname (usually `backend`) |
| `BACKEND_ENABLE_INTERACTIONS` | `true`/`false` — enable interactions router |
| `BACKEND_ENABLE_LEARNERS` | `true`/`false` — enable learners router |
| `LMS_API_KEY` | API key for LMS backend authetication |
| `AUTOCHECKER_API_URL`, `AUTOCHECKER_API_LOGIN`, `AUTOCHECKER_API_PASSWORD` | ETL sync source (optional — can be dummy values if not used) |
| `POSTGRES_HOST_ADDRESS` | Host IP to bind PostgreSQL (e.g., `0.0.0.0`) |
| `POSTGRES_HOST_PORT` | Host port for PostgreSQL (e.g., `42001`) |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Database credentials |
| `PGADMIN_HOST_ADDRESS`, `PGADMIN_HOST_PORT`, `PGADMIN_EMAIL`, `PGADMIN_PASSWORD` | pgAdmin access |
| `CADDY_CONTAINER_PORT` | Container port for Caddy (usually `80`) |
| `LMS_API_HOST_ADDRESS`, `LMS_API_HOST_PORT` | Public host/port for the entire application |
| `BOT_TOKEN` | Telegram bot token from @BotFather |
| `LLM_API_KEY` | LLM provider API key (Qwen or compatible) |
| `LLM_API_BASE_URL` | LLM API base URL (e.g., `http://host.docker.internal:42005/v1` for local Qwen proxy) |
| `LLM_API_MODEL` | Model name (e.g., `qwen-coder`) |
| `QWEN_CODE_API_URL` | Qwen Code API URL for Caddy reverse proxy (optional) |

See `.env.docker.example` for a template with all variables and comments.

### Step-by-step deployment

```bash
# 1. Prepare the system
sudo apt-get update && sudo apt-get install -y docker.io docker-compose git

# 2. Clone the repository
git clone https://github.com/<your-username>/se-toolkit-hackathon.git
cd se-toolkit-hackathon

# 3. Create environment secrets
cp .env.docker.example .env.docker.secret
nano .env.docker.secret  # fill in real values

# 4. Ensure the bot Docker image can be built (uv.lock and pyproject.toml are in repo)
#    The multi-stage build uses astral/uv images; ensure network access to Docker Hub or your mirror.

# 5. Build and start
docker compose --env-file .env.docker.secret up --build -d

# 6. Check health
docker compose --env-file .env.docker.secret ps
docker compose --env-file .env.docker.secret logs --tail 20

# 7. Test the API:
curl http://<LMS_API_HOST_ADDRESS>:<LMS_API_HOST_PORT>/items/ -H "Authorization: Bearer <LMS_API_KEY>"
curl http://<LMS_API_HOST_ADDRESS>:<LMS_API_HOST_PORT>/health

# 8. Open the web dashboard:
#    http://<LMS_API_HOST_ADDRESS>:<LMS_API_HOST_PORT>
```

### Updating
```bash
git pull
docker compose --env-file .env.docker.secret up --build -d
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
