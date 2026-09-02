from datetime import UTC, datetime

from formwise_api.authentication.models import AuthenticatedIdentity
from formwise_api.authentication.repository import FirestoreUserRepository
from formwise_api.config import Settings


class FakeSnapshot:
    def __init__(self, exists: bool, data: dict[str, object] | None = None) -> None:
        self.exists = exists
        self._data = data

    def to_dict(self) -> dict[str, object] | None:
        return self._data


class FakeReference:
    def __init__(self, snapshot: FakeSnapshot) -> None:
        self.snapshot = snapshot
        self.created: dict[str, object] | None = None
        self.updated: dict[str, object] | None = None

    def get(self) -> FakeSnapshot:
        return self.snapshot

    def create(self, record: dict[str, object]) -> None:
        self.created = record

    def update(self, record: dict[str, object]) -> None:
        self.updated = record


class FakeCollection:
    def __init__(self, reference: FakeReference) -> None:
        self.reference = reference

    def document(self, _: str) -> FakeReference:
        return self.reference


class FakeClient:
    def __init__(self, reference: FakeReference) -> None:
        self.reference = reference

    def collection(self, _: str) -> FakeCollection:
        return FakeCollection(self.reference)


def identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        uid="uid-1",
        display_name="User",
        email="user@example.com",
        photo_url=None,
    )


def test_first_login_creates_only_the_required_fields() -> None:
    reference = FakeReference(FakeSnapshot(False))
    repository = FirestoreUserRepository(FakeClient(reference), Settings())
    repository.upsert_on_login(identity())
    assert reference.created is not None
    assert set(reference.created) == {
        "uid",
        "displayName",
        "email",
        "photoURL",
        "createdAt",
        "lastLogin",
        "locale",
        "status",
        "termsVersion",
    }
    assert reference.updated is None


def test_returning_login_updates_only_last_login() -> None:
    now = datetime.now(UTC)
    record = {
        "displayName": "Existing User",
        "email": "user@example.com",
        "photoURL": None,
        "createdAt": now,
        "locale": "en",
        "status": "active",
    }
    reference = FakeReference(FakeSnapshot(True, record))
    repository = FirestoreUserRepository(FakeClient(reference), Settings())
    repository.upsert_on_login(identity())
    assert reference.created is None
    assert reference.updated is not None
    assert set(reference.updated) == {"lastLogin"}
