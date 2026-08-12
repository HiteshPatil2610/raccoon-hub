"""
main.py
------------------------------------------------------------------
FastAPI application entrypoint. Run locally with:

    uvicorn app.main:app --reload

Swagger UI (test every endpoint from the browser): /docs
------------------------------------------------------------------
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, public
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background jobs on startup; stop them on shutdown."""
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Raccoon Hub API", version="0.2.0", lifespan=lifespan)

# CORS — Bearer token auth, not cookies, so allow_credentials stays False.
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
