from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.auth import _validate_amzur_email
from app.core.security import create_access_token, decode_access_token


def test_validate_amzur_email_accepts_valid_domain() -> None:
    assert _validate_amzur_email("User@Amzur.com") == "user@amzur.com"


def test_validate_amzur_email_rejects_non_amzur_domain() -> None:
    with pytest.raises(HTTPException) as exc:
        _validate_amzur_email("user@example.com")

    assert exc.value.status_code == 403


def test_access_token_round_trip() -> None:
    email = "person@amzur.com"
    token = create_access_token(email=email)

    decoded = decode_access_token(token)
    assert decoded == email


def test_access_token_tampering_is_rejected() -> None:
    token = create_access_token(email="person@amzur.com")
    tampered = token + "x"

    with pytest.raises(ValueError):
        decode_access_token(tampered)
