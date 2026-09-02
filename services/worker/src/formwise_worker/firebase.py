import json
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

from formwise_worker.config import get_worker_settings, resolve_env_relative_path


def get_firestore_client() -> Any:
    try:
        app = firebase_admin.get_app()
    except ValueError:
        settings = get_worker_settings()
        options = {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
        credential: Any = None
        if settings.firebase_service_account_json:
            credential = credentials.Certificate(json.loads(settings.firebase_service_account_json))
        elif settings.firebase_service_account_path:
            path = resolve_env_relative_path(settings.firebase_service_account_path)
            if not path.exists():
                raise FileNotFoundError(f"Firebase service account file not found: {path}")
            credential = credentials.Certificate(str(path))
        else:
            raise RuntimeError("Firebase Admin credentials are required for the OCR worker.")
        app = firebase_admin.initialize_app(credential, options)
    return firestore.client(app)
