from formwise_api.understanding.models import DocumentType


class RuleBasedDocumentClassifier:
    _rules: tuple[tuple[DocumentType, tuple[str, ...]], ...] = (
        ("identity_document", ("passport", "aadhaar", "identity card", "voter id")),
        ("academic_record", ("semester", "marks", "grade", "transcript", "university")),
        ("medical_form", ("patient", "diagnosis", "medical", "hospital", "insurance")),
        ("financial_form", ("account number", "ifsc", "income", "bank", "financial")),
        ("certificate", ("certificate", "certify", "awarded")),
        ("government_form", ("government", "ministry", "department", "application no")),
        ("application_form", ("application", "applicant", "declaration")),
    )

    def classify(self, text: str) -> tuple[DocumentType, float]:
        lowered = text.lower()
        for document_type, keywords in self._rules:
            matches = sum(keyword in lowered for keyword in keywords)
            if matches:
                return document_type, min(0.95, 0.55 + matches * 0.15)
        return "unknown", 0.2
