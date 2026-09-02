from typing import Protocol

from formwise_api.understanding.models import (
    MissingField,
    StructuredCheckbox,
    StructuredField,
    StructuredSection,
    StructuredTable,
)


class DocumentClassifier(Protocol):
    def classify(self, text: str) -> tuple[str, float]: ...


class SectionDetector(Protocol):
    def detect(self, text: str) -> list[StructuredSection]: ...


class FieldExtractor(Protocol):
    def extract(self, text: str, sections: list[StructuredSection]) -> list[StructuredField]: ...


class FieldNormalizer(Protocol):
    def normalize(self, field: StructuredField) -> StructuredField: ...


class TableExtractor(Protocol):
    def extract(self, text: str, sections: list[StructuredSection]) -> list[StructuredTable]: ...


class CheckboxDetector(Protocol):
    def detect(self, text: str, sections: list[StructuredSection]) -> list[StructuredCheckbox]: ...


class SignatureDetector(Protocol):
    def detect(self, text: str) -> str: ...


class MissingFieldAnalyzer(Protocol):
    def analyze(self, fields: list[StructuredField]) -> list[MissingField]: ...
