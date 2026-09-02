from formwise_api.retention.repository import FirestoreRetainedConversationSelector


class _Snapshot:
    def __init__(self, identifier: str, data: dict[str, str]) -> None:
        self.id = identifier
        self._data = data

    def to_dict(self) -> dict[str, str]:
        return self._data


class _Query:
    def __init__(self, snapshots: list[_Snapshot]) -> None:
        self._snapshots = snapshots

    def where(self, *_: object) -> "_Query":
        return self

    def order_by(self, *_: object, **__: object) -> "_Query":
        return self

    def limit(self, _: int) -> "_Query":
        return self

    def stream(self):
        return iter(self._snapshots)


class _Client:
    def __init__(self, snapshots: list[_Snapshot]) -> None:
        self._query = _Query(snapshots)

    def collection(self, _: str) -> _Query:
        return self._query


def test_oldest_retained_conversation_selection_uses_persisted_order() -> None:
    selector = FirestoreRetainedConversationSelector(
        _Client([_Snapshot("first", {"id": "conversation-old"})])
    )

    assert selector.oldest_retained_conversation_id("user-1") == "conversation-old"
