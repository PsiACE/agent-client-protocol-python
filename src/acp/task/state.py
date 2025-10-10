from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Protocol

__all__ = [
    "InMemoryMessageStateStore",
    "IncomingMessage",
    "MessageStateStore",
    "OutgoingMessage",
]


@dataclass(slots=True)
class OutgoingMessage:
    request_id: int
    method: str
    future: asyncio.Future[Any]


@dataclass(slots=True)
class IncomingMessage:
    method: str
    params: Any
    status: str = "pending"
    result: Any = None
    error: Any = None


class MessageStateStore(Protocol):
    def register_outgoing(self, request_id: int, method: str) -> asyncio.Future[Any]: ...

    def resolve_outgoing(self, request_id: int, result: Any) -> None: ...

    def reject_outgoing(self, request_id: int, error: Any) -> None: ...

    def reject_all_outgoing(self, error: Any) -> None: ...

    def begin_incoming(self, method: str, params: Any) -> IncomingMessage: ...

    def complete_incoming(self, record: IncomingMessage, result: Any) -> None: ...

    def fail_incoming(self, record: IncomingMessage, error: Any) -> None: ...


class InMemoryMessageStateStore(MessageStateStore):
    def __init__(self) -> None:
        self._outgoing: dict[int, OutgoingMessage] = {}
        self._incoming: list[IncomingMessage] = []

    def register_outgoing(self, request_id: int, method: str) -> asyncio.Future[Any]:
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._outgoing[request_id] = OutgoingMessage(request_id, method, future)
        return future

    def resolve_outgoing(self, request_id: int, result: Any) -> None:
        record = self._outgoing.pop(request_id, None)
        if record and not record.future.done():
            record.future.set_result(result)

    def reject_outgoing(self, request_id: int, error: Any) -> None:
        record = self._outgoing.pop(request_id, None)
        if record and not record.future.done():
            record.future.set_exception(error)

    def reject_all_outgoing(self, error: Any) -> None:
        for record in self._outgoing.values():
            if not record.future.done():
                record.future.set_exception(error)
        self._outgoing.clear()

    def begin_incoming(self, method: str, params: Any) -> IncomingMessage:
        record = IncomingMessage(method=method, params=params)
        self._incoming.append(record)
        return record

    def complete_incoming(self, record: IncomingMessage, result: Any) -> None:
        record.status = "completed"
        record.result = result

    def fail_incoming(self, record: IncomingMessage, error: Any) -> None:
        record.status = "failed"
        record.error = error
