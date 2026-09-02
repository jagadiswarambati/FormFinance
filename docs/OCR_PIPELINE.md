# OCR Pipeline

Only documents with `status: uploaded` can begin OCR. `POST /api/v1/documents/{documentId}/ocr` requires the owner’s Firebase token, changes the document to `ocr_processing`, and creates a durable Firestore `ocr_jobs/{documentId}` record.

The worker uses the enabled `PaddleOCRProvider` with PP-StructureV3. Google Vision, Azure OCR, AWS Textract, and Tesseract exist only as disabled provider placeholders behind the same `OCRProvider` contract.

The immutable original remains in `storage/uploads/`. OCR output is written separately as `storage/ocr/{documentId}.txt`; Firestore keeps only its storage key and metadata.

| Endpoint                                  | Purpose                                                   |
| ----------------------------------------- | --------------------------------------------------------- |
| `POST /api/v1/documents/{documentId}/ocr` | Enqueue OCR for an uploaded document.                     |
| `GET /api/v1/documents/{documentId}/ocr`  | Return OCR status, provider, confidence, and text length. |

Run the local worker with `python -m formwise_worker.main`. Use `--once` to process a single queued job.
