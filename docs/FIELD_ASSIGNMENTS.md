# Intelligent Field Assignment Engine

Milestone 8 creates deterministic, human-reviewed `field_assignments`. It does not render, modify, export, or otherwise alter a source document.

```text
StructuredDocument + safe conversation history + prior approved safe assignments
  → FieldPrivacyPolicy → source selection / validation / conflicts
  → confidence + clarification question → human review → approved assignment
```

## Privacy authority

The frozen `FieldPrivacyPolicy` classifies every structured field before any source is evaluated. Only `safe` fields can have a value, evidence, clarification question, validation result, edit, or approval.

`restricted` and `sensitive` fields always generate a value-free `manual_only` assignment with `reason="Protected by Privacy Policy"`. They are never requested, sent to an AI provider, edited, approved, or persisted with a value. Documents whose privacy status is `blocked` are rejected before the assignment workflow begins.

## API

- `POST /api/v1/documents/{documentId}/assignments/generate`
- `GET /api/v1/documents/{documentId}/assignments`
- `PATCH /api/v1/assignments/{assignmentId}` with `approve`, `reject`, or `edit`

All endpoints require Firebase authentication and owner authorization. The UI is at **My Forms → Structured document → Review field assignments**.

## Firestore schema

`field_assignments/{id}` contains document ID, field ID, label, safe suggested value when permitted, confidence, source, reason, evidence, review requirement, status, optional safe clarification question, privacy tier, and timestamps. This collection is the sole input for a future renderer; Milestone 8 does not create a renderer.
