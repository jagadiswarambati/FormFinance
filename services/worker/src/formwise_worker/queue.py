from collections.abc import Awaitable, Callable
from typing import Protocol

JobHandler = Callable[[str], Awaitable[None]]
class JobQueue(Protocol):
    async def enqueue(self, job_type: str, payload: str) -> None: ...
    def register(self, job_type: str, handler: JobHandler) -> None: ...
