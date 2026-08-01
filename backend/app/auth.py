"""
auth.py
------------------------------------------------------------------
Simple password-based admin auth using a signed session cookie
(via Starlette's SessionMiddleware, added in main.py). No user
accounts, no JWT - just a single admin password, matching Phase-0
scope ("just for you").
------------------------------------------------------------------
"""

from fastapi import HTTPException, Request, status

from app.config import settings


def verify_password(password: str) -> bool:
    return password == settings.ADMIN_PASSWORD


def login(request: Request, password: str) -> bool:
    """On success, marks this browser session as admin-authenticated."""
    if verify_password(password):
        request.session["is_admin"] = True
        return True
    return False


def logout(request: Request) -> None:
    request.session.pop("is_admin", None)


def require_admin(request: Request) -> None:
    """
    FastAPI dependency - raise 401 if the current session isn't
    logged in as admin. Use via `Depends(require_admin)` on any
    route that pastes/edits/deletes products.
    """
    if not request.session.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin login required.",
        )