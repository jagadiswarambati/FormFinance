# Document Rendering Engine

Milestone 9 is a deterministic, asynchronous write-only pipeline. It consumes only the immutable original, Field Map v1, and approved safe assignments. Missing, invalid, manual-only, or below-threshold field-map metadata is a validation failure or manual-only outcome; the renderer never reconstructs it.

No export or download endpoint is included.
