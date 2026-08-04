# Raccoon Hub

<p align="center">
  <strong>AI-assisted product discovery for Amazon India.</strong><br />
  Add products from an admin panel, organize them with tags, and publish a clean storefront.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?logo=react&logoColor=white" alt="React and Vite" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/AI-Google%20Gemini-4285F4?logo=google&logoColor=white" alt="Google Gemini" />
</p>

---

## Overview

Raccoon Hub is an affiliate-style product storefront for Amazon India products. It includes a public shop for visitors and a protected admin area where products can be previewed, tagged, saved, hidden, or removed.

Google Gemini generates a short, factual product blurb from a product's title and features. The application uses the Gemini API instead of hosting a large local AI model, keeping the backend lightweight and suitable for a free-tier deployment.

## What it does

| Public shop | Admin dashboard | AI assistance |
| --- | --- | --- |
| Browse active products | Secure admin login | Generates product blurbs during preview |
| View product information and tags | Add a product with an Amazon URL | Stores blurbs in PostgreSQL |
| Open Amazon affiliate links | Edit suggested tags before saving | Does not regenerate blurbs on every visit |
| View product detail pages | Hide or delete products | Continues working if Gemini is unavailable |

## Key features

- Public product catalogue with detail pages, images, price, ratings, features, tags, and affiliate links.
- Admin-only product management using Bearer-token authentication.
- Product preview before saving.
- Automatic tag suggestions, editable by the admin.
- AI-generated product descriptions using Google Gemini.
- Saved AI descriptions shown in the admin preview, expanded cards, and product detail pages.
- PostgreSQL database migrations managed with Alembic.
- Mock product-data provider for local development, with support for Amazon Creators API integration.
- Graceful fallback: a Gemini problem never blocks a product from being saved.

## Architecture

```text
Browser (React + Vite)
          |
          v
FastAPI backend
   |              |
   v              v
PostgreSQL     Google Gemini API
   |
   v
Product data, tags, and saved AI blurbs
```

### AI blurb flow

```text
Admin pastes an Amazon product URL
          |
          v
Backend prepares product title and features
          |
          v
Gemini creates a short product blurb
          |
          v
Admin reviews preview and confirms product
          |
          v
Product, tags, and blurb are stored in PostgreSQL
```

The blurb is generated once during preview and stored in the database. Visitors opening a product page do not trigger another Gemini request.

## Technology stack

| Layer | Tools |
| --- | --- |
| Frontend | React, Vite, React Router, CSS, Lucide React, Motion |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL, Alembic |
| AI | Google Gemini API with `google-genai` |
| Deployment | Render-compatible |

## Project structure

```text
raccoon-hub/
|-- backend/
|   |-- app/
|   |   |-- routers/          # Admin and public API routes
|   |   |-- providers/        # Mock and Amazon product-data providers
|   |   |-- ai_client.py      # Gemini client and AI helpers
|   |   |-- auth.py           # Admin authentication
|   |   |-- models.py         # SQLAlchemy database models
|   |   |-- schemas.py        # API request/response schemas
|   |   `-- main.py           # FastAPI entrypoint
|   |-- alembic/              # Database migrations
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |-- pages/
|   |   `-- api/
|   `-- package.json
`-- README.md
```

## Getting started

### Prerequisites

- Python 3.10 or newer
- Node.js and npm
- PostgreSQL database
- A Google AI Studio API key

### 1. Clone the project

```bash
git clone <your-repository-url>
cd raccoon-hub
```

### 2. Set up the backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure environment variables

Create `backend/.env`:

```env
# Product data
DATA_PROVIDER=mock
AMAZON_ASSOCIATE_TAG=your-associate-tag-21

# Database
DATABASE_URL=your-postgresql-database-url

# Admin authentication
ADMIN_PASSWORD=your-admin-password
SESSION_SECRET_KEY=generate-a-long-random-secret

# AI
GEMINI_API_KEY=your-google-ai-studio-api-key

# Frontend address allowed to call the backend
ALLOWED_ORIGINS=http://localhost:5173
```

> [!WARNING]
> Never commit `.env`, API keys, database URLs, passwords, or session secrets. They are already excluded by `.gitignore`.

### 4. Apply database migrations

```powershell
alembic upgrade head
```

### 5. Run the backend

```powershell
uvicorn app.main:app --reload
```

Backend health check: <http://127.0.0.1:8000/health>
Interactive API docs: <http://127.0.0.1:8000/docs>

### 6. Run the frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite, normally <http://localhost:5173>.

## Testing the AI feature

1. Open `/admin` in the local frontend.
2. Sign in using `ADMIN_PASSWORD`.
3. Paste a full Amazon URL containing `/dp/`.
4. Select **Preview**.
5. Check that an AI blurb appears below the price and availability.
6. Select **Confirm & Add Product**.
7. Open the product from the Shop page and verify the same saved blurb is displayed.

`DATA_PROVIDER=mock` is recommended while developing. It returns predictable demo product data so you can test the complete admin, database, tag, and AI flow without live Amazon credentials.

## Deployment notes

This project is designed to work with a lightweight deployment setup:

- Host the React frontend and FastAPI backend on Render.
- Use a hosted PostgreSQL database.
- Add backend environment variables in the Render dashboard.
- Set `ALLOWED_ORIGINS` to your deployed frontend URL.
- Run `alembic upgrade head` against the production database after deploying a new migration.

Required backend environment variables:

```env
DATA_PROVIDER=mock
AMAZON_ASSOCIATE_TAG=your-associate-tag-21
DATABASE_URL=your-production-database-url
ADMIN_PASSWORD=your-admin-password
SESSION_SECRET_KEY=your-long-random-secret
GEMINI_API_KEY=your-google-ai-studio-api-key
ALLOWED_ORIGINS=https://your-frontend-domain.onrender.com
```

## Roadmap

- [ ] Semantic product search using Gemini embeddings
- [ ] Similar-product recommendations
- [ ] Duplicate product detection
- [ ] Amazon Creators API integration for live product data
- [ ] Price tracking and price-change alerts
- [ ] More filters and sorting options
- [ ] User accounts and wishlists
- [ ] Admin analytics

## Security

- Gemini is called only from the backend; the API key is never sent to the browser.
- Admin routes require a valid Bearer token.
- Sensitive values belong in `.env` locally and deployment environment variables in production.
- AI errors are handled safely so product management continues if Gemini is down, rate-limited, or misconfigured.
