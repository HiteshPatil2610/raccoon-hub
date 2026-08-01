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

from app.config import settings
from app.routers import admin, public

app = FastAPI(title="Raccoon Hub API", version="0.1.0")

# CORS - admin auth is a Bearer token in the Authorization header (see
# app/auth.py), not a cookie, so allow_credentials doesn't need to be True
# here. Still restricting to explicit origins rather than "*" as good
# practice, even though it's no longer strictly required for auth to work.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(public.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}