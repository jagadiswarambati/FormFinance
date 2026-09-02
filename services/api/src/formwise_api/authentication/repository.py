from datetime import UTC, datetime
from typing import Any, Protocol

from formwise_api.authentication.models import AuthenticatedIdentity, CurrentUserResponse
from formwise_api.config import Settings


class UserRepository(Protocol):
    def upsert_on_login(self, identity: AuthenticatedIdentity) -> CurrentUserResponse: ...


class FirestoreUserRepository:
    def __init__(self, client: Any, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    def upsert_on_login(self, identity: AuthenticatedIdentity) -> CurrentUserResponse:
        reference = self._client.collection("users").document(identity.uid)
        snapshot = reference.get()
        now = datetime.now(UTC)
        if snapshot.exists:
            reference.update({"lastLogin": now})
            data = snapshot.to_dict() or {}
            created_at = data.get("createdAt")
            if not isinstance(created_at, datetime):
                raise RuntimeError("Stored user record is missing a valid creation timestamp.")
            display_name = data.get("displayName")
            photo_url = data.get("photoURL")
            return CurrentUserResponse(
                uid=identity.uid,
                display_name=display_name if isinstance(display_name, str) else None,
                email=str(data["email"]),
                photo_url=photo_url if isinstance(photo_url, str) else None,
                locale=str(data["locale"]),
                status=str(data["status"]),
                created_at=created_at,
                last_login=now,
            )
        record = {
            "uid": identity.uid,
            "displayName": identity.display_name,
            "email": identity.email,
            "photoURL": identity.photo_url,
            "createdAt": now,
            "lastLogin": now,
            "locale": "en",
            "status": "active",
            "termsVersion": self._settings.terms_version,
        }
        reference.create(record)
        return CurrentUserResponse(uid=identity.uid, display_name=identity.display_name, email=identity.email, photo_url=identity.photo_url, locale="en", status="active", created_at=now, last_login=now)
