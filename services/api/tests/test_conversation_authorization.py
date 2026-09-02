from fastapi.testclient import TestClient

from formwise_api.authentication.models import AuthenticatedIdentity
from formwise_api.conversations.router import get_conversation_service
from formwise_api.dependencies.authentication import get_authenticated_identity
from formwise_api.main import app


class _ConversationService:
    def get_for_owner(self, conversation_id: str, user_id: str):
        return None


def test_conversation_endpoint_does_not_disclose_another_users_conversation() -> None:
    app.dependency_overrides[get_authenticated_identity] = lambda: AuthenticatedIdentity(
        uid="user-a", display_name="User A", email="a@example.com", photo_url=None
    )
    app.dependency_overrides[get_conversation_service] = _ConversationService
    try:
        response = TestClient(app).get("/api/v1/conversations/user-b-conversation")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "The requested resource was not found."
