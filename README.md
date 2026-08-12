# Raccoon Hub

<p align="center">
  <strong>AI-assisted product discovery for Amazon India.</strong><br />
  Curate products from an admin panel, auto-tag them with NLP, generate AI blurbs, and publish a clean storefront.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?logo=react&logoColor=white" alt="React and Vite" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/AI-Google%20Gemini-4285F4?logo=google&logoColor=white" alt="Google Gemini" />
  <img src="https://img.shields.io/badge/NLP-spaCy-09A3D5?logo=spacy&logoColor=white" alt="spaCy" />
</p>

---

## Overview

Raccoon Hub is a curated affiliate storefront for Amazon India. An admin adds products by pasting any Amazon URL — the backend extracts the ASIN, fetches product data, runs a 4-stage NLP tag pipeline, and calls Google Gemini to write a product blurb. The admin reviews everything in a preview, edits the tags, then confirms. Visitors browse a fast, cached public shop and click through to Amazon via affiliate links.

---

## What it does

| Public shop | Admin dashboard | AI + NLP |
|---|---|---|
| Search products by title | Secure single-admin login | Gemini writes product blurbs |
| Filter by tag (grouped: Category / Budget / Spec / Style) | Add a product from any Amazon URL | spaCy extracts category, spec, freeform tags |
| Sort by newest, price, or rating | Preview before saving (no DB write) | Budget tier classified by price rules |
| Paginated grid (24 per page) | Edit suggested tags before confirming | Blurb stored once, served from DB |
| Expand card in-place for full details | Inline tag editing on existing products | Embeddings for similar-product search |
| Dedicated product detail page | Bulk import up to 20 URLs at once | Fails soft — never blocks saving |
| Out-of-stock badge + greyscale | Toggle product visibility (active/hidden) | |
| Price history sparkline chart | Delete products | |
| Similar products section | Analytics: view + click counters | |
| Amazon affiliate buy links | Daily auto-refresh of all products | |
| Favorites saved in localStorage | | |

---

## Key features

- **Smart tag pipeline** — 4 stages: spaCy PhraseMatcher (category), price-rule (budget tier), regex (specs like `16000-dpi`, `120-hz`), spaCy noun chunks (freeform). All suggestions, admin-editable before saving.
- **AI product blurbs** — Gemini writes a 2-3 sentence description per product at preview time. Stored in DB, never regenerated per visitor. Works fine if Gemini is unavailable.
- **Preview → Confirm flow** — Nothing is saved until the admin explicitly confirms. Tags can be freely edited between preview and confirm.
- **Inline tag editing** — Tags on existing products can be edited directly in the admin table without re-adding the product.
- **Bulk import** — Paste up to 20 Amazon URLs (or upload a CSV) to preview-and-save multiple products at once.
- **Price history** — Records a price history entry whenever the live-fetch detects a price change. Shown as a sparkline chart on the product detail page.
- **Similar products** — Gemini embeddings stored via pgvector. Falls back to same-category products when pgvector is unavailable.
- **Daily refresh** — APScheduler job at 03:00 UTC re-fetches all active products and updates cached price, availability, and images.
- **Analytics** — View count per product detail page, click count per Buy button click. Admin dashboard shows top products.
- **SEO** — Dynamic `og:title`, `og:description`, `og:image`, `og:url` meta tags on product detail pages.
- **Bearer token auth** — Stateless signed tokens (`itsdangerous`). Works across different subdomains without cookie issues.

---

## Architecture

```
Browser (React + Vite SPA)
          │
          │  REST JSON
          ▼
    FastAPI backend ──────────────────► Google Gemini API
          │                              (blurbs + embeddings)
          ▼
     PostgreSQL DB
          │
          ▼
  Amazon Creators API  (or Mock Provider in local dev)
```

### Admin: add a product

```
Paste Amazon URL
      │
      ▼  extract ASIN → fetch product data → NLP tag pipeline → Gemini blurb
      │
      ▼
Admin reviews preview (edits tags)
      │
      ▼
Confirm → saved to PostgreSQL
```

---

## Technology stack

| Layer | Tools |
|---|---|
| **Frontend** | React 18, Vite 5, React Router 6, Motion (Framer Motion v11), Lucide React |
| **Backend** | Python 3.10+, FastAPI, SQLAlchemy 2, Pydantic v2, APScheduler |
| **Database** | PostgreSQL, Alembic migrations, pgvector (optional, for semantic search) |
| **AI / NLP** | Google Gemini API (`google-genai`), spaCy `en_core_web_sm` |
| **Auth** | `itsdangerous` URLSafeTimedSerializer — stateless Bearer tokens |
| **Deployment** | Render (separate frontend + backend services) |

---

## Project structure

```
raccoon-hub/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── admin.py          # All admin routes (auth-protected)
│   │   │   └── public.py         # Public routes (no auth)
│   │   ├── providers/
│   │   │   ├── mock_provider.py  # Fake data for local dev
│   │   │   └── creators_api_provider.py  # Amazon Creators API
│   │   ├── main.py               # FastAPI app + scheduler lifespan
│   │   ├── models.py             # ORM: Product, Tag, PriceHistory
│   │   ├── schemas.py            # Pydantic request/response models
│   │   ├── scheduler.py          # Daily product refresh job
│   │   ├── ai_client.py          # Gemini blurb + embedding functions
│   │   ├── tag_extractor.py      # 4-stage NLP tag pipeline
│   │   ├── tag_config.py         # Tag taxonomy config
│   │   ├── asin_utils.py         # ASIN extraction + affiliate URL builder
│   │   ├── auth.py               # Token issue + verify
│   │   └── config.py             # All env vars via pydantic-settings
│   ├── alembic/                  # DB migrations
│   └── requirements.txt
│
└── frontend/
    └── src/
        ├── pages/
        │   ├── Home.jsx           # Grid + search + sort + sidebar + pagination
        │   ├── ProductDetail.jsx  # Detail page + sparkline + similar products
        │   └── AdminPanel.jsx     # Full admin dashboard
        ├── components/
        │   ├── ProductCard.jsx    # Collapsed/expanded animated card
        │   ├── PriceSparkline.jsx # SVG price history chart
        │   ├── BuyButton.jsx      # Affiliate link + click tracking
        │   ├── ImageGallery.jsx
        │   ├── StarRating.jsx
        │   └── TagChipEditor.jsx  # Tag add/remove UI
        └── api/
            └── client.js          # Fetch wrapper + Bearer token management
```

---

## Database tables

| Table | Purpose |
|---|---|
| `products` | All product data: title, price, images, features, AI blurb, availability, view/click counts |
| `tags` | Slugified tags with type (`category`, `budget_tier`, `spec`, `freeform`) |
| `product_tags` | Many-to-many join (CASCADE delete) |
| `price_history` | One row per price change detected on live-fetch |

---

## Getting started

### Prerequisites

- Python 3.10+
- Node.js and npm
- PostgreSQL database
- Google AI Studio API key (free at [aistudio.google.com](https://aistudio.google.com))

### 1. Clone

```bash
git clone <your-repository-url>
cd raccoon-hub
```

### 2. Backend setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Environment variables

Create `backend/.env`:

```env
DATA_PROVIDER=mock
AMAZON_ASSOCIATE_TAG=your-tag-21
DATABASE_URL=postgresql://user:pass@localhost:5432/raccoon_hub
ADMIN_PASSWORD=your-admin-password
SESSION_SECRET_KEY=generate-a-long-random-string-here
GEMINI_API_KEY=your-gemini-api-key
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_AMAZON_ASSOCIATE_TAG=your-tag-21
```

> **Never commit `.env` files.** They are already in `.gitignore`.

> **Important:** Do not put inline `#` comments on the same line as a value in `.env`.
> `pydantic-settings` reads them as part of the value, not as comments.

### 4. Apply migrations

```powershell
alembic upgrade head
```

### 5. Run the backend

```powershell
uvicorn app.main:app --reload
```

- API: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/health>

### 6. Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>

---

## Admin panel walkthrough

1. Go to `/admin` and log in with your `ADMIN_PASSWORD`.
2. **Add a product** — paste any Amazon.in URL (full `/dp/` link or shortened `amzn.in`). Click **Preview**.
3. Review the fetched data: image, title, price, availability, AI blurb, and suggested tags.
4. Edit tags using the tag chip editor (add / remove).
5. Click **Confirm & Add Product** — saved to the database.
6. **Bulk import** — paste multiple URLs (one per line) or upload a CSV with a `url` column. Preview all at once.
7. **Manage products** — toggle Active/Hidden, edit tags inline, delete.
8. **Analytics** — view the most-viewed and most-clicked products at the bottom of the panel.

> Use `DATA_PROVIDER=mock` while developing — it generates realistic fake data so you can test the full flow without Amazon credentials.

---

## Deployment

Deploy as two separate services on **Render**:

| Service | Type | Build | Start |
|---|---|---|---|
| Backend | Web Service (Python) | `pip install -r requirements.txt && python -m spacy download en_core_web_sm && alembic upgrade head` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Frontend | Static Site | `npm run build` | — |

Set `ALLOWED_ORIGINS` on the backend to your frontend's Render URL.
Set `VITE_API_BASE_URL` on the frontend to your backend's Render URL.

> **pgvector (optional):** Render's managed PostgreSQL supports pgvector. After deploying, run `alembic upgrade head` to apply the embedding migration. Similar-product search will then use real Gemini embeddings instead of the same-category fallback.

---

## Security notes

- The Gemini API key is only ever used server-side — never sent to the browser.
- Admin routes require a valid signed Bearer token (7-day expiry).
- Tokens are stored in `localStorage` and sent in the `Authorization` header. Cleared automatically on any 401.
- All secrets belong in `.env` locally and Render environment variables in production.
- AI/provider errors are swallowed gracefully — a Gemini outage or rate limit never blocks product saving.
