# Backlog

**Status, November 2026:** phases 1 to 6 and 9 are done. Phase 9 shipped on the
current Svelte SPA instead of waiting for the SvelteKit port. Phases 2.5, 7, 8,
10 and 11 are open.

Two kinds of work live here:

1. **Refactor phases**, fixing what's already there. Sequenced; each phase
   has acceptance criteria and ships independently.
2. **Feature backlog**, new functionality on top of the refactored base.
   Prioritized but not strictly sequenced.

## Refactor phases

Each phase is one branch (`refactor/phase-N-name`) merged to `main` after
acceptance.

### Phase 1: Async backend (done)
**Branch:** `refactor/phase-1-async`
**Why:** Foundation. Sync DB in FastAPI blocks the event loop. SSE needs
async to handle long-lived connections.

Scope:

- Switch `psycopg2-binary` → `asyncpg`.
- Migrate engine to `create_async_engine`, sessions to `AsyncSession`.
- All route handlers become `async def`.
- `get_db` becomes async dependency.
- Update all queries (`.query()` → `select()` + `await session.execute()`).

Acceptance:

- All existing endpoints respond identically (verified via Swagger).
- No `psycopg2` import remains.
- A k6 or `wrk` smoke test of 100 RPS on `GET /api/drinks` succeeds with no
  blocked event loop warnings.

### Phase 2: JWT auth (access tokens) (done)
**Branch:** `refactor/phase-2-auth`
**Why:** Current auth is "send the admin UUID as a header". Anyone with that
UUID is admin. Critical security fix.

Refresh tokens are intentionally **deferred to Phase 7** where SvelteKit's
server routes can set HttpOnly cookies. The current Vite SPA cannot store a
refresh token safely; an 8-hour access token covers a typical staff shift.

Scope:

- `PyJWT[crypto]` added.
- `pydantic-settings` introduced via `app/config.py`. `JWT_SECRET`,
  `JWT_ALGORITHM`, `JWT_ACCESS_TTL_MINUTES`, Postgres + CORS env vars all
  flow through `Settings`. `JWT_SECRET` rejected at startup if shorter than
  32 chars.
- `/api/admin/login` returns `{ access_token, token_type: "bearer",
  expires_in }`. Token has `sub`, `iat`, `exp`, `type: "access"` claims.
- New `require_admin` dependency reads `Authorization: Bearer <jwt>` via
  FastAPI's `HTTPBearer`, validates the JWT, returns the loaded `Admin`.
- `X-Admin-Id` header support removed.
- Frontend SPA updated: stores token in `localStorage` (interim, moves to
  HttpOnly cookie in Phase 7), sends `Authorization: Bearer` on every admin
  call, clears token + redirects to login on 401.

Acceptance:

- Login returns an access token; bad creds → 401.
- Missing / malformed / expired token → 401 with `WWW-Authenticate: Bearer`.
- Admin can log in, manage drinks, manage orders. Reloading the admin tab
  keeps the session (token survives in `localStorage`).
- No `X-Admin-Id` reference remains in the codebase.

### Phase 2.5: Refresh tokens (deferred until SvelteKit)
**Branch:** `refactor/phase-2.5-refresh-tokens` (after Phase 7)
**Why:** Short-lived access tokens + long-lived refresh in HttpOnly cookie
is the safe pattern. Cannot be done cleanly on the current SPA, needs a
server-side endpoint that can `Set-Cookie` with HttpOnly + Secure flags.

Scope (when SvelteKit lands):

- Access TTL drops to 15-30 min.
- Refresh tokens: 7-day TTL, one-time use, rotated on each refresh.
- Stored in DB (`admin_refresh_tokens` table) for revocation.
- SvelteKit `+server.ts` endpoint issues the cookie; browser never sees the
  refresh token directly.
- Auto-refresh on 401 via SvelteKit `handleFetch` hook.

### Phase 3: Service layer + settings (done)
**Branch:** `refactor/phase-3-services`
**Why:** Business logic currently lives in route handlers. Hard to test,
hard to reuse from CLI scripts and SSE handlers.

Scope:

- New `app/services/` package.
- `OrderService.place_order(payload) → Order`.
- `OrderService.transition(order_id, target_status, actor) → Order`.
- `CatalogService.upsert_drink(...)`, etc.
- `pydantic-settings` for env vars with validation; `os.getenv` is banned.
- Route handlers shrink to: parse input → call service → return response.

Acceptance:

- No `db.query()` or business logic remains in any file under `app/api/`.
- All services have at least one unit test (mocked or in-memory DB).
- Missing env vars cause startup to fail with a clear message.

### Phase 4: Order status + ticket numbers (done)
**Branch:** `refactor/phase-4-order-lifecycle`
**Why:** The current "Mark ready" button is non-functional. Ticket numbers
do not exist yet.

Scope:

- Migration `0004_order_status_and_tickets`:
  - Adds `status order_status NOT NULL DEFAULT 'pending'`.
  - Adds `ticket_number int NOT NULL`, `ticket_date date NOT NULL`.
  - Adds `accepted_at`, `ready_at`, `completed_at`, `cancelled_at`.
  - Backfills existing rows with `status=completed`, sequential ticket
    numbers per day.
  - Adds `UNIQUE(ticket_date, ticket_number)` constraint.
- Migration `0005_orders_guest_name_nullable`: drop NOT NULL on
  `guest_name`.
- `OrderService` enforces the state machine documented in
  [BUSINESS_LOGIC.md](BUSINESS_LOGIC.md).
- Ticket-number allocator uses Postgres advisory lock keyed on the bar's
  current date.
- New endpoints: `accept`, `ready`, `complete`, `cancel`.
- `BAR_TIMEZONE` env var (default `Asia/Tashkent`).

Acceptance:

- 100 concurrent `POST /api/orders` produce 100 unique ticket numbers (load
  test with `wrk` or async pytest).
- Invalid transition (e.g. `pending → ready`) returns 409.
- Midnight rollover: an order placed at 23:59:30 gets today's number; one
  placed at 00:00:10 gets tomorrow's #001.

### Phase 5: Realtime via SSE (done)
**Branch:** `refactor/phase-5-realtime`
**Why:** Admins should not have to refresh to see new orders. The TV
`/display` needs live ticket updates.

Scope:

- Redis service added to `docker-compose.yml`.
- `app/realtime.py`: async pub/sub broadcaster.
- Endpoints: `GET /api/stream/admin` (admin-auth), `GET /api/stream/display`
  (public, read-only).
- Publishers in `OrderService` for every status transition.
- Heartbeat every 15s to keep proxies from killing the connection.
- Reconnect with last-event-id support.

Acceptance:

- Two browser tabs on `/admin` both see a new order appear within 500ms of
  the POST.
- Killing the backend mid-stream causes the frontend to auto-reconnect.
- An `/display` tab open for 24h does not leak memory or drop the
  connection.

### Phase 6: Test suite (done)
**Branch:** `refactor/phase-6-tests`
**Why:** Backfill the safety net. Going forward, every PR adds tests for
its change; this phase establishes the baseline.

Scope:

- `pytest`, `pytest-asyncio`, `httpx.AsyncClient` for API tests.
- Postgres testcontainer for integration tests.
- Coverage target: ≥ 80% on `app/services/`, ≥ 60% overall.
- GitHub Actions workflow: lint (ruff) + tests on every push.

Acceptance:

- `pytest` runs green in CI.
- Critical flows covered: place order, accept→ready→complete, cancel,
  ticket-number uniqueness, JWT expiry, drink CRUD authorization.

### Phase 7: SvelteKit migration
**Branch:** `refactor/phase-7-sveltekit`
**Why:** Replace the hand-rolled SPA routing with a real framework. Adds
SSR for the menu (phone-first perf).

Scope:

- New `web/` directory (sibling to `frontend/`); migrate pages one at a
  time.
- Routes: `/`, `/admin`, `/admin/drinks`, `/admin/orders`, `/qr`,
  `/display`.
- Server load functions call the backend so secrets / tokens never reach
  the browser.
- `docker-compose.yml` switches `frontend` service to `web/`.
- Old `frontend/` deleted in a separate, clean final commit.

Acceptance:

- `lighthouse` score ≥ 90 on `/` over 3G profile.
- All flows from the current SPA work in the new app (manual QA pass).
- No client-side fetch to the backend that should be SSR (audit network tab).

### Phase 8: Tailwind v4 + design tokens
**Branch:** `refactor/phase-8-design`
**Why:** Plain CSS is hard to maintain. Tailwind v4 with design tokens gives
consistent spacing, colors, and typography across screens.

Scope:

- Tailwind v4 installed; `@theme` block with brand colors / spacing.
- Components ported one at a time; legacy CSS deleted as it's replaced.
- Dark theme variant for `/display` (TV screens look better in dark mode).

Acceptance:

- No `.css` file outside `app.css` and component-scoped styles.
- Visual regression: screenshot diff against pre-refactor baseline acceptable
  per the customer.

### Phase 9: Realtime in the UI (done)
**Branch:** `refactor/phase-9-realtime-ui`
**Why:** With SSE backend ready and SvelteKit migrated, wire up the live
behavior end-to-end.

Scope:

- Admin queue subscribes to `/api/stream/admin`; new orders animate in.
- Optional sound chime on new order (toggle in admin header).
- `/display` subscribes to `/api/stream/display`; ready tickets animate in,
  completed tickets fade out.
- Reconnect with exponential backoff.

Acceptance:

- Place order on phone → admin tablet shows it within 1s, no refresh.
- Mark ready → `/display` shows ticket within 1s.
- Disable network on `/display` tab for 30s → reconnects automatically when
  network returns, fetches fresh state.

### Phase 10: i18n done right
**Branch:** `refactor/phase-10-i18n`
**Why:** The current language switcher is a giant inline `copy` object.
Hard to extend, no plurals, no formatting.

Scope:

- `svelte-i18n` or `@inlang/paraglide`.
- Translations in `messages/{en,ru,uz}.json`.
- Language switcher persists in `localStorage`.
- Numbers/currency formatted via locale.

Acceptance:

- All customer-facing strings come from translation files.
- Switching language changes everything on the page including currency
  formatting.

### Phase 11: Polish & a11y
**Branch:** `refactor/phase-11-polish`
**Why:** Pre-launch hardening.

Scope:

- Loading skeletons.
- Error boundaries.
- Mobile gestures: swipe to remove from cart.
- Keyboard navigation on the admin panel.
- WCAG AA color contrast checked.
- Real device testing: iOS Safari, Android Chrome.

Acceptance:

- axe-core scan returns no violations.
- Keyboard-only QA pass on admin works end-to-end.

## Feature backlog (post-MVP)

Not sequenced. Pick based on customer demand.

| Priority | Feature | Rough size |
|---|---|---|
| High | Sales reporting (daily/weekly revenue, top drinks) | M |
| High | Out-of-stock toggle per drink | S |
| Medium | SMS notification when ready (Twilio / Eskiz) | M |
| Medium | Estimated wait time on the order success screen | M |
| Medium | Printer integration (ESC/POS) for kitchen tickets | L |
| Medium | Drink modifications (extra sugar, no whip, size) | L |
| Low | Customer accounts / order history | XL |
| Low | In-app payment (Click, Payme) | XL |
| Low | Multi-venue / multi-tenant | XL |
| Low | Admin role separation (staff vs owner) | M |
| Low | Drink popularity ML ranking on the menu | M |

## Operational backlog

| Item | Why |
|---|---|
| Daily `pg_dump` to off-host storage | Disaster recovery |
| Sentry for backend + frontend | Visibility on prod errors |
| Healthcheck `/healthz` + uptime monitor | Customer doesn't notice outages first |
| `.env.example` checked in, real `.env` rotated | Onboarding + secret hygiene |
| Rate limit on `/api/admin/login` | Brute-force defense |
| Rate limit on `/api/orders` (per IP) | Spam / abuse defense |
| Caddy / nginx in front with TLS | Production deployment |
