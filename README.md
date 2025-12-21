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
