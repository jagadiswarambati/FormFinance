from pathlib import Path

from formwise_api.understanding.builder import StructuredDocumentBuilder
from formwise_api.understanding.checkboxes import MarkupCheckboxDetector
from formwise_api.understanding.classification import RuleBasedDocumentClassifier
from formwise_api.understanding.field_map import LayoutFieldMapBuilder
from formwise_api.understanding.fields import RuleBasedFieldExtractor
from formwise_api.understanding.missing import RequiredFieldAnalyzer
from formwise_api.understanding.models import StructuredDocument
from formwise_api.understanding.native_pdf import NativeFillablePdfExtractor
from formwise_api.understanding.native_projection import NativeWidgetProjection
from formwise_api.understanding.normalization import StandardFieldNormalizer
from formwise_api.understanding.rendering_semantics import RenderingSemanticsClassifier
from formwise_api.understanding.sections import RuleBasedSectionDetector
from formwise_api.understanding.signatures import LabelBasedSignatureDetector
from formwise_api.understanding.tables import DelimitedTableExtractor


class UnderstandingPipeline:
    def __init__(self) -> None:
        self._classifier = RuleBasedDocumentClassifier()
        self._sections = RuleBasedSectionDetector()
        self._fields = RuleBasedFieldExtractor()
        self._normalizer = StandardFieldNormalizer()
        self._tables = DelimitedTableExtractor()
        self._checkboxes = MarkupCheckboxDetector()
        self._signature = LabelBasedSignatureDetector()
        self._missing = RequiredFieldAnalyzer()
        self._builder = StructuredDocumentBuilder()
        self._field_map = LayoutFieldMapBuilder()
        self._rendering_semantics = RenderingSemanticsClassifier()

    def understand(self, document_id: str, protected_text: str, provider_version: str, protected_layout_key: str | None = None, original_pdf_path: Path | None = None) -> StructuredDocument:
        document_type, classification_confidence = self._classifier.classify(protected_text)
        sections = self._sections.detect(protected_text)
        native = NativeWidgetProjection(NativeFillablePdfExtractor().extract(original_pdf_path)) if original_pdf_path else None
        fields = self._field_map.attach([self._normalizer.normalize(field) for field in self._fields.extract(protected_text, sections)], protected_layout_key, native)
        fields = [field.model_copy(update={"render_metadata": self._rendering_semantics.classify(field)}) for field in fields]
        return self._builder.build(document_id, document_type, classification_confidence, sections, fields, self._tables.extract(protected_text, sections), self._checkboxes.detect(protected_text, sections), self._signature.detect(protected_text), self._missing.analyze(fields), provider_version)
