# MilkShake

QR-driven drink ordering app with FastAPI, PostgreSQL, and Svelte.

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
docker-compose exec backend python -m app.scripts.create_superuser --email admin@gmail.com --password Password123
```

## URLs

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Admin UI: `http://localhost:5173/admin`
- QR page: `http://localhost:5173/qr`

## Admin credentials (example)

- Email: `admin@gmail.com`
- Password: `Password123`

Change the email/password in the superuser command to your own values.

## Database connection (host machine)

- Host: `localhost`
- Port: `55432`
- Database: `milkshake`
- User: `milkshake`
- Password: `milkshake123`

## Notes

- Database schema is managed by Alembic (do not use `db/init.sql`).
- Edit `.env` for local secrets and ports.

## Local hosting + QR (phone access)

To make the site reachable from a phone on the same network:

```bash
cd frontend
npm install
npm run dev -- --host
```

Then open `http://<LAN-IP>:5173/qr` on your computer to generate a QR code that
points to the menu URL. Scan it with the phone.

If the backend runs on the same machine, set `VITE_API_BASE` to
`http://<LAN-IP>:8000` in `frontend/.env` so the phone can reach the API.
