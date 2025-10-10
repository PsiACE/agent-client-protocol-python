from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from .exceptions import RequestError

JsonValue = Any
MethodHandler = Callable[[str, JsonValue | None, bool], Awaitable[JsonValue | None]]


__all__ = ["Connection", "JsonValue", "MethodHandler"]


@dataclass(slots=True)
class _Pending:
    future: asyncio.Future[Any]


class Connection:
    """Minimal JSON-RPC 2.0 connection over newline-delimited JSON frames."""

    def __init__(
        self,
        handler: MethodHandler,
        writer: asyncio.StreamWriter,
        reader: asyncio.StreamReader,
    ) -> None:
        self._handler = handler
        self._writer = writer
        self._reader = reader
        self._next_request_id = 0
        self._pending: dict[int, _Pending] = {}
        self._inflight: set[asyncio.Task[Any]] = set()
        self._write_lock = asyncio.Lock()
        self._recv_task = asyncio.create_task(self._receive_loop())

    async def close(self) -> None:
        """Stop the receive loop and cancel any in-flight handler tasks."""
        if not self._recv_task.done():
            self._recv_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._recv_task
        if self._inflight:
            tasks = list(self._inflight)
            for task in tasks:
                task.cancel()
            for task in tasks:
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    async def send_request(self, method: str, params: JsonValue | None = None) -> Any:
        request_id = self._next_request_id
        self._next_request_id += 1
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._pending[request_id] = _Pending(future)
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        await self._send_obj(payload)
        return await future

    async def send_notification(self, method: str, params: JsonValue | None = None) -> None:
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        await self._send_obj(payload)

    async def _receive_loop(self) -> None:
        try:
            while True:
                line = await self._reader.readline()
                if not line:
                    break
                try:
                    message: dict[str, Any] = json.loads(line)
                except Exception:
                    logging.exception("Error parsing JSON-RPC message")
                    continue
                await self._process_message(message)
        except asyncio.CancelledError:
            return

    async def _process_message(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        has_id = "id" in message
        if method is not None and has_id:
            self._schedule(self._handle_request(message))
            return
        if method is not None and not has_id:
            await self._handle_notification(message)
            return
        if has_id:
            await self._handle_response(message)

    def _schedule(self, coroutine: Awaitable[Any]) -> None:
        task = asyncio.create_task(coroutine)
        self._inflight.add(task)
        task.add_done_callback(self._task_done)

    def _task_done(self, task: asyncio.Task[Any]) -> None:
        self._inflight.discard(task)
        if task.cancelled():
            return
        with contextlib.suppress(Exception):
            task.result()

    async def _handle_request(self, message: dict[str, Any]) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": message["id"]}
        try:
            result = await self._handler(message["method"], message.get("params"), False)
            if isinstance(result, BaseModel):
                result = result.model_dump()
            payload["result"] = result if result is not None else None
        except RequestError as exc:
            payload["error"] = exc.to_error_obj()
        except ValidationError as exc:
            payload["error"] = RequestError.invalid_params({"errors": exc.errors()}).to_error_obj()
        except Exception as exc:
            try:
                data = json.loads(str(exc))
            except Exception:
                data = {"details": str(exc)}
            payload["error"] = RequestError.internal_error(data).to_error_obj()
        await self._send_obj(payload)

    async def _handle_notification(self, message: dict[str, Any]) -> None:
        with contextlib.suppress(Exception):
            await self._handler(message["method"], message.get("params"), True)

    async def _handle_response(self, message: dict[str, Any]) -> None:
        pending = self._pending.pop(message["id"], None)
        if pending is None:
            return
        if "result" in message:
            pending.future.set_result(message.get("result"))
            return
        if "error" in message:
            error_obj = message.get("error") or {}
            pending.future.set_exception(
                RequestError(
                    error_obj.get("code", -32603),
                    error_obj.get("message", "Error"),
                    error_obj.get("data"),
                )
            )
            return
        pending.future.set_result(None)

    async def _send_obj(self, payload: dict[str, Any]) -> None:
        data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        async with self._write_lock:
            self._writer.write(data)
            with contextlib.suppress(ConnectionError, RuntimeError):
                await self._writer.drain()
