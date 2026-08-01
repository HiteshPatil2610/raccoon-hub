"""
config.py
------------------------------------------------------------------
Centralised environment configuration for Raccoon Hub backend.

All secrets/config are read from environment variables so nothing
sensitive is hardcoded. Locally, create a `.env` file in `backend/`
(never commit it). On Render, set these as environment variables in
the service's dashboard.
------------------------------------------------------------------
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Data provider switch ---
    # "mock"          -> fake deterministic product data, no Amazon API needed.
    #                    Use this until Creators API credentials are issued.
    # "creators_api"  -> real Amazon Creators API (PA-API 5.0's replacement).
    DATA_PROVIDER: str = "mock"

    # --- Amazon Associates ---
    # Still required even in mock mode, since it's used to build the
    # outbound "Buy on Amazon" affiliate link (see asin_utils.build_affiliate_url).
    AMAZON_ASSOCIATE_TAG: str  # must end in -21 for India

    # --- Amazon Creators API credentials (PA-API 5.0's replacement) ---
    # Optional because they won't exist until Amazon issues them. Only
    # required when DATA_PROVIDER=creators_api.
    CREATORS_API_CLIENT_ID: str | None = None
    CREATORS_API_CLIENT_SECRET: str | None = None
    CREATORS_API_MARKETPLACE: str = "www.amazon.in"

    # --- Database ---
    DATABASE_URL: str  # e.g. postgresql://user:pass@host:5432/dbname

    # --- Admin auth ---
    ADMIN_PASSWORD: str
    SESSION_SECRET_KEY: str  # random long string, used to sign the session cookie

    # --- CORS ---
    # Comma-separated list of allowed frontend origins, e.g.
    # "http://localhost:5173,https://your-frontend.onrender.com"
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # --- Session cookie ---
    # Local dev (http://localhost): keep the defaults below (lax/False).
    # Production (frontend and backend on different Render subdomains -
    # a cross-site setup from the browser's perspective): set
    # SESSION_COOKIE_SAMESITE=none and SESSION_COOKIE_SECURE=true, or the
    # admin session cookie will silently fail to be sent on API calls.
    SESSION_COOKIE_SAMESITE: str = "lax"
    SESSION_COOKIE_SECURE: bool = False

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()