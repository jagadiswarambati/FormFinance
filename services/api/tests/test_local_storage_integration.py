import asyncio
from pathlib import Path

from formwise_api.storage.local import LocalStorageAdapter


async def _content():
    yield b"synthetic-pdf"


def test_local_storage_adapter_writes_and_reads_an_uploaded_artifact(tmp_path: Path) -> None:
    adapter = LocalStorageAdapter(str(tmp_path / "uploads"), str(tmp_path / "quarantine"))
    result = asyncio.run(
        adapter.write_upload("synthetic.pdf", "application/pdf", _content(), 300)
    )

    assert result.file_size == len(b"synthetic-pdf")
    assert adapter.inspect("synthetic.pdf") == result
    assert adapter.release_quarantined("synthetic.pdf")
    assert (tmp_path / "uploads" / "synthetic.pdf").read_bytes() == b"synthetic-pdf"
