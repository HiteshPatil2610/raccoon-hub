"""
auth.py
------------------------------------------------------------------
Token-based admin auth. Chosen over cookie-based sessions because
the frontend and backend live on different subdomains in production
(different "sites" from a browser's perspective, since onrender.com
itself is on the Public Suffix List). Modern browsers increasingly
block third-party cookies in exactly this cross-site setup (Safari's
ITP does by default; Chrome is moving the same direction), which
made session cookies unreliable here regardless of SameSite/Secure
configuration. A bearer token sent explicitly in the Authorization
header sidesteps that entire class of problem.

Uses itsdangerous (already a dependency, no new package needed) for
a signed, timestamped, stateless token - no server-side session
store required. The frontend is responsible for storing the token
(localStorage) and attaching it to every admin request.
------------------------------------------------------------------
"""

from typing import Optional

from fastapi import Header, HTTPException, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings

_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 7  # 7 days
_serializer = URLSafeTimedSerializer(settings.SESSION_SECRET_KEY, salt="admin-auth")


def verify_password(password: str) -> bool:
    return password == settings.ADMIN_PASSWORD


def issue_token() -> str:
    """Call after a successful password check to generate the admin's token."""
    return _serializer.dumps({"admin": True})


def _verify_token(token: str) -> bool:
    try:
        data = _serializer.loads(token, max_age=_TOKEN_MAX_AGE_SECONDS)
        return bool(data.get("admin"))
    except (BadSignature, SignatureExpired):
        return False


def require_admin(authorization: Optional[str] = Header(default=None)) -> None:
    """
    FastAPI dependency - expects an `Authorization: Bearer <token>` header.
    Raises 401 if missing, malformed, expired, or invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin login required.",
        )

    token = authorization[len("Bearer "):].strip()
    if not _verify_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin login required.",
        )