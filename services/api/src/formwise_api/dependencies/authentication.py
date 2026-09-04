from typing import Any

import structlog
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth

from formwise_api.authentication.firebase import (
    get_firebase_app,
    get_firestore_client,
)
from formwise_api.authentication.models import AuthenticatedIdentity
from formwise_api.authentication.repository import (
    FirestoreUserRepository,
    UserRepository,
)
from formwise_api.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)
logger = structlog.get_logger()


def get_user_repository(
    settings: Settings = Depends(get_settings),
) -> UserRepository:
    return FirestoreUserRepository(get_firestore_client(), settings)


def get_authenticated_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_demo_user_id: str | None = Header(default=None, alias="X-Demo-User-ID"),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedIdentity:

    if credentials is None or credentials.scheme.lower() != "bearer":
        # Demo-only bypass: only reachable when DEMO_AUTH_ENABLED=true (never
        # true in production, enforced by Settings.validate_security_configuration)
        # and only when no real bearer token was presented, so a configured
        # Firebase token always takes precedence over the demo header.
        if settings.demo_auth_enabled and x_demo_user_id:
            logger.info("authentication_demo_mode_used", uid=x_demo_user_id)
            return AuthenticatedIdentity(
                uid=x_demo_user_id,
                display_name="Demo User",
                email=f"{x_demo_user_id}@demo.formfinance.local",
                photo_url=None,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )

    try:
        decoded: dict[str, Any] = auth.verify_id_token(
            credentials.credentials,
            app=get_firebase_app(),
            check_revoked=True,
        )

    except Exception as exception:
        logger.info("authentication_token_rejected", error_type=type(exception).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exception

    uid = decoded.get("uid")
    email = decoded.get("email")

    if not isinstance(uid, str) or not isinstance(email, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    display_name = (
        decoded.get("name")
        if isinstance(decoded.get("name"), str)
        else None
    )

    photo_url = (
        decoded.get("picture")
        if isinstance(decoded.get("picture"), str)
        else None
    )

    return AuthenticatedIdentity(
        uid=uid,
        display_name=display_name,
        email=email,
        photo_url=photo_url,
    )
