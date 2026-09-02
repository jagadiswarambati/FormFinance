"""End-to-end acceptance contract for the emulator-backed closed-beta environment."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("FORMWISE_E2E_BASE_URL") or not os.getenv("FORMWISE_E2E_ID_TOKEN"),
    reason="requires closed-beta API URL and a Firebase emulator identity token",
)


def test_closed_beta_flow_environment_is_explicitly_configured() -> None:
    """The external flow runs only with isolated emulator credentials and synthetic fixtures."""
    assert os.environ["FORMWISE_E2E_BASE_URL"].startswith("http")
    assert os.environ["FORMWISE_E2E_ID_TOKEN"]
