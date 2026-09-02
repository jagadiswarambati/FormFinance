from formwise_api.understanding.native_pdf import NativePdfWidgetMetadata


class NativeWidgetProjection:
    """Immutable metadata lookup exposed to the existing Field Map projection."""

    def __init__(self, widgets: list[NativePdfWidgetMetadata]) -> None:
        self._by_field_name = {widget.widget_id: widget for widget in widgets}

    def get(self, widget_id: str) -> NativePdfWidgetMetadata | None:
        return self._by_field_name.get(widget_id)

    def match(self, widget_id: str | None, field_label: str) -> NativePdfWidgetMetadata | None:
        return self.get(widget_id) if widget_id else self.get(field_label)
