from formwise_api.understanding.field_map import LayoutFieldMapBuilder
from formwise_api.understanding.models import FieldRenderMetadata, StructuredField


def test_field_map_without_layout_preserves_immutable_field_semantics() -> None:
    field = StructuredField(
        id="full_name",
        label="Full name",
        confidence=0.99,
        required=False,
        render_metadata=FieldRenderMetadata(
            privacy_tier="safe",
            privacy_reason="No restricted data detected",
            field_type="text",
        ),
    )

    result = LayoutFieldMapBuilder().attach([field], None)

    assert result == [field]
