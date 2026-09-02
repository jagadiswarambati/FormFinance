from typing import Literal

from formwise_api.understanding.models import StructuredField

PrivacyTier = Literal["safe", "restricted", "sensitive"]


class FieldPrivacyPolicy:
    """Frozen SDD field taxonomy; this policy makes assignment eligibility explicit."""

    _sensitive = ("aadhaar", "pan", "passport", "bank", "account", "ifsc", "card", "cvv", "pin", "otp", "password", "voter", "licence", "license")
    _restricted = ("date of birth", "dob", "gender", "health", "medical", "income", "caste", "religion", "signature")

    def classify(self, field: StructuredField) -> PrivacyTier:
        label = field.label.lower()
        if any(keyword in label for keyword in self._sensitive):
            return "sensitive"
        if any(keyword in label for keyword in self._restricted):
            return "restricted"
        return "safe"
