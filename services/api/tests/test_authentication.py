from datetime import UTC, datetime

from fastapi.testclient import TestClient

from formwise_api.authentication.models import AuthenticatedIdentity, CurrentUserResponse
from formwise_api.dependencies.authentication import (
    get_authenticated_identity,
    get_user_repository,
)
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


def test_me_requires_a_valid_identity() -> None:
    response = TestClient(app).get("/api/v1/me")
    assert response.status_code == 401


def test_me_returns_the_backend_verified_user() -> None:
    identity = AuthenticatedIdentity(
        uid="firebase-uid",
        display_name="FormWise User",
        email="user@example.com",
        photo_url=None,
    )
    app.dependency_overrides[get_authenticated_identity] = lambda: identity
    app.dependency_overrides[get_user_repository] = FakeUserRepository
    try:
        response = TestClient(app).get("/api/v1/me")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["uid"] == "firebase-uid"
    assert response.json()["email"] == "user@example.com"
    assert "displayName" in response.json()
    assert "createdAt" in response.json()
