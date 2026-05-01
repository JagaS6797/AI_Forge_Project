from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import CurrentUser, get_current_user
from app.core.passwords import hash_password, verify_password
from app.core.security import create_access_token
from app.db.session import get_db_session
from app.models.auth_credential import AuthCredential
from app.models.user import User
from app.schemas.auth import AuthUser, GoogleLoginRequest, LoginRequest, LoginResponse, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)

_AMZUR_DOMAIN = "@amzur.com"


def _validate_amzur_email(email: str) -> str:
    email = email.lower().strip()
    if not email.endswith(_AMZUR_DOMAIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Only Amzur employee accounts are allowed"},
        )
    return email


async def _ensure_user_row(db: AsyncSession, email: str) -> None:
    try:
        existing = await db.scalar(select(User).where(User.email == email))
        if not existing:
            db.add(User(email=email))
            await db.commit()
    except Exception:
        logger.exception("Could not upsert user row. Continuing.")


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> LoginResponse:
    email = _validate_amzur_email(payload.user_id)

    try:
        existing = await db.scalar(select(AuthCredential).where(AuthCredential.email == email))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "conflict", "message": "An account with this email already exists"},
            )
        db.add(AuthCredential(email=email, password_hash=hash_password(payload.password)))
        await db.commit()
        await _ensure_user_row(db, email)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Database error during registration.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "db_error", "message": "Database unavailable. Try again later."},
        )

    token = create_access_token(email=email)
    return LoginResponse(access_token=token, user=AuthUser(email=email))


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> LoginResponse:
    email = _validate_amzur_email(payload.user_id)

    try:
        credential = await db.scalar(select(AuthCredential).where(AuthCredential.email == email))
    except Exception:
        logger.exception("Database error during login.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "db_error", "message": "Database unavailable. Try again later."},
        )

    if not credential or not verify_password(payload.password, credential.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Invalid user ID or password"},
        )

    await _ensure_user_row(db, email)
    token = create_access_token(email=email)
    return LoginResponse(access_token=token, user=AuthUser(email=email))


@router.post("/google", response_model=LoginResponse)
async def google_login(
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> LoginResponse:
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "not_configured", "message": "Google login is not configured"},
        )

    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        idinfo = google_id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.google_client_id,
            clock_skew_in_seconds=10,
        )
        email: str = idinfo["email"]
    except Exception as exc:
        logger.exception("Google token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": f"Google authentication failed: {exc}"},
        )

    email = _validate_amzur_email(email)
    await _ensure_user_row(db, email)
    token = create_access_token(email=email)
    return LoginResponse(access_token=token, user=AuthUser(email=email))


@router.get("/me", response_model=AuthUser)
async def me(current_user: CurrentUser = Depends(get_current_user)) -> AuthUser:
    return AuthUser(email=current_user.email)
