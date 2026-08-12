# Raccoon Hub — Project Overview

> **AI-assisted affiliate product storefront for Amazon India.**
> An admin curates products via a protected dashboard; visitors browse and click through to Amazon.

**Last updated:** 2026-08-11

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Technology Stack](#technology-stack)
3. [Architecture](#architecture)
4. [Folder Structure](#folder-structure)
5. [Database Schema](#database-schema)
6. [API Reference](#api-reference)
7. [Frontend Pages & Components](#frontend-pages--components)
8. [Key Workflows](#key-workflows)
9. [Authentication](#authentication)
10. [Tag Extraction Pipeline](#tag-extraction-pipeline)
11. [AI Integration (Gemini)](#ai-integration-gemini)
12. [Product Data Providers](#product-data-providers)
13. [Environment Variables](#environment-variables)
14. [Running Locally](#running-locally)
15. [Deployment](#deployment)
16. [Feature Status & Roadmap](#feature-status--roadmap)

---

## What It Does

Raccoon Hub is a curated affiliate storefront. The admin manually adds Amazon India products
by pasting a product URL into the admin panel. The backend:

1. Extracts the ASIN from any Amazon URL format (including shortened links).
2. Fetches live product data (title, price, images, features, availability).
3. Runs an NLP tag-extraction pipeline to suggest category, budget tier, spec, and freeform tags.
4. Calls Google Gemini to generate a short product blurb.
5. Shows the admin a full preview — editable tags, blurb, and product details — before saving.
6. On confirm, saves the product + tags to PostgreSQL.

Visitors on the public shop can:
- Browse the product grid with **search**, **tag filters** (grouped by type with counts), and **sort** (newest / price / rating).
- See **out-of-stock** products visually dimmed with a badge.
- Expand a card in-place for a full view with image gallery, AI blurb, features, and buy button.
- Open a dedicated product detail page per product.
- Click through to Amazon via an affiliate link.
- Save favorites locally (localStorage).
- Navigate paginated results (24 per page).

---

## Technology Stack

| Layer | Tools |
|---|---|
| **Frontend** | React 18, Vite 5, React Router 6, Motion (Framer Motion v11), Lucide React |
| **Backend** | Python 3.10+, FastAPI 0.111, SQLAlchemy 2.0, Pydantic v2 |
| **Database** | PostgreSQL, Alembic (migrations) |
| **AI** | Google Gemini API (`google-genai` SDK) — `gemini-flash-latest` for blurbs, `gemini-embedding-001` for embeddings (implemented, pending route wiring) |
| **NLP** | spaCy 3.7 with `en_core_web_sm` model |
| **Auth** | `itsdangerous` URLSafeTimedSerializer — stateless signed Bearer tokens |
| **Deployment** | Render (separate frontend + backend services) |

---

## Architecture

```
Browser (React + Vite SPA)
          │
          │  REST JSON over HTTPS
          ▼
    FastAPI backend  ──────────────────► Google Gemini API
          │                               (blurb generation + embeddings)
          ▼
     PostgreSQL DB
          │
          ▼
Amazon Creators API  (or Mock Provider in local dev)
```

### Why Bearer tokens instead of cookies

The frontend and backend are hosted on different Render subdomains. Because `onrender.com` is on
the Public Suffix List, browsers treat these as separate sites. Safari ITP blocks third-party
cookies by default; Chrome is moving the same direction. A Bearer token sent in the
`Authorization` header completely sidesteps this class of cross-site cookie problem.

---

## Folder Structure

```
raccoon-hub/
├── PROJECT_OVERVIEW.md          ← this file (full technical reference)
├── CHANGELOG.md                 ← all changes with timestamps + pending feature list
├── README.md                    ← quick-start guide
├── render.yaml                  ← Render deployment config
│
├── backend/
│   ├── .env                     ← local secrets (never commit)
│   ├── alembic.ini              ← Alembic migration config
│   ├── requirements.txt
│   │
│   ├── alembic/
│   │   ├── env.py               ← migration environment setup
│   │   └── versions/
│   │       ├── f869c8c6f512_initial_migration.py
│   │       ├── 75aa7c4f5468_add_ai_blurb_column.py
│   │       └── a1b2c3d4e5f6_add_price_history_and_analytics.py  ← NEW
│   │
│   └── app/
│       ├── main.py              ← FastAPI app, CORS, router registration
│       ├── config.py            ← pydantic-settings: all env vars
│       ├── database.py          ← SQLAlchemy engine + session factory
│       ├── models.py            ← ORM models: Product, Tag, PriceHistory   ← UPDATED
│       ├── schemas.py           ← Pydantic request/response models          ← UPDATED
│       ├── auth.py              ← token issue + verify (itsdangerous)
│       ├── ai_client.py         ← Gemini blurb + embedding functions
│       ├── tag_config.py        ← categories, price tiers, spec patterns
│       ├── tag_extractor.py     ← 4-stage NLP tagging pipeline
│       ├── asin_utils.py        ← ASIN extraction + affiliate URL builder
│       │
│       ├── providers/
│       │   ├── __init__.py      ← get_provider() factory (mock vs. real)
│       │   ├── base.py          ← abstract ProductDataProvider interface
│       │   ├── mock_provider.py ← deterministic fake data for local dev
│       │   └── creators_api_provider.py ← Amazon Creators API (OAuth2, pending verification)
│       │
│       └── routers/
│           ├── admin.py         ← /admin/* routes (auth-protected)           ← UPDATED
│           └── public.py        ← /products, /tags, /products/count          ← UPDATED
│
└── frontend/
    ├── .env                     ← VITE_* vars (never commit secrets)
    ├── index.html
    ├── vite.config.js
    ├── package.json
    │
    └── src/
        ├── main.jsx             ← React root, BrowserRouter
        ├── App.jsx              ← header, nav, route definitions
        ├── App.css
        ├── index.css            ← global styles, CSS variables
        │
        ├── api/
        │   └── client.js        ← fetch wrapper, Bearer token management      ← UPDATED
        │
        ├── pages/
        │   ├── Home.jsx / .css          ← product grid + search + sort + sidebar + pagination  ← UPDATED
        │   ├── ProductDetail.jsx / .css ← single product full page
        │   └── AdminPanel.jsx / .css    ← admin dashboard + inline tag editing  ← UPDATED
        │
        └── components/
            ├── ProductCard.jsx / .css   ← collapsed/expanded card + OOS badge  ← UPDATED
            ├── ImageGallery.jsx / .css  ← main + thumbnail image viewer
            ├── BuyButton.jsx / .css     ← Amazon affiliate link button
            ├── StarRating.jsx / .css    ← star display + review count
            ├── TagChipEditor.jsx / .css ← admin tag add/remove UI
            ├── HeroPixelReveal.jsx / .css  ← home page hero animation
            └── PageRevealOverlay.jsx / .css ← page entrance animation
```

---

## Database Schema

### Table: `products`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Auto-generated `uuid4()` |
| `asin` | VARCHAR(10) | Unique, indexed |
| `original_url` | TEXT | The exact URL pasted by the admin |
| `title` | TEXT | Product title |
| `price_display` | VARCHAR(50) | Human-readable, e.g. `"₹1,299"` |
| `price_amount` | NUMERIC(10,2) | Numeric price for sorting/filtering |
| `currency` | VARCHAR(3) | Default `"INR"` |
| `availability` | VARCHAR(30) | e.g. `"In Stock"`, `"Out of Stock"` |
| `star_rating` | FLOAT | Nullable |
| `review_count` | INTEGER | Nullable |
| `image_large_url` | TEXT | Main product image URL |
| `image_variants` | JSONB | `list[str]` — additional image URLs |
| `features` | JSONB | `list[str]` — bullet-point features |
| `category` | VARCHAR(100) | Primary category slug, e.g. `"gaming-mouse"` |
| `ai_blurb` | TEXT | Gemini-generated 2-3 sentence description |
| `is_active` | BOOLEAN | Default `true`. Controls public visibility |
| `view_count` | INTEGER | **NEW** — incremented on each detail page load |
| `click_count` | INTEGER | **NEW** — incremented when Buy button is clicked |
| `last_fetched_at` | DATETIME | Last live fetch timestamp |
| `created_at` | DATETIME | When the product was added |

### Table: `tags`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Auto-generated |
| `name` | VARCHAR(100) | Unique, indexed. Slugified, e.g. `"gaming-mouse"`, `"16000-dpi"` |
| `tag_type` | VARCHAR(30) | One of: `category`, `budget_tier`, `spec`, `freeform` |

### Table: `product_tags` (join)

| Column | Type | Notes |
|---|---|---|
| `product_id` | UUID (FK → products.id) | CASCADE DELETE |
| `tag_id` | UUID (FK → tags.id) | CASCADE DELETE |

### Table: `price_history` *(NEW)*

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Auto-generated |
| `product_id` | UUID (FK → products.id) | CASCADE DELETE, indexed |
| `price_amount` | NUMERIC(10,2) | Price at time of recording |
| `price_display` | VARCHAR(50) | Human-readable price at that time |
| `recorded_at` | DATETIME | When this price was observed |

> One row is written whenever the live-fetch detects a price change on a product detail page load.
> Used for sparkline price-trend charts on the product detail page *(route + frontend pending)*.

### Tag Types Explained

| Type | Description | Example |
|---|---|---|
| `category` | Top-level category (spaCy PhraseMatcher) | `gaming-mouse`, `headphone` |
| `budget_tier` | Price bracket classification | `budget`, `mid-range`, `premium` |
| `spec` | Numeric spec (regex) | `16000-dpi`, `120-hz`, `10000-mah` |
| `freeform` | Descriptive noun-chunk (spaCy) | `rgb-lighting`, `ergonomic-grip` |

### Migrations (Alembic)

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe the change"
```

Current migrations (in order):
1. `f869c8c6f512` — Initial migration (all base tables)
2. `75aa7c4f5468` — Add `ai_blurb` column to products
3. `a1b2c3d4e5f6` — Add `price_history` table + `view_count`/`click_count` to products

---

## API Reference

### Public Endpoints (no authentication)

#### `GET /health`
Health check. Returns `{"status": "ok"}`.

#### `GET /products`
Paginated, filterable, sortable, searchable list of active products.

| Query Param | Type | Default | Description |
|---|---|---|---|
| `tag` | string | — | Filter by tag name, e.g. `gaming-mouse` |
| `category` | string | — | Filter by category slug |
| `search` | string | — | Case-insensitive title search (`ILIKE`) |
| `sort` | string | `newest` | `newest` / `price_asc` / `price_desc` / `rating` |
| `limit` | int | 24 | Max results (1–100) |
| `offset` | int | 0 | Skip N products (for pagination) |

Response: `List[ProductOut]` — only `is_active=True` products, served from DB cache.

#### `GET /products/count`
Returns total matching count for the same filter params as `GET /products`.
Used by the frontend pagination UI.

Response: `{"total": 42}`

#### `GET /products/{asin}`
Full product detail. **Live-fetches** from the configured provider; silently falls back to
cached DB data if the live call fails or is rate-limited. Updates `last_fetched_at` on success.

Response: `ProductDetailOut` (includes `original_url`)

#### `GET /tags`
All distinct tags with per-tag active product counts, ordered by `tag_type` then `name`.
Used by the filter sidebar.

Response: `List[TagOut]` — each tag includes `product_count`

---

### Admin Endpoints (`/admin/*` — Bearer token required)

#### `POST /admin/login`
```json
Request:  { "password": "your-admin-password" }
Response: { "token": "<signed-token>" }
```
Token is valid for 7 days. Stored in frontend `localStorage`.

#### `POST /admin/logout`
No-op (stateless tokens). Frontend simply clears the token from localStorage.

#### `POST /admin/products/preview`
```json
Request:  { "url": "https://www.amazon.in/dp/B0XXXXXXXXXX" }
Response: { "product": { ...ProductPreviewData }, "suggested_tags": [...TagSuggestion] }
```
Pipeline: extract ASIN → fetch product data → run tag pipeline → generate Gemini blurb.
**Nothing is saved to the DB yet.**

#### `POST /admin/products/confirm`
```json
Request:  { "product": { ...ProductPreviewData }, "final_tags": [...TagSuggestion] }
Response: ProductOut
```
Saves product + admin-edited tags to the database. Returns `409` if ASIN already exists.

#### `GET /admin/products`
Returns all products including inactive ones (unlike the public listing). `List[ProductOut]`

#### `PATCH /admin/products/{id}`
```json
Request:  { "category": "gaming-mouse", "is_active": false, "tags": [...TagSuggestion] }
Response: ProductOut
```
Updates category, active status, and/or tags. When `tags` is provided, **all existing tags are
replaced** with the new list. The `ProductRow` component in `AdminPanel.jsx` uses this for
inline tag editing.

#### `DELETE /admin/products/{id}`
Hard-deletes a product and all its tag associations. Response: `{"status": "deleted"}`

---

## Frontend Pages & Components

### Pages

#### `Home` (`/`)
- Loads all tags on mount and populates the grouped filter sidebar (Category / Budget / Spec / Style).
- Sidebar shows per-tag product counts. Collapses to horizontal pill row on mobile.
- Toolbar row: **search input** (300ms debounce, `ILIKE` on title) + **sort dropdown** (Newest / Price ↑ / Price ↓ / Rating).
- Fetches products + total count in parallel on every filter/sort/search/page change.
- **Pagination**: Prev/Next controls; 24 products per page.
- Uses Motion `LayoutGroup` for animated grid reflow on card expand/collapse.
- Single-expansion model: only one `ProductCard` is expanded at a time.

#### `ProductDetail` (`/product/:asin`)
- Fetches live product data on mount via `GET /products/{asin}`.
- Displays: `ImageGallery`, `StarRating`, price, availability badge, tag chips (styled by type), AI blurb, feature bullet list, `BuyButton`.
- Back link to home.
- *(Price sparkline chart — pending Feature 6)*

#### `AdminPanel` (`/admin`)
- On load, checks `localStorage` for a valid token; shows login form if absent.
- **Add product flow**: URL input → Preview (fetches + shows blurb + tag suggestions) → `TagChipEditor` → Confirm & Save.
- **Existing products table**: each row is a `ProductRow` component with:
  - Toggle Active/Hidden button
  - **Tags button** — expands an inline `TagChipEditor` row; Save/Cancel saves via `PATCH /admin/products/{id}`
  - Delete button (with confirmation dialog)

### Key Components

| Component | Description | Recent changes |
|---|---|---|
| `ProductCard` | Two-state animated card (collapsed / expanded). Favorites in `localStorage`. | Added `is-out-of-stock` class, greyscale overlay, red "Out of Stock" badge |
| `ImageGallery` | Main image + variant thumbnails | — |
| `BuyButton` | Amazon affiliate link (`/dp/{asin}?tag={associate_tag}`) | — |
| `StarRating` | Visual star display + review count | — |
| `TagChipEditor` | Add/remove tag chips — used in admin preview and inline row editor | — |
| `HeroPixelReveal` | Home page hero pixel animation | — |
| `PageRevealOverlay` | Full-page entrance animation on route load | — |

---

## Key Workflows

### Admin: Add a Product

```
Admin pastes Amazon URL into the Add Product form
      │
      ▼
POST /admin/products/preview
      │
      ├─► asin_utils.extract_asin()     → extract ASIN (follow redirect if shortened)
      ├─► provider.fetch_product(asin)  → fetch title, price, images, features
      ├─► tag_extractor.extract_tags()  → suggest category, budget tier, spec, freeform tags
      └─► ai_client.generate_blurb()    → Gemini writes 2-3 sentence description
      │
      ▼
Admin reviews preview:
  - sees product image, title, price, availability
  - sees AI blurb
  - edits suggested tags via TagChipEditor (add / remove chips)
      │
      ▼
POST /admin/products/confirm
      │
      └─► Product + Tags saved to PostgreSQL
```

### Admin: Edit Tags on an Existing Product

```
Admin clicks "Tags (N)" button on a product row
      │
      ▼
Inline TagChipEditor appears below the row
      │
Admin adds / removes chips, clicks "Save tags"
      │
      ▼
PATCH /admin/products/{id}  { tags: [...] }
      │
      └─► Backend clears old tags, re-links new ones, returns updated product
```

### Public: Browse the Shop

```
Browser loads /
      │
      ▼
GET /tags          → populate grouped filter sidebar with counts
GET /products      → first page of products (DB cache, no external API)
GET /products/count → total matching for pagination UI
      │
      ▼
User types in search box (300ms debounce)
  → new GET /products?search=... + GET /products/count?search=...

User picks a tag from sidebar
  → new GET /products?tag=... + count

User changes sort dropdown
  → new GET /products?sort=price_asc + count

User clicks Prev / Next
  → new GET /products?offset=24 + count
      │
      ▼
User clicks a card → animates expand in-place (Motion layout)
User clicks "View full page" → /product/:asin
  → GET /products/{asin}  (live fetch, DB fallback)
```

### AI Blurb Flow

```
Admin triggers preview
      │
      ▼
ai_client.generate_product_blurb(title, features)
      │
      ├── GEMINI_API_KEY missing?  → return None  (no blurb, product saves fine)
      ├── API call fails / limit?  → return None  (fail soft)
      └── Success → return 2-3 sentence plain-text description
      │
      ▼
Blurb stored once in products.ai_blurb at confirm time
      │
      ▼
Served to all visitors from DB — zero per-visit Gemini calls
```

---

## Authentication

**Type:** Stateless signed Bearer token — no server-side session store required.
**Library:** `itsdangerous.URLSafeTimedSerializer`
**Token expiry:** 7 days

**Flow:**
1. Admin POSTs password to `POST /admin/login`.
2. Backend compares against `ADMIN_PASSWORD` env var.
3. On success, issues a signed token (`{"admin": true}` payload, signed with `SESSION_SECRET_KEY`).
4. Frontend stores token in `localStorage` under key `raccoon_hub_admin_token`.
5. Every admin request attaches `Authorization: Bearer <token>`.
6. `require_admin` FastAPI dependency validates signature + expiry on every protected route.
7. Any `401` response clears the token from `localStorage` and reverts the UI to the login screen.

**Why not cookies:** Frontend and backend live on different Render subdomains. `onrender.com` is
on the Public Suffix List — browsers treat them as separate sites. Safari ITP blocks third-party
cookies in this exact setup by default; Chrome is moving the same way. Bearer tokens in headers
bypass this entirely.

---

## Tag Extraction Pipeline

Runs against the combined `title + features` text for every product preview.
Results are suggestions only — admin reviews and edits before confirming.

### Stage 1 — Category (spaCy PhraseMatcher)
- `PhraseMatcher` built once at import time from `CATEGORIES` in `tag_config.py`.
- 13 categories, ordered most-specific-first (e.g. `gaming-mouse` before `mouse`).
- First matching category in priority order wins.

### Stage 2 — Budget Tier (price rule)
- Compares `price_amount` against per-category thresholds from `BUDGET_TIER_THRESHOLDS`.
- Result: `budget`, `mid-range`, or `premium`.
- Falls back to `DEFAULT_BUDGET_TIER_THRESHOLDS` for uncategorised products.

### Stage 3 — Spec Tags (regex)
- 7 patterns in `SPEC_PATTERNS`: DPI, Hz, mAh, GB, GHz, Watt, inch.
- Format: `(\d+)\s?unit` → tag: `{number}-{unit}`, e.g. `16000-dpi`, `120-hz`.

### Stage 4 — Freeform Tags (spaCy noun chunks)
- Noun-chunk extraction filtered by: min 3 chars, max 3 words, not in `FREEFORM_STOPWORDS`.
- Slugified and deduplicated. Max `MAX_FREEFORM_TAGS` (default: 8).

---

## AI Integration (Gemini)

**File:** `backend/app/ai_client.py`

### `generate_product_blurb(title, features) → str | None`
- Model: `gemini-flash-latest`
- Writes 2-3 factual sentences, no marketing fluff, plain text only.
- Called once per product during admin preview; stored in `products.ai_blurb`.
- Served from DB to all visitors — no per-visit API calls.
- Returns `None` on missing key, rate limit, or any exception (fail soft).

### `embed_text(text) → list[float] | None`
- Model: `gemini-embedding-001`
- Foundation for semantic search, "similar products", and duplicate detection.
- Implemented but **not yet wired to any route** (pending Feature 1 — see Roadmap).
- Returns `None` on any failure (fail soft).

---

## Product Data Providers

Controlled by `DATA_PROVIDER` env var. `get_provider()` in `providers/__init__.py` is the
single switch point — no other code needs to change when switching providers.

### Mock Provider (`DATA_PROVIDER=mock`) — **default**
- Generates deterministic fake data seeded by ASIN hash (same ASIN → same data always).
- INR prices range ₹299–₹24,999. Placeholder images from `placehold.co`.
- No external API calls. Use this for all local development.

### Amazon Creators API Provider (`DATA_PROVIDER=creators_api`)
- Replaces the retired PA-API 5.0.
- Auth: OAuth 2.0 client-credentials via Login-With-Amazon (`https://api.amazon.com/auth/o2/token`, scope `creatorsapi::catalog`). Token cached in-memory.
- Product fetch: `POST https://creatorsapi.amazon/catalog/v1/getItems`
- **Status: written from migration docs. Not yet verified against live credentials.**
  Response field paths may need adjustment once real credentials are available.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `ADMIN_PASSWORD` | ✅ | — | Single admin login password |
| `SESSION_SECRET_KEY` | ✅ | — | Long random string for token signing |
| `AMAZON_ASSOCIATE_TAG` | ✅ | — | Amazon associate tag (must end in `-21` for India) |
| `ALLOWED_ORIGINS` | ✅ | `http://localhost:5173` | Comma-separated CORS allow-list |
| `DATA_PROVIDER` | ❌ | `mock` | `mock` or `creators_api` |
| `GEMINI_API_KEY` | ❌ | `None` | Google AI Studio API key (get free at aistudio.google.com) |
| `CREATORS_API_CLIENT_ID` | ❌ | `None` | Required only when `DATA_PROVIDER=creators_api` |
| `CREATORS_API_CLIENT_SECRET` | ❌ | `None` | Required only when `DATA_PROVIDER=creators_api` |
| `CREATORS_API_MARKETPLACE` | ❌ | `www.amazon.in` | Amazon marketplace domain |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Backend API base URL |
| `VITE_AMAZON_ASSOCIATE_TAG` | — | Associate tag for affiliate buy links |

---

## Running Locally

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows PowerShell
source venv/bin/activate       # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Download the spaCy language model
python -m spacy download en_core_web_sm

# Create backend/.env and fill in values (see Environment Variables above)

# Apply all DB migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload
# → API:       http://127.0.0.1:8000
# → Swagger:   http://127.0.0.1:8000/docs
# → Health:    http://127.0.0.1:8000/health
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Deployment

Hosted on **Render** as two separate services:

| Service | Type | Build Command | Start Command |
|---|---|---|---|
| Backend | Web Service (Python) | `pip install -r requirements.txt && python -m spacy download en_core_web_sm && alembic upgrade head` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Frontend | Static Site | `npm run build` | — (Render serves `dist/`) |

Set `ALLOWED_ORIGINS` on the backend to the frontend's Render URL.
Set `VITE_API_BASE_URL` on the frontend to the backend's Render URL.
All other secrets are set as environment variables in each service's Render dashboard.

---

## Feature Status & Roadmap

### Completed Features

| # | Feature | Status |
|---|---|---|
| — | Project documentation (`PROJECT_OVERVIEW.md`, `CHANGELOG.md`) | ✅ Done |
| 5 | Tag editing on existing products (inline in admin table) | ✅ Done |
| 11 | Pagination on the home grid (24/page, Prev/Next) | ✅ Done |
| 12 | Sort options (Newest / Price ↑↓ / Rating) | ✅ Done |
| 3 | Tag filter sidebar with counts and type grouping | ✅ Done |
| 4 | Text search (debounced, ILIKE on title) | ✅ Done |
| 13 | Out-of-stock visual treatment (badge + greyscale) | ✅ Done |
| 6 | Price history model + DB migration | ✅ Data layer done |

### Pending Features

| # | Feature | Status |
|---|---|---|
| 6 | Price history sparkline chart (routes + frontend) | ⏳ In progress |
| 7 | Bulk import from CSV / URL list | ⏳ Not started |
| 9 | Admin analytics (view/click counters) — model done | ⏳ Routes + frontend pending |
| 10 | Daily product refresh via APScheduler background job | ⏳ Not started |
| 1 | Semantic search / "Similar Products" (pgvector + Gemini) | ⏳ Not started |
| 14 | SEO / Open Graph meta tags on product detail pages | ⏳ Not started |
| 2 | Amazon Creators API live verification + debug logging | ⏳ Not started |

> See `CHANGELOG.md` for the exact remaining work (files to create/edit) for each pending feature.
