# Upload API

The document upload flow uses an authenticated upload intent. The API never accepts a multipart form as its primary upload endpoint.

1. `POST /api/v1/documents/upload-intents` creates `documents/{documentId}` with status `upload_pending` and returns a short-lived, single-purpose `uploadUrl`.
2. The browser sends the original bytes with `PUT uploadUrl`. In local development, this is handled by the Local Storage Adapter; a future object-storage adapter returns its own direct upload URL without changing the browser workflow.
3. `POST /api/v1/documents/{documentId}/complete` requires the Firebase Bearer token, verifies the stored object, and marks the metadata `uploaded`.

All intent, completion, and list requests require `Authorization: Bearer <Firebase ID token>`. The single-purpose upload target is authenticated by its signed, expiring URL.

## Endpoints

| Method | Path                                      | Purpose                                            |
| ------ | ----------------------------------------- | -------------------------------------------------- |
| POST   | `/api/v1/documents/upload-intents`        | Validate metadata and create an upload intent.     |
| PUT    | `uploadUrl` returned by the intent        | Write bytes to the configured Storage Adapter.     |
| POST   | `/api/v1/documents/{documentId}/complete` | Verify storage and mark the document uploaded.     |
| GET    | `/api/v1/documents?limit=5`               | List the current user’s latest uploaded documents. |

Accepted types are PDF, PNG, JPG, and JPEG, with a maximum size of 10 MB. The server validates the extension, declared content type, streamed size, ownership, intent status, and signed upload URL.

## Development storage

Set `LOCAL_STORAGE_PATH=storage/uploads` and a long random `UPLOAD_SIGNING_SECRET`. The Local Storage Adapter writes `<documentId>_<sanitized-original-filename>` and prevents overwrites. `storage/uploads/` is Git-ignored.
