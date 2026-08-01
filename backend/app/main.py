"""
main.py
------------------------------------------------------------------
FastAPI application entrypoint. Run locally with:

    uvicorn app.main:app --reload

Swagger UI (test every endpoint from the browser): /docs
------------------------------------------------------------------
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routers import admin, public

app = FastAPI(title="Raccoon Hub API", version="0.1.0")

# Session cookie middleware - powers the admin login (see app/auth.py).
# See config.py for why SameSite/Secure differ between local dev and production.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    same_site=settings.SESSION_COOKIE_SAMESITE,
    https_only=settings.SESSION_COOKIE_SECURE,
)

# CORS - only the frontend origins listed in ALLOWED_ORIGINS may call this
# API with credentials (cookies). Wildcard "*" cannot be combined with
# allow_credentials=True, so explicit origins are required.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(public.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}