from formwise_worker.rendering.interfaces import DocumentRenderer


class RendererFactory:
    def select(self, content_type: str, widget_fields: bool) -> DocumentRenderer:
        from formwise_worker.rendering.renderers import (
            FillablePDFRenderer,
            ImageRenderer,
            StaticPDFRenderer,
        )
        if content_type == "application/pdf": return FillablePDFRenderer() if widget_fields else StaticPDFRenderer()
        if content_type in {"image/png", "image/jpeg"}: return ImageRenderer()
        raise ValueError("DOCUMENT_UNSUPPORTED")
