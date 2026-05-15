# MilkShake

QR-driven drink ordering web app for a single milkshake bar. Customers scan a
QR code on the bar's TV, order from their phone, and receive a ticket number.
Staff manage the queue from an admin panel and flash the ticket number on a
second TV screen when the drink is ready for pickup.

## Documentation

| Doc | What's in it |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System diagram, components, technology choices, routes |
| [docs/BUSINESS_LOGIC.md](docs/BUSINESS_LOGIC.md) | User flows, order lifecycle, ticket numbering, state machine |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | ERD, table-by-table reference, constraints |
| [docs/BACKLOG.md](docs/BACKLOG.md) | Refactor phases, acceptance criteria, future features |

## Stack

| Layer | Today | Target (post-refactor) |
|---|---|---|
| Backend | FastAPI (sync) + SQLAlchemy + psycopg2 | FastAPI (async) + SQLAlchemy async + asyncpg |
| Auth | `X-Admin-Id` header (insecure) | JWT bearer tokens |
| Realtime | None (manual refresh) | Server-Sent Events |
| Frontend | Svelte 5 SPA + Vite | SvelteKit (SSR) + Tailwind v4 |
| Database | PostgreSQL 15 | PostgreSQL 15 |
| Orchestration | Docker Compose | Docker Compose + Redis (for SSE fan-out) |

## Routes

| URL | Audience | Device |
|---|---|---|
| `/` | Customer | Personal phone (QR-scanned) |
| `/admin` | Bar staff | Tablet / laptop |
| `/qr` | Bar venue | TV #1 (kiosk mode) |
| `/display` | Bar venue | TV #2 (kiosk mode) |

## Quick start (Docker)

```bash
# first time only
docker-compose down -v

# build and run
docker-compose build backend
docker-compose up -d

# run migrations
docker-compose exec backend alembic upgrade head

# create admin user
docker-compose exec backend python -m app.scripts.create_superuser \
  --email admin@example.com --password ChangeMe123
```

## Local URLs

- Public menu: http://localhost:5173
- Admin panel: http://localhost:5173/admin
- TV QR page: http://localhost:5173/qr
- TV display page: http://localhost:5173/display (post-refactor)
- API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs
- Postgres (host): `localhost:55432`, db `milkshake`, user `milkshake`

## Phone access on LAN

To make the menu reachable from a real phone on the same Wi-Fi:

```bash
cd frontend
npm install
npm run dev -- --host
```

Set `VITE_API_BASE=http://<LAN-IP>:8000` in `frontend/.env` so the phone can
reach the API.

## Project status

This codebase is **mid-refactor**. The MVP works end-to-end but several
components are slated for replacement before the customer goes live. See
[docs/BACKLOG.md](docs/BACKLOG.md) for the phased roadmap.
