# 🥤 MilkShake

A QR‑code–driven drink‑ordering web app built with **Vue 3 + FastAPI + PostgreSQL**, fully containerised with Docker.

---

## 🚀 Features

| Area               | Capability                                                                                                                                                                                                     |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Guest (mobile)** | • Scan QR → `/order` SPA<br>• Browse drinks by category & type<br>• Add to cart, checkout with name & optional phone<br>• Instant order confirmation                                                           |
| **Admin**          | • JWT‑protected dashboard at `/admin`<br>• CRUD categories (sortable)<br>• CRUD drinks (up to 3 images, cover auto‑picked)<br>• Live order queue (`pending` → `completed` / `cancelled`) with cash/card record |
| **Backend**        | • FastAPI + SQLAlchemy<br>• Enum‑driven schema, price snapshot, trigger enforcing ≤ 3 images                                                                                                                   |
| **Dev Experience** | • Hot‑reload front & back<br>• One‑command Docker up<br>• Swag / OpenAPI docs at `/docs`                                                                                                                       |

---

## 🗂️ Folder Structure

```text
MilkShake/
├─ backend/               # Python 3.11 + FastAPI
│  ├─ app/                #   ← ALL Python lives here
│  │   ├─ main.py         # FastAPI entry
│  │   ├─ api/            # “views” (routers)
│  │   ├─ models/         # SQLAlchemy ORM
│  │   ├─ schemas/        # Pydantic
│  │   ├─ utils/          # helpers
│  │   ├─ db.py | config.py
│  └─ Dockerfile
├─ frontend/              # Vue 3 + Vite
│  ├─ src/ (components, views, router)
│  └─ Dockerfile
├─ db/
│  └─ init.sql            # DDL + triggers + seed
├─ docker-compose.yml
└─ .env.example
```

---

## 🔧 Prerequisites

* **Docker 20+** & **docker‑compose**
* (Optional) Node 20+ & Python 3.11 for local non‑Docker runs

---

## ⚡ Quick Start

```bash
cp .env.example .env               # adjust secrets if needed
docker-compose up --build          # 🐳 spins up db, back, front
```

* API → [http://localhost:8000](http://localhost:8000)
* Swagger → [http://localhost:8000/docs](http://localhost:8000/docs)
* Frontend → [http://localhost:5173/order](http://localhost:5173/order)

### Tear down

```bash
docker-compose down -v            # stops & prunes db volume
```

---

## 🌍 Environment Variables (excerpt)

| Key                    | Purpose                   | Example                 |
| ---------------------- | ------------------------- | ----------------------- |
| `POSTGRES_DB`          | Postgres database name    | `milkshake`             |
| `SECRET_KEY`           | FastAPI JWT signing key   | `changeme`              |
| `BACKEND_CORS_ORIGINS` | Allowed front‑end origins | `http://localhost:5173` |

See **`.env.example`** for full list.

---

## 📑 API Cheat Sheet (core routes)

| Method  | Path                              | Role   | Description              |
| ------- | --------------------------------- | ------ | ------------------------ |
| `GET`   | `/api/drinks`                     | Public | List all drinks          |
| `POST`  | `/api/orders`                     | Public | Create guest order       |
| `PATCH` | `/api/admin/orders/{id}/complete` | Admin  | Mark order paid & served |
| `POST`  | `/api/admin/drinks`               | Admin  | Create drink (JSON)      |
| `POST`  | `/api/admin/drinks/{id}/images`   | Admin  | Upload drink image       |

Full live docs at `/docs` once the backend is running.

---

## 🧑‍💻 Useful Dev Commands

```bash
# frontend (outside Docker)
cd frontend && npm i && npm run dev

# backend (outside Docker)
cd backend/app && uvicorn main:app --reload --port 8000

# run Alembic migrations
alembic revision --autogenerate -m "init"
alembic upgrade head
```

---

## 🚦 Milestones

| Stage | Deliverable                             |
| ----- | --------------------------------------- |
| M1    | Infrastructure up → health check passes |
| M2    | Database schema migrated                |
| M3    | Public API (drinks, orders) done        |
| M4    | Admin API + auth                        |
| M5    | Guest SPA ready                         |
| M6    | Admin SPA ready                         |
| M7    | Visual polish & tests                   |

---

## 🤝 Contributing

1. Fork & clone.
2. Create feature branch: `git checkout -b feat/my‑thing`.
3. Commit with conventional commits (`feat: …`, `fix: …`).
4. PR into `main`.

---

## 📜 License

MIT © 2025 MilkShake Team
