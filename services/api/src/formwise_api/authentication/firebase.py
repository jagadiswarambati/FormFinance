import json
from functools import lru_cache
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

from formwise_api.config import get_settings, resolve_env_relative_path


@lru_cache
def get_firebase_app() -> firebase_admin.App:
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    settings = get_settings()

    options: dict[str, str] = {}

    if settings.firebase_project_id:
        options["projectId"] = settings.firebase_project_id

    credential: Any = None

    # Option 1: Load from JSON stored in environment variable
    if settings.firebase_service_account_json:
        credential = credentials.Certificate(
            json.loads(settings.firebase_service_account_json)
        )

    # Option 2: Load from local JSON file (recommended for development)
    elif settings.firebase_service_account_path:
        service_account_path = resolve_env_relative_path(settings.firebase_service_account_path)

        if not service_account_path.exists():
            raise FileNotFoundError(
                f"Firebase service account file not found: {service_account_path}"
            )

        credential = credentials.Certificate(str(service_account_path))

    else:
        raise RuntimeError(
            "No Firebase Admin credentials configured. "
            "Set FIREBASE_SERVICE_ACCOUNT_PATH or FIREBASE_SERVICE_ACCOUNT_JSON."
        )

    return firebase_admin.initialize_app(
        credential,
        options or None,
    )


def get_firestore_client() -> Any:
    return firestore.client(get_firebase_app())
