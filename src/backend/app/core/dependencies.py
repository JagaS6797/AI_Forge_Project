from __future__ import annotations

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.security import decode_access_token


class CurrentUser(BaseModel):
    email: EmailStr


_DEV_USER_EMAIL = "dev@example.com"


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts
    if scheme.lower() != "bearer" or not token:
        return None
    return token


async def get_current_user(request: Request) -> CurrentUser:
    """Resolve the authenticated user from request state.

    In development (ENVIRONMENT=development) and when no auth middleware
    has populated request.state.user, returns a placeholder dev user so
    the app is usable before the auth layer is wired up.
    """
    email = None
    token = _extract_bearer_token(request)
    if token:
        try:
            email = decode_access_token(token)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "unauthorized", "message": "Invalid authentication token"},
            )

    if not email:
        if settings.environment == "development":
            return CurrentUser(email=_DEV_USER_EMAIL)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Authentication required"},
        )

    return CurrentUser(email=email)
