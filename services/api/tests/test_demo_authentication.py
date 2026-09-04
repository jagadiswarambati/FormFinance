"""Tests for the DEMO_AUTH_ENABLED / X-Demo-User-ID authentication bypass.

These exercise `get_authenticated_identity` directly (not via dependency
override) so the actual header-parsing and settings-gating logic is proven,
not just the endpoints that depend on it.
"""

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from formwise_api.authentication.models import AuthenticatedIdentity, CurrentUserResponse
from formwise_api.config import Settings, get_settings
from formwise_api.dependencies.authentication import get_authenticated_identity, get_user_repository
from formwise_api.main import app


class FakeUserRepository:
    def upsert_on_login(self, identity: AuthenticatedIdentity) -> CurrentUserResponse:
        now = datetime.now(UTC)
        return CurrentUserResponse(
            uid=identity.uid,
            display_name=identity.display_name,
            email=identity.email,
            photo_url=identity.photo_url,
            locale="en",
            status="active",
            created_at=now,
            last_login=now,
        )


def test_demo_header_is_ignored_when_demo_auth_disabled() -> None:
    """DEMO_AUTH_ENABLED defaults to False: the header must not authenticate anyone."""
    with pytest.raises(HTTPException) as excinfo:
        get_authenticated_identity(
            credentials=None,
            x_demo_user_id="demo-user-1",
            settings=Settings(demo_auth_enabled=False),
        )
    assert excinfo.value.status_code == 401


def test_demo_header_authenticates_when_demo_auth_enabled() -> None:
    identity = get_authenticated_identity(
        credentials=None,
        x_demo_user_id="demo-user-1",
        settings=Settings(demo_auth_enabled=True),
    )
    assert identity.uid == "demo-user-1"
    assert identity.email == "demo-user-1@demo.formfinance.local"


def test_missing_demo_header_still_requires_auth_even_when_enabled() -> None:
    with pytest.raises(HTTPException) as excinfo:
        get_authenticated_identity(
            credentials=None,
            x_demo_user_id=None,
            settings=Settings(demo_auth_enabled=True),
        )
    assert excinfo.value.status_code == 401


def test_production_settings_reject_demo_auth_enabled() -> None:
    """The demo bypass must be structurally impossible to enable in production."""
    with pytest.raises(ValueError):
        Settings(
            formwise_env="production",
            demo_auth_enabled=True,
            security_hsts_max_age_seconds=3600,
            readiness_require_worker_heartbeat=True,
        )


def test_me_endpoint_accepts_demo_header_end_to_end() -> None:
    """Full HTTP round trip through /me using only the X-Demo-User-ID header."""
    app.dependency_overrides[get_settings] = lambda: Settings(demo_auth_enabled=True)
    app.dependency_overrides[get_user_repository] = lambda: FakeUserRepository()
    try:
        response = TestClient(app).get(
            "/api/v1/me",
            headers={"X-Demo-User-ID": "demo-user-42"},
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["uid"] == "demo-user-42"
