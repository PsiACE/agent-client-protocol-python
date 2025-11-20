from __future__ import annotations

import asyncio
import contextlib
import copy
import inspect
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, ValidationError

from .exceptions import RequestError
from .task import (
    DefaultMessageDispatcher,
    InMemoryMessageQueue,
    InMemoryMessageStateStore,
    MessageDispatcher,
    MessageQueue,
    MessageSender,
    MessageStateStore,
    NotificationRunner,
    RequestRunner,
    RpcTask,
    RpcTaskKind,
    SenderFactory,
    TaskSupervisor,
)
from .telemetry import span_context

JsonValue = Any
MethodHandler = Callable[[str, JsonValue | None, bool], Awaitable[JsonValue | None]]


__all__ = ["Connection", "JsonValue", "MethodHandler", "StreamDirection", "StreamEvent"]


DispatcherFactory = Callable[
    [MessageQueue, TaskSupervisor, MessageStateStore, RequestRunner, NotificationRunner],
    MessageDispatcher,
]


class StreamDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


@dataclass(frozen=True, slots=True)
class StreamEvent:
    direction: StreamDirection
    message: dict[str, Any]


StreamObserver = Callable[[StreamEvent], Awaitable[None] | None]


class Connection:
    """Minimal JSON-RPC 2.0 connection over newline-delimited JSON frames."""

    def __init__(
        self,
        handler: MethodHandler,
        writer: asyncio.StreamWriter,
        reader: asyncio.StreamReader,
        *,
        queue: MessageQueue | None = None,
        state_store: MessageStateStore | None = None,
        dispatcher_factory: DispatcherFactory | None = None,
        sender_factory: SenderFactory | None = None,
        observers: list[StreamObserver] | None = None,
        listening: bool = True,
    ) -> None:
        self._handler = handler
        self._writer = writer
        self._reader = reader
        self._next_request_id = 0
        self._state = state_store or InMemoryMessageStateStore()
        self._tasks = TaskSupervisor(source="acp.Connection")
        self._tasks.add_error_handler(self._on_task_error)
        self._queue = queue or InMemoryMessageQueue()
        self._closed = False
        self._sender = (sender_factory or self._default_sender_factory)(self._writer, self._tasks)
        if listening:
            self._recv_task = self._tasks.create(
                self._receive_loop(),
                name="acp.Connection.receive",
                on_error=self._on_receive_error,
            )
        else:
            self._recv_task = None
        dispatcher_factory = dispatcher_factory or self._default_dispatcher_factory
        self._dispatcher = dispatcher_factory(
            self._queue,
            self._tasks,
            self._state,
            self._run_request,
            self._run_notification,
        )
        self._dispatcher.start()
        self._observers: list[StreamObserver] = list(observers or [])

    async def close(self) -> None:
        """Stop the receive loop and cancel any in-flight handler tasks."""
        if self._closed:
            return
        self._closed = True
        await self._dispatcher.stop()
        await self._sender.close()
        await self._tasks.shutdown()
        self._state.reject_all_outgoing(ConnectionError("Connection closed"))

    async def main_loop(self) -> None:
        try:
            await self._receive_loop()
        except Exception as exc:
            logging.exception("Connection main loop failed", exc_info=exc)
            self._on_receive_error(None, exc)  # type: ignore[arg-type]
            raise

    async def __aenter__(self) -> Connection:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    def add_observer(self, observer: StreamObserver) -> None:
        """Register a callback that receives every raw JSON-RPC message."""
        self._observers.append(observer)

    async def send_request(self, method: str, params: JsonValue | None = None) -> Any:
        request_id = self._next_request_id
        self._next_request_id += 1
        future = self._state.register_outgoing(request_id, method)
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        await self._sender.send(payload)
        self._notify_observers(StreamDirection.OUTGOING, payload)
        return await future

    async def send_notification(self, method: str, params: JsonValue | None = None) -> None:
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        await self._sender.send(payload)
        self._notify_observers(StreamDirection.OUTGOING, payload)

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
                self._notify_observers(StreamDirection.INCOMING, message)
                await self._process_message(message)
        except asyncio.CancelledError:
            return

    async def _process_message(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        has_id = "id" in message
        if method is not None and has_id:
            await self._queue.publish(RpcTask(RpcTaskKind.REQUEST, message))
            return
        if method is not None and not has_id:
            await self._queue.publish(RpcTask(RpcTaskKind.NOTIFICATION, message))
            return
        if has_id:
            await self._handle_response(message)

    def _notify_observers(self, direction: StreamDirection, message: dict[str, Any]) -> None:
        if not self._observers:
            return
        snapshot = copy.deepcopy(message)
        event = StreamEvent(direction, snapshot)
        for observer in list(self._observers):
            try:
                result = observer(event)
            except Exception:
                logging.exception("Stream observer failed", exc_info=True)
                continue
            if inspect.isawaitable(result):
                self._tasks.create(
                    result,
                    name=f"acp.Connection.observer.{direction.value}",
                    on_error=self._on_observer_error,
                )

    def _on_observer_error(self, task: asyncio.Task[Any], exc: BaseException) -> None:
        logging.exception("Stream observer coroutine failed", exc_info=exc)

    async def _run_request(self, message: dict[str, Any]) -> Any:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": message["id"]}
        method = message["method"]
        with span_context(
            "acp.request",
            attributes={"method": method},
        ):
            try:
                result = await self._handler(method, message.get("params"), False)
                if isinstance(result, BaseModel):
                    result = result.model_dump(
                        mode="json",
                        by_alias=True,
                        exclude_none=True,
                        exclude_unset=True,
                    )
                payload["result"] = result if result is not None else None
                await self._sender.send(payload)
                self._notify_observers(StreamDirection.OUTGOING, payload)
                return payload.get("result")
            except RequestError as exc:
                payload["error"] = exc.to_error_obj()
                await self._sender.send(payload)
                self._notify_observers(StreamDirection.OUTGOING, payload)
                raise
            except ValidationError as exc:
                err = RequestError.invalid_params({"errors": exc.errors()})
                payload["error"] = err.to_error_obj()
                await self._sender.send(payload)
                self._notify_observers(StreamDirection.OUTGOING, payload)
                raise err from None
            except Exception as exc:
                try:
                    data = json.loads(str(exc))
                except Exception:
                    data = {"details": str(exc)}
                err = RequestError.internal_error(data)
                payload["error"] = err.to_error_obj()
                await self._sender.send(payload)
                self._notify_observers(StreamDirection.OUTGOING, payload)
                raise err from None

    async def _run_notification(self, message: dict[str, Any]) -> None:
        method = message["method"]
        with span_context("acp.notification", attributes={"method": method}), contextlib.suppress(Exception):
            await self._handler(method, message.get("params"), True)

    async def _handle_response(self, message: dict[str, Any]) -> None:
        request_id = message["id"]
        result = message.get("result")
        if "result" in message:
            self._state.resolve_outgoing(request_id, result)
            return
        if "error" in message:
            error_obj = message.get("error") or {}
            self._state.reject_outgoing(
                request_id,
                RequestError(
                    error_obj.get("code", -32603),
                    error_obj.get("message", "Error"),
                    error_obj.get("data"),
                ),
            )
            return
        self._state.resolve_outgoing(request_id, None)

    def _on_receive_error(self, task: asyncio.Task[Any], exc: BaseException) -> None:
        logging.exception("Receive loop failed", exc_info=exc)
        self._state.reject_all_outgoing(exc)

    def _on_task_error(self, task: asyncio.Task[Any], exc: BaseException) -> None:
        logging.exception("Background task failed", exc_info=exc)

    def _default_dispatcher_factory(
        self,
        queue: MessageQueue,
        supervisor: TaskSupervisor,
        state: MessageStateStore,
        request_runner: RequestRunner,
        notification_runner: NotificationRunner,
    ) -> MessageDispatcher:
        return DefaultMessageDispatcher(
            queue=queue,
            supervisor=supervisor,
            store=state,
            request_runner=request_runner,
            notification_runner=notification_runner,
        )

    def _default_sender_factory(self, writer: asyncio.StreamWriter, supervisor: TaskSupervisor) -> MessageSender:
        return MessageSender(writer, supervisor)
