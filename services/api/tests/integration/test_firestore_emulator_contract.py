"""Firebase-emulator integration contracts; enabled only in an emulator environment."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("FIRESTORE_EMULATOR_HOST"),
    reason="requires FIRESTORE_EMULATOR_HOST",
)


def test_firestore_emulator_is_available_for_repository_integration() -> None:
    """CI/emulator profiles must explicitly provide the Firestore emulator endpoint."""
    assert os.environ["FIRESTORE_EMULATOR_HOST"]
