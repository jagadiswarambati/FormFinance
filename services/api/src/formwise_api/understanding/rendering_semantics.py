from formwise_api.understanding.models import FieldRenderMetadata, StructuredField


class RenderingSemanticsClassifier:
    """Classifies render behavior during understanding, never during rendering."""

    def classify(self, field: StructuredField) -> FieldRenderMetadata:
        label = field.label.casefold()
        metadata = field.render_metadata
        if any(token in label for token in ("checkbox", "agree", "yes/no", "yes / no")):
            return metadata.model_copy(update={"field_type": "checkbox", "checkbox_mapping": {"checked": "checked", "unchecked": "unchecked"}, "overflow_policy": "manual_only"})
        if "date" in label:
            return metadata.model_copy(update={"field_type": "date", "overflow_policy": "shrink"})
        if "signature" in label:
            return metadata.model_copy(update={"field_type": "signature_placeholder", "overflow_policy": "manual_only"})
        if any(token in label for token in ("address", "remarks", "description")):
            return metadata.model_copy(update={"field_type": "text", "multiline": True, "overflow_policy": "wrap"})
        return metadata.model_copy(update={"field_type": "text", "overflow_policy": "shrink"})
