import base64
import binascii
import hashlib
import hmac
import json
import time

from fastapi import HTTPException, status


class UploadSigner:
    def __init__(self, secret: str, ttl_seconds: int) -> None:
        self._secret = secret.encode()
        self._ttl_seconds = ttl_seconds

    def issue(self, document_id: str, owner_uid: str) -> tuple[str, int]:
        expires_at = int(time.time()) + self._ttl_seconds
        payload = json.dumps({"documentId": document_id, "ownerUid": owner_uid, "expiresAt": expires_at}, separators=(",", ":")).encode()
        encoded = base64.urlsafe_b64encode(payload).decode().rstrip("=")
        signature = hmac.new(self._secret, encoded.encode(), hashlib.sha256).hexdigest()
        return f"{encoded}.{signature}", expires_at

    def verify(self, token: str, document_id: str) -> str:
        try:
            encoded, signature = token.split(".", maxsplit=1)
            expected = hmac.new(self._secret, encoded.encode(), hashlib.sha256).hexdigest()
            payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
            valid = hmac.compare_digest(signature, expected) and payload["documentId"] == document_id and int(payload["expiresAt"]) >= int(time.time())
        except (KeyError, ValueError, TypeError, binascii.Error, json.JSONDecodeError, UnicodeDecodeError):
            valid = False
        if not valid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Upload target is invalid or expired.")
        return str(payload["ownerUid"])
