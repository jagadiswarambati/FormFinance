# Form Understanding Engine

Milestone 6 converts only the protected OCR artifact into the canonical `StructuredDocument`. No AI provider, raw OCR artifact, or original uploaded file is used by this pipeline.

## Corrective field-map projection

The frozen SDD requires a page-aware field map for a later renderer. OCR now preserves PP-StructureV3 layout tokens separately from text: page, bounding box, reading order, region/table metadata, optional widget identifier, and coordinate confidence. Privacy creates a separate sanitized layout artifact; Form Understanding consumes only that protected layout artifact and persists `renderMetadata` for every field.

`renderMetadata` contains `pageNumber`, `boundingBox`, `widgetId`, `coordinateConfidence`, `privacyTier`, and `privacyReason`. Missing or low-confidence coordinates remain unset/low-confidence. They are never inferred later by a renderer; future rendering must use manual-completion behavior for those fields.

The final field-map projection also persists `fieldType`, text alignment, multiline/overflow rules, table/cell metadata, checkbox mappings, and native-widget appearance metadata. These semantics are determined in Form Understanding and are immutable renderer input; rendering must not inspect or reconstruct source-document structure.

```text
Protected text → classifier → sections → fields → normalization → tables / checkboxes
              → signature + missing-field analysis → StructuredDocument → Firestore
```

## Components

- `DocumentClassifier`: rule-based document type classification.
- `SectionDetector`: finds heading-based semantic sections.
- `FieldExtractor` and `FieldNormalizer`: produce label/value relationships and normalized safe values.
- `TableExtractor`, `CheckboxDetector`, and `SignatureDetector`: retain document structures rather than flattening them.
- `MissingFieldAnalyzer`: reports required and potentially missing semantic fields.
- `StructuredDocumentBuilder`: assembles the canonical projection and confidence summary.

## Persistence and API

The owner-authorized result is stored at `structured_documents/{documentId}`. It contains document type, sections, fields, tables, checkboxes, signature status, missing fields, confidence summary, status, provider version, and creation time.

- `POST /api/v1/documents/{documentId}/understand` requires completed privacy processing and creates/replaces the deterministic projection.
- `GET /api/v1/documents/{documentId}/understanding` retrieves the projection for its owner.

The Structured Document Viewer is available from **My Forms** after privacy processing completes. It is inspection-only and has no AI, chat, recommendations, or summaries.
