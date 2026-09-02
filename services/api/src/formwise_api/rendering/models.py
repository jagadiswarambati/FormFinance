"""Compatibility re-exports for shared provider-neutral rendering models."""

from formwise_document_core.rendering_models import (
    RenderRecord,
    RenderResult,
    RenderValidationReport,
)

__all__ = ["RenderRecord", "RenderResult", "RenderValidationReport"]
