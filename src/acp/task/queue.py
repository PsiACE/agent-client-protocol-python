from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Protocol

from . import RpcTask

__all__ = ["InMemoryMessageQueue", "MessageQueue"]


class MessageQueue(Protocol):
    async def publish(self, task: RpcTask) -> None: ...

    async def close(self) -> None: ...

    def task_done(self) -> None: ...

    async def join(self) -> None: ...

    def __aiter__(self) -> AsyncIterator[RpcTask]: ...


class InMemoryMessageQueue:
    """Simple in-memory broker for RPC task dispatch."""

    def __init__(self, *, maxsize: int = 0) -> None:
        self._queue: asyncio.Queue[RpcTask | None] = asyncio.Queue(maxsize=maxsize)
        self._closed = False

    async def publish(self, task: RpcTask) -> None:
        if self._closed:
            msg = "mssage queue already closed"
            raise RuntimeError(msg)
        await self._queue.put(task)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._queue.put(None)

    async def join(self) -> None:
        await self._queue.join()

    def task_done(self) -> None:
        with suppress(ValueError):
            self._queue.task_done()

    def __aiter__(self) -> AsyncIterator[RpcTask]:
        return _QueueIterator(self)


class _QueueIterator:
    def __init__(self, queue: InMemoryMessageQueue) -> None:
        self._queue = queue

    def __aiter__(self) -> _QueueIterator:
        return self

    async def __anext__(self) -> RpcTask:
        item = await self._queue._queue.get()
        if item is None:
            self._queue.task_done()
            raise StopAsyncIteration
        return item
