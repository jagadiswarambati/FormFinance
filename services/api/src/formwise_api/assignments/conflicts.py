class ConflictDetector:
    def has_conflict(self, candidates: list[str]) -> bool:
        return len({candidate.strip().casefold() for candidate in candidates if candidate.strip()}) > 1
