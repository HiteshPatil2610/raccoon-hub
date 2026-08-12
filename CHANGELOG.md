# Raccoon Hub — Changelog

All changes are recorded in reverse-chronological order.
Each entry includes the date, time (IST), what changed, and which files were modified.

---

## ALL FEATURES COMPLETE ✅

All 15 originally planned features have been implemented.
No pending features remain. See the completed log below for full details.

---

## COMPLETED CHANGES

---

### [2026-08-11 | Session 4] — Bug Fix: Backend Not Starting (apscheduler missing)

**Time:** Evening session
**Problem:** Every API call in the admin panel showed **(failed)** in the browser Network tab.
Root cause: `apscheduler` was added to `requirements.txt` but never installed into the venv.
`main.py` imports `scheduler.py` which imports `apscheduler` — so the backend crashed on
startup with `ModuleNotFoundError: No module named 'apscheduler'` before serving a single request.

**Fix:**
```powershell
cd d:\raccoon-hub\backend
.\venv\Scripts\pip.exe install apscheduler==3.10.4
```

**Files modified:** None (install only — `requirements.txt` already had the entry)

---

### [2026-08-11 | Session 4] — Bug Fix: .env Inline Comment Breaking DATABASE_URL

**Time:** Evening session
**Problem:** `DATABASE_URL` line had an inline `#` comment:
```
DATABASE_URL=postgresql://...@localhost:5432/raccoon_hub #postgresql://...render.com/...
```
`pydantic-settings` does not strip inline comments — the `#postgresql://...` part was being
read as part of the connection string, making it invalid and crashing the app on startup.

Additionally, `ALLOWED_ORIGINS` was missing from `.env`, causing CORS to only allow
`http://localhost:5173` and block `http://127.0.0.1:5173`.

**Fix:** Removed inline comment from `DATABASE_URL`; added explicit `ALLOWED_ORIGINS` entry.

**Files modified:**
- `backend/.env` — Removed inline comment on `DATABASE_URL`; added `ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`

---

### [2026-08-11 | Session 3] — Feature 2: Amazon Creators API Verification Docs + Debug Logging

**What changed:** `creators_api_provider.py` fully rewritten with:
- A prominent status banner noting the provider is written from docs, not yet verified against live credentials
- `DEBUG_CREATORS_API=true` env flag that logs full raw JSON responses for every API call
- Detailed `VERIFY:` inline comments on every response field path that is assumed vs. confirmed
- Fallback key handling (`itemsResult` / `ItemsResult`) to handle potential PascalCase variation
- Structured per-field debug logging in `_parse_item()` to identify missing fields at a glance
- Step-by-step verification guide in the module docstring

**Files modified:**
- `backend/app/providers/creators_api_provider.py` — Full rewrite with debug flag, VERIFY comments, structured logging

---

### [2026-08-11 | Session 3] — Feature 1: Semantic Search / Similar Products (pgvector + Gemini Embeddings)

**What changed:**
- `pgvector==0.3.5` added to `requirements.txt`
- New Alembic migration `b2c3d4e5f6a7` enables the pgvector extension and adds a `vector(768)` `embedding` column + HNSW index to `products`. Migration is **fully idempotent** — if pgvector is not installed on the PostgreSQL server (e.g. local dev), it skips gracefully and stamps itself as applied. The app continues to run normally.
- `models.py` — `embedding` column added using `pgvector.sqlalchemy.Vector(768)` with a `try/except` fallback to `Text` if pgvector Python package is not installed
- `admin.py` confirm route — after saving a product, calls `ai_client.embed_text()` to generate a 768-dim Gemini embedding and stores it. Fail-soft: if embedding fails, the product is already saved, DB is rolled back to a clean state, and the error is swallowed
- `public.py` — `GET /products/{asin}/similar` endpoint: uses `pgvector` cosine distance for nearest-neighbour search when embedding exists; falls back to same-category products when pgvector is unavailable or no embedding stored
- `ProductDetail.jsx` — fetches and renders a "Similar Products" horizontal grid row below the product info
- `api/client.js` — `getSimilarProducts(asin)` method added

> **Local dev note:** pgvector is not installed on the local PostgreSQL server. The migration skipped the extension/column/index and stamped itself. The similar products endpoint returns same-category fallback results. On Render (managed Postgres, pgvector available), run `alembic upgrade head` to apply the column and index.

**Files modified:**
- `backend/requirements.txt` — Added `pgvector==0.3.5`
- `backend/alembic/versions/b2c3d4e5f6a7_add_embedding_column.py` — New migration (graceful skip if pgvector not on server)
- `backend/app/models.py` — `embedding` column with try/except import fallback
- `backend/app/routers/admin.py` — Embedding generation on confirm (fail-soft)
- `backend/app/routers/public.py` — `/products/{asin}/similar` endpoint
- `frontend/src/pages/ProductDetail.jsx` — Similar products section
- `frontend/src/api/client.js` — `getSimilarProducts(asin)`

---

### [2026-08-11 | Session 3] — Feature 10: Daily Product Refresh via Background Scheduler

**What changed:**
- New `scheduler.py` — `AsyncIOScheduler` (APScheduler) with one job: `refresh_all_products` runs at **03:00 UTC daily**. Loops all active products, calls `get_provider().fetch_product(asin)`, updates price/availability/images/features in DB, and records a `PriceHistory` entry whenever the price changes. Robust error handling: per-product failures are logged and skipped without stopping the rest of the batch.
- `main.py` — Migrated to FastAPI `lifespan` context manager (replaces deprecated `on_event`). Scheduler starts on app startup and stops cleanly on shutdown.
- `requirements.txt` — `apscheduler==3.10.4` added

**Files modified:**
- `backend/app/scheduler.py` — New file
- `backend/app/main.py` — Lifespan context manager, scheduler start/stop
- `backend/requirements.txt` — `apscheduler==3.10.4`

---

### [2026-08-11 | Session 3] — Feature 9: Admin Analytics (View + Click Counters)

**What changed:**
- `GET /products/{asin}` now increments `view_count` on every detail page load
- New `POST /admin/products/{asin}/track-click` — no auth required, fire-and-forget counter incremented when the Buy button is clicked
- New `GET /admin/analytics` — returns top 20 products sorted by `view_count + click_count` descending
- `BuyButton.jsx` — fires `api.trackClick(asin)` on every outbound Amazon click (non-blocking)
- `AdminPanel.jsx` — new `Analytics` section at the bottom: table of top products with view/click counts
- `ProductAnalyticsOut` schema added

**Files modified:**
- `backend/app/routers/admin.py` — `track-click` and `analytics` endpoints
- `backend/app/routers/public.py` — `view_count` increment on detail page
- `backend/app/schemas.py` — `ProductAnalyticsOut` schema
- `frontend/src/components/BuyButton.jsx` — `trackClick` on click
- `frontend/src/pages/AdminPanel.jsx` — `Analytics` component
- `frontend/src/pages/AdminPanel.css` — Analytics table styles
- `frontend/src/api/client.js` — `trackClick(asin)`, `getAnalytics()`

---

### [2026-08-11 | Session 3] — Feature 7: Bulk Import from URL List / CSV

**What changed:**
- New `POST /admin/products/bulk-preview` endpoint — accepts up to 20 URLs, runs the full preview pipeline (ASIN extract → fetch → tag extraction → Gemini blurb) on each URL independently. One URL failing does not block the rest. Returns a per-URL array of success/error results.
- `AdminPanel.jsx` — new `BulkImport` component: textarea for pasting URLs one-per-line + CSV file upload (parses `url` column), Preview All button, results table showing ✓/✗ per URL with title/price or error message
- `BulkPreviewRequest` and `BulkPreviewResult` schemas added

**Files modified:**
- `backend/app/routers/admin.py` — `bulk-preview` endpoint; `_run_preview()` helper shared with single preview
- `backend/app/schemas.py` — `BulkPreviewRequest`, `BulkPreviewResult`
- `frontend/src/pages/AdminPanel.jsx` — `BulkImport` component
- `frontend/src/pages/AdminPanel.css` — Bulk import styles
- `frontend/src/api/client.js` — `bulkPreviewProducts(urls)`

---

### [2026-08-11 | Session 3] — Feature 14: SEO / Open Graph Meta Tags

**What changed:**
- `ProductDetail.jsx` now sets `document.title` and injects `og:title`, `og:description`, `og:image`, `og:url`, `og:type` meta tags on mount using product data. Tags are cleaned up (reset) when the user navigates away.
- Implemented via `setMeta()` helper that creates/updates `<meta property="...">` elements in the document `<head>` dynamically.
- Product blurb is used as `og:description`; falls back to price display string.

**Files modified:**
- `frontend/src/pages/ProductDetail.jsx` — `setMeta()`, `applyProductSEO()`, `resetSEO()` functions; called on product load and cleanup

---

### [2026-08-11 | Session 3] — Feature 6 (complete): Price History Route + Sparkline Chart

**What changed:**
- `GET /products/{asin}/price-history` — new public endpoint returning last 60 price history entries (oldest-first) for a product
- `GET /products/{asin}` (detail) — now records a `PriceHistory` row whenever the live-fetch detects a price change from the cached value
- New `PriceSparkline` React component — SVG sparkline with fill area, trend line, first/last dots, min/max range label, date labels at both ends, and a trend indicator (↑ red / ↓ green)
- `ProductDetail.jsx` — fetches price history and renders `PriceSparkline` below the price (only shown when ≥2 history points exist)
- `PriceHistoryOut` schema added

**Files modified:**
- `backend/app/routers/public.py` — price-history endpoint; price change detection + history recording in detail route
- `backend/app/schemas.py` — `PriceHistoryOut`
- `frontend/src/components/PriceSparkline.jsx` — New SVG sparkline component
- `frontend/src/components/PriceSparkline.css` — Sparkline styles
- `frontend/src/pages/ProductDetail.jsx` — Sparkline + similar products integration; SEO meta tags
- `frontend/src/pages/ProductDetail.css` — Similar products grid styles
- `frontend/src/api/client.js` — `getPriceHistory(asin)`, `getSimilarProducts(asin)`, `trackClick(asin)`, `getAnalytics()`, `bulkPreviewProducts(urls)`

---

### [2026-08-11 | Session 2] — Bug Fix: Migration a1b2c3d4e5f6 Failing on Duplicate Index

**Time:** Afternoon session
**Problem:** Running `alembic upgrade head` failed with:
```
psycopg2.errors.DuplicateTable: relation "ix_price_history_product_id" already exists
```
The `price_history` table had been partially created in a previous failed run, so the
`CREATE TABLE` succeeded but `CREATE INDEX` failed because the index already existed.
Alembic's version table never recorded the migration as complete.

**Fix:** Rewrote the migration to be fully idempotent — checks `information_schema` and
`pg_indexes` before every DDL operation and skips anything already present.

**Files modified:**
- `backend/alembic/versions/a1b2c3d4e5f6_add_price_history_and_analytics.py` — Rewritten as idempotent

---

### [2026-08-11 | Session 2] — Feature 6 (partial): Price History Model + Analytics Migration

**What changed:** Data layer only.
- `PriceHistory` ORM model added with `product_id` FK (CASCADE DELETE), `price_amount`, `price_display`, `recorded_at`
- `view_count` and `click_count` INTEGER columns added to `Product` model (default 0)
- `price_history` relationship added to `Product`
- Alembic migration `a1b2c3d4e5f6` creates `price_history` table and adds the two new columns

**Files modified:**
- `backend/app/models.py` — `PriceHistory` model, analytics columns, relationship
- `backend/alembic/versions/a1b2c3d4e5f6_add_price_history_and_analytics.py` — New migration

---

### [2026-08-11 | Session 2] — Feature 13: Out-of-Stock Visual Treatment on Grid Cards

**What changed:** Collapsed cards where `availability` contains "out of stock" now:
- Show a red **"Out of Stock"** badge (top-left corner, semi-transparent backdrop blur)
- Apply `filter: grayscale(60%)` + `opacity: 0.6` to the entire card

**Files modified:**
- `frontend/src/components/ProductCard.jsx` — `isOutOfStock` flag; `is-out-of-stock` class; OOS badge element
- `frontend/src/components/ProductCard.css` — `.is-out-of-stock` styles; `.product-card__oos-badge`

---

### [2026-08-11 | Session 2] — Features 11, 12, 3, 4: Pagination + Sort + Tag Sidebar + Search

**What changed (all implemented together):**

**Feature 11 — Pagination:** Home grid paginates 24 products per page. Prev/Next controls at the bottom. New `GET /products/count` endpoint returns the total matching count for the pagination UI. Page resets to 0 whenever filters/sort/search change.

**Feature 12 — Sort:** Sort dropdown added — Newest (default), Price ↑, Price ↓, Top Rated. Sort applied server-side via `ORDER BY` for correctness across pages.

**Feature 3 — Tag Sidebar:** Simple tag pill row replaced with a grouped sticky sidebar. Tags grouped by type — Category / Budget / Spec / Style — with product count badges. On mobile (≤700px) collapses to a horizontal wrapping pill row.

**Feature 4 — Text Search:** Search input with 300ms debounce. Postgres `ILIKE` filter on product title. Parallel fetch of products + count on every change.

**Files modified:**
- `backend/app/routers/public.py` — `search`, `sort`, `limit`, `offset` params on `GET /products`; new `GET /products/count`; `GET /tags` returns `product_count` per tag
- `backend/app/schemas.py` — `TagOut.product_count` optional field
- `frontend/src/pages/Home.jsx` — Full rewrite: search (debounced), sort dropdown, grouped sidebar with counts, pagination prev/next
- `frontend/src/pages/Home.css` — Full rewrite: toolbar, sidebar, count badges, pagination, mobile responsive
- `frontend/src/api/client.js` — `countProducts(params)` method

---

### [2026-08-11 | Session 1] — Feature 5: Tag Editing on Existing Products

**What changed:** Admin can now edit tags on already-saved products inline in the products
table — no need to delete and re-add a product just to fix its tags.

- Each product row has a **Tags (N)** button. Clicking it expands an inline `TagChipEditor`
  row directly below the product row.
- Admin adds/removes chips, clicks **Save tags**.
- `PATCH /admin/products/{id}` with `{ tags: [...] }` in the payload replaces all existing
  tags with the new list server-side.

**Files modified:**
- `backend/app/schemas.py` — `tags: Optional[List[TagSuggestion]]` added to `ProductUpdateRequest`
- `backend/app/routers/admin.py` — `PATCH /admin/products/{id}` clears and re-links tags when `tags` provided
- `frontend/src/pages/AdminPanel.jsx` — Rewritten: `ProductRow` component with inline tag editor; `handleToggleActive`/`handleDelete` moved into `ProductRow`
- `frontend/src/pages/AdminPanel.css` — Tag editing row styles (`.admin-panel__edit-tags`, `.admin-panel__tag-edit-row`, save/cancel buttons)

---

### [2026-08-11 | Session 1] — Initial Documentation

**What was added:**
- `PROJECT_OVERVIEW.md` — Comprehensive technical reference: architecture diagram, folder structure, full DB schema, complete API reference, all key workflows, auth design, tag extraction pipeline stages, AI integration details, provider switching, all env vars, local dev setup, deployment guide, and feature roadmap.
- `CHANGELOG.md` — This file. All future changes tracked here.
