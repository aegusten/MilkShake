# MilkShake

QR-driven drink ordering web app for a single milkshake bar. Customers scan
a QR code on the bar's TV, order from their phone, and get a ticket number.
Staff manage the queue from an admin panel; when a drink is ready, the
ticket number flashes on a second TV so the customer knows to pick it up.

For business rules, architecture, data model, and roadmap, see
[`docs/`](docs/).

---

## Stack at a glance

| Layer | Today | Future (per [BACKLOG.md](docs/BACKLOG.md)) |
|---|---|---|
| Backend | FastAPI (async) + SQLAlchemy 2.0 async + asyncpg | + SSE realtime broadcaster |
| Auth | JWT bearer, 8 h access TTL | + refresh tokens via HttpOnly cookie (Phase 7) |
| DB | PostgreSQL 15, Alembic migrations | + `order_status` enum and ticket numbers (Phase 4) |
| Frontend | Svelte 5 SPA + Vite | SvelteKit (SSR) + Tailwind v4 (Phase 7-8) |
| Tests | pytest + pytest-asyncio (service layer) | + integration + e2e (Phase 6) |
| Infra | Docker Compose | + Redis pub/sub, Caddy TLS (Phase 5 / prod) |

---

## Prerequisites

You only need three things on the host:

| Tool | Version | Used for |
|---|---|---|
| **Docker Desktop** (Windows/macOS) or **Docker Engine + Compose v2** (Linux) | 20.10+ | Running everything |
| **Git** | any recent | Cloning the repo |
| **Python 3.11+** | (one-liner only) | Generating the JWT secret |

You do **not** need Python, Node.js, or PostgreSQL installed on the host —
they all run inside containers.

Disk: ~3 GB free for Docker images.

---

## First-time setup (end-to-end)

Open a terminal in the directory where you want the project to live.

### 1. Clone the repo

```powershell
git clone <repo-url> milkshake
cd milkshake
```

### 2. Create your local `.env`

```powershell
# PowerShell (Windows)
Copy-Item .env.example .env

# Bash (macOS / Linux / Git Bash)
cp .env.example .env
```

### 3. Fill in `.env`

Open `.env` in your editor and set two values:

**a) Postgres password** — change `change-me-locally` to anything strong.

**b) `JWT_SECRET`** — must be at least 32 characters. Generate one with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the output into `JWT_SECRET=` in `.env`.

> **If you've run the project before** with a different Postgres password,
> the existing Docker volume is bound to the old password and will refuse
> the new one. Wipe it first: `docker compose down -v` (destructive — drops
> the dev DB).

### 4. Build the images

```powershell
docker compose build
```

This builds two images: `milkshake-backend` (Python 3.11 + FastAPI deps)
and `milkshake-frontend` (Node 20 + Vite). Postgres uses the official
`postgres:15` image — nothing to build.

First build takes 1-2 minutes. Subsequent builds are cached and quick.

### 5. Start the stack

```powershell
docker compose up -d
```

Three containers come up:

| Container | Host port | Inside the network |
|---|---|---|
| `milkshake_db` (Postgres 15) | `55432` | `db:5432` |
| `milkshake_backend` (FastAPI) | `8000` | `backend:8000` |
| `milkshake_frontend` (Vite dev server) | `5173` | `frontend:5173` |

Watch the backend logs until you see `Application startup complete`:

```powershell
docker compose logs -f backend
```

(Ctrl+C exits the tail; the container keeps running.)

### 6. Apply the database migrations

```powershell
docker compose exec backend alembic upgrade head
```

This creates the schema (admins, drinks, item_masters, orders, etc.).

### 7. Create your first admin

```powershell
docker compose exec backend python -m app.scripts.create_superuser `
  --email you@example.com --password ChangeMe123
```

> The backtick at end of line is PowerShell's line continuation. In Bash,
> use `\` instead, or just put the whole command on one line.

You're done. Open http://localhost:5173/admin and log in.

---

## URLs

| URL | Audience |
|---|---|
| http://localhost:5173 | Customer menu |
| http://localhost:5173/admin | Bar staff panel (login required) |
| http://localhost:5173/qr | TV #1 — QR code page |
| http://localhost:5173/display | TV #2 — ready-tickets page (Phase 5+) |
| http://localhost:8000 | API root |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc UI |
| `localhost:55432` | Postgres (credentials in `.env`) |

---

## Project layout

```
milkshake/
├── backend/
│   ├── alembic/                  # DB migrations
│   ├── app/
│   │   ├── api/                  # HTTP route handlers (thin)
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response shapes
│   │   ├── services/             # Business logic (auth, catalog, orders, uploads)
│   │   ├── scripts/              # CLI utilities (create_superuser)
│   │   ├── utils/                # Helpers (passwords, JWT)
│   │   ├── config.py             # pydantic-settings entry
│   │   ├── db.py                 # Async engine + session factory
│   │   └── main.py               # FastAPI app, middleware, exception handlers
│   ├── tests/                    # pytest suite (service layer)
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/                     # Svelte SPA (-> SvelteKit in Phase 7)
│   ├── src/
│   │   ├── api/                  # API client (Bearer token, fetch)
│   │   ├── components/
│   │   │   ├── admin/            # Admin UI
│   │   │   └── public/           # Customer + QR UI
│   │   └── App.svelte            # Path-based route resolver
│   ├── Dockerfile
│   └── package.json
├── docs/                         # ARCHITECTURE / BUSINESS_LOGIC / DATA_MODEL / BACKLOG
├── docker-compose.yml
├── .env.example                  # Template env vars (committed)
└── .env                          # Real env vars (gitignored)
```

---

## Daily usage

```powershell
# start everything (after first-time setup)
docker compose up -d

# stop the stack (keeps the DB volume)
docker compose down

# WIPE everything including the DB (destructive)
docker compose down -v

# tail logs
docker compose logs -f backend
docker compose logs -f frontend

# shell into a container
docker compose exec backend bash
docker compose exec frontend sh

# Postgres prompt
docker compose exec db psql -U milkshake -d milkshake
```

---

## Running tests

The backend has a pytest suite (currently service-layer only — see Phase 6
in the backlog for the full plan). Tests run inside the backend container
against an auto-created `milkshake_test` database in the same Postgres.

```powershell
# all tests
docker compose exec backend pytest

# one file
docker compose exec backend pytest tests/test_order_service.py

# stop on first failure, more verbose
docker compose exec backend pytest -x -vv

# specific test by name
docker compose exec backend pytest -k "place_order"
```

Expected baseline today: **18 passed, 1 warning** (the warning is from
`passlib` — upstream, not ours).

---

## Common tasks

### Generate a new JWT secret

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Create / overwrite an admin

```powershell
# create
docker compose exec backend python -m app.scripts.create_superuser `
  --email new@example.com --password NewPass123

# overwrite existing (resets password, re-enables account)
docker compose exec backend python -m app.scripts.create_superuser `
  --email new@example.com --password NewPass123 --force
```

### Add a database migration

```powershell
# generate from model changes
docker compose exec backend alembic revision --autogenerate `
  -m "add order status column"

# apply
docker compose exec backend alembic upgrade head

# roll back one
docker compose exec backend alembic downgrade -1

# show current revision
docker compose exec backend alembic current
```

### Reset the dev database from scratch

```powershell
docker compose down -v
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.create_superuser `
  --email you@example.com --password ChangeMe123
```

### Hit the API directly

```powershell
# log in (returns JWT)
curl -X POST http://localhost:8000/api/admin/login `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"you@example.com\",\"password\":\"ChangeMe123\"}'

# call an admin endpoint with the token
curl http://localhost:8000/api/admin/orders `
  -H "Authorization: Bearer <paste-token-here>"
```

The interactive UI for this is at http://localhost:8000/docs — click
"Authorize", paste the access_token, and call any endpoint.

---

## Phone / QR access (test on a real device)

The customer flow assumes a phone scanning the bar's QR code. To test it
end-to-end on your phone:

1. Find your computer's LAN IP:
   ```powershell
   # Windows
   ipconfig

   # macOS / Linux
   ifconfig | findstr "inet "
   ```
   You're looking for something like `192.168.1.42`.

2. Tell the frontend to use that IP for API calls. Create
   `frontend/.env` (gitignored) with:
   ```
   VITE_API_BASE=http://192.168.1.42:8000
   ```

3. Restart the frontend container so Vite picks up the new env var:
   ```powershell
   docker compose restart frontend
   ```

4. On your computer, open `http://192.168.1.42:5173/qr`. Scan the QR with
   your phone (must be on the same Wi-Fi).

5. Update `BACKEND_CORS_ORIGINS` in the root `.env` to include the LAN
   origin so the API accepts requests from the phone:
   ```
   BACKEND_CORS_ORIGINS=http://localhost:5173,http://192.168.1.42:5173
   ```
   Restart the backend: `docker compose restart backend`.

---

## Production deployment (not yet automated)

Production setup is outlined in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) ("Deployment topology
(target)"). Short version:

- Single VPS, Docker Compose, Caddy or nginx in front for TLS.
- Generate a **fresh** `JWT_SECRET` for production — never reuse dev.
- Set a strong `POSTGRES_PASSWORD`.
- Lock `BACKEND_CORS_ORIGINS` down to your real domain (no `localhost`).
- Nightly `pg_dump` to off-host storage.
- `docker compose --profile prod` style override file (TBD).

Do **not** deploy without going through Phase 4 (order status flow) and
Phase 5 (SSE realtime) — those are blockers for a functional bar.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `port already allocated` on `up` | Another service is using 5173, 8000, or 55432 | Stop the conflicting service, or change host ports in `docker-compose.yml` |
| Backend log: `password authentication failed for user "milkshake"` | The Postgres volume was initialized with a different password than the current `.env` | `docker compose down -v` then start fresh (loses dev data) |
| Backend won't start: `ValidationError` mentioning `JWT_SECRET` | `.env` missing or `JWT_SECRET` shorter than 32 chars | Regenerate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| Frontend page blank for ~10 s | Vite is doing its first compile | Wait, refresh. Check `docker compose logs frontend` |
| Phone can't reach the menu | `VITE_API_BASE` still points at `localhost` (the phone's own loopback) | Use the host's LAN IP and add it to `BACKEND_CORS_ORIGINS` |
| `curl` fails with `Connection refused` on `localhost:8000` | Backend not yet running or crashed | `docker compose ps`, then `docker compose logs backend` |
| Admin token suddenly stops working | 8-hour TTL expired | Log in again. Phase 2.5 (refresh tokens) will fix this in Phase 7. |
| Tests fail with `got Future attached to a different loop` | pytest-asyncio loop scoping (already handled by `NullPool` in `tests/conftest.py`) | Pull latest; if still broken, ensure `pytest.ini` has `asyncio_mode = auto` |
| `docker compose exec backend alembic upgrade head` says `Target database is not up to date` | First-run state — schema not yet applied | Run the same command again; if it still fails, check Alembic logs |

---

## Status

This codebase is **mid-refactor**, on the way to a real customer launch.
The MVP runs end-to-end today, but several capabilities are still being
hardened.

### Phases shipped

- **Phase 1** — async backend (asyncpg + `AsyncSession`)
- **Phase 2** — JWT bearer auth + pydantic-settings + JWT_SECRET validation
- **Phase 3** — service layer + pytest suite (18 tests, all green)

### Next up

- **Phase 4** — order status state machine (pending → accepted → ready → completed) + 3-digit daily-reset ticket numbers
- **Phase 5** — Server-Sent Events for live order push to `/admin` and `/display`
- **Phase 6** — broader test coverage (integration + e2e)
- **Phase 7** — SvelteKit migration (SSR menu, file-based routing)
- **Phase 8+** — Tailwind v4, realtime UI, i18n, polish

Full roadmap with acceptance criteria: [docs/BACKLOG.md](docs/BACKLOG.md).

---

## Documentation

| Doc | What's in it |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System diagram, components, routes, deployment topology |
| [docs/BUSINESS_LOGIC.md](docs/BUSINESS_LOGIC.md) | Actors, order flow, ticket-numbering rules, state machine |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | ERD, table-by-table reference, invariants |
| [docs/BACKLOG.md](docs/BACKLOG.md) | All 11 refactor phases + post-MVP feature backlog |

## License

Internal project. No public license assigned.
