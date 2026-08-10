from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from .config import get_settings

ANONYMOUS_CLIENT = "anonymous"
SCHEME = "Bearer"


def verify_bearer_token(
    authorization: str | None = Header(default=None),
    x_client_id: str | None = Header(default=None),
) -> str:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or missing bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization:
        raise credentials_error

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != SCHEME.lower() or not token:
        raise credentials_error

    if not secrets.compare_digest(token, get_settings().api_token):
        raise credentials_error

    return x_client_id or ANONYMOUS_CLIENT