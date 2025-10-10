from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError

from .meta import AGENT_METHODS, CLIENT_METHODS, PROTOCOL_VERSION  # noqa: F401
from .schema import (
    AuthenticateRequest,
    AuthenticateResponse,
    CancelNotification,
    CreateTerminalRequest,
    CreateTerminalResponse,
    InitializeRequest,
    InitializeResponse,
    KillTerminalCommandRequest,
    KillTerminalCommandResponse,
    LoadSessionRequest,
    LoadSessionResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    ReleaseTerminalRequest,
    ReleaseTerminalResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SessionNotification,
    SetSessionModelRequest,
    SetSessionModelResponse,
    SetSessionModeRequest,
    SetSessionModeResponse,
    TerminalOutputRequest,
    TerminalOutputResponse,
    WaitForTerminalExitRequest,
    WaitForTerminalExitResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
)

JsonValue = Any
MethodHandler = Callable[[str, JsonValue | None, bool], Awaitable[JsonValue | None]]

_AGENT_CONNECTION_ERROR = "AgentSideConnection requires asyncio StreamWriter/StreamReader"
_CLIENT_CONNECTION_ERROR = "ClientSideConnection requires asyncio StreamWriter/StreamReader"


class RequestError(Exception):
    """JSON-RPC 2.0 error helper."""

    def __init__(self, code: int, message: str, data: Any | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.data = data

    @staticmethod
    def parse_error(data: dict | None = None) -> RequestError:
        return RequestError(-32700, "Parse error", data)

    @staticmethod
    def invalid_request(data: dict | None = None) -> RequestError:
        return RequestError(-32600, "Invalid request", data)

    @staticmethod
    def method_not_found(method: str) -> RequestError:
        return RequestError(-32601, "Method not found", {"method": method})

    @staticmethod
    def invalid_params(data: dict | None = None) -> RequestError:
        return RequestError(-32602, "Invalid params", data)

    @staticmethod
    def internal_error(data: dict | None = None) -> RequestError:
        return RequestError(-32603, "Internal error", data)

    @staticmethod
    def auth_required(data: dict | None = None) -> RequestError:
        return RequestError(-32000, "Authentication required", data)

    @staticmethod
    def resource_not_found(uri: str | None = None) -> RequestError:
        data = {"uri": uri} if uri is not None else None
        return RequestError(-32002, "Resource not found", data)

    def to_error_obj(self) -> dict[str, Any]:
        return {"code": self.code, "message": str(self), "data": self.data}


class _NoMatch:
    """Sentinel returned by routing helpers when no handler matches."""


_NO_MATCH = _NoMatch()


@dataclass(slots=True)
class _Pending:
    future: asyncio.Future[Any]


def _dump_params(params: BaseModel) -> dict[str, Any]:
    return params.model_dump(exclude_none=True, exclude_defaults=True)


def _optional_result(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, BaseModel):
        return _dump_params(payload)
    return payload


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


class Client(Protocol):
    async def requestPermission(self, params: RequestPermissionRequest) -> RequestPermissionResponse: ...

    async def sessionUpdate(self, params: SessionNotification) -> None: ...

    async def writeTextFile(self, params: WriteTextFileRequest) -> WriteTextFileResponse | None: ...

    async def readTextFile(self, params: ReadTextFileRequest) -> ReadTextFileResponse: ...

    async def createTerminal(self, params: CreateTerminalRequest) -> CreateTerminalResponse: ...

    async def terminalOutput(self, params: TerminalOutputRequest) -> TerminalOutputResponse: ...

    async def releaseTerminal(self, params: ReleaseTerminalRequest) -> ReleaseTerminalResponse | None: ...

    async def waitForTerminalExit(self, params: WaitForTerminalExitRequest) -> WaitForTerminalExitResponse: ...

    async def killTerminal(self, params: KillTerminalCommandRequest) -> KillTerminalCommandResponse | None: ...

    async def extMethod(self, method: str, params: dict[str, Any]) -> dict[str, Any]: ...

    async def extNotification(self, method: str, params: dict[str, Any]) -> None: ...


class Agent(Protocol):
    async def initialize(self, params: InitializeRequest) -> InitializeResponse: ...

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse: ...

    async def loadSession(self, params: LoadSessionRequest) -> LoadSessionResponse | None: ...

    async def setSessionMode(self, params: SetSessionModeRequest) -> SetSessionModeResponse | None: ...

    async def setSessionModel(self, params: SetSessionModelRequest) -> SetSessionModelResponse | None: ...

    async def authenticate(self, params: AuthenticateRequest) -> AuthenticateResponse | None: ...

    async def prompt(self, params: PromptRequest) -> PromptResponse: ...

    async def cancel(self, params: CancelNotification) -> None: ...

    async def extMethod(self, method: str, params: dict[str, Any]) -> dict[str, Any]: ...

    async def extNotification(self, method: str, params: dict[str, Any]) -> None: ...


class AgentSideConnection:
    """Agent-side connection wrapper that dispatches JSON-RPC messages to a Client implementation."""

    def __init__(
        self,
        to_agent: Callable[[AgentSideConnection], Agent],
        input_stream: Any,
        output_stream: Any,
    ) -> None:
        agent = to_agent(self)
        handler = _create_agent_handler(agent)

        if not isinstance(input_stream, asyncio.StreamWriter) or not isinstance(output_stream, asyncio.StreamReader):
            raise TypeError(_AGENT_CONNECTION_ERROR)
        self._conn = Connection(handler, input_stream, output_stream)

    async def sessionUpdate(self, params: SessionNotification) -> None:
        await self._conn.send_notification(
            CLIENT_METHODS["session_update"],
            _dump_params(params),
        )

    async def requestPermission(self, params: RequestPermissionRequest) -> RequestPermissionResponse:
        response = await self._conn.send_request(
            CLIENT_METHODS["session_request_permission"],
            _dump_params(params),
        )
        return RequestPermissionResponse.model_validate(response)

    async def readTextFile(self, params: ReadTextFileRequest) -> ReadTextFileResponse:
        response = await self._conn.send_request(
            CLIENT_METHODS["fs_read_text_file"],
            _dump_params(params),
        )
        return ReadTextFileResponse.model_validate(response)

    async def writeTextFile(self, params: WriteTextFileRequest) -> WriteTextFileResponse | None:
        response = await self._conn.send_request(
            CLIENT_METHODS["fs_write_text_file"],
            _dump_params(params),
        )
        return WriteTextFileResponse.model_validate(response) if isinstance(response, dict) else None

    async def createTerminal(self, params: CreateTerminalRequest) -> TerminalHandle:
        response = await self._conn.send_request(
            CLIENT_METHODS["terminal_create"],
            _dump_params(params),
        )
        create_response = CreateTerminalResponse.model_validate(response)
        return TerminalHandle(create_response.terminalId, params.sessionId, self._conn)

    async def terminalOutput(self, params: TerminalOutputRequest) -> TerminalOutputResponse:
        response = await self._conn.send_request(
            CLIENT_METHODS["terminal_output"],
            _dump_params(params),
        )
        return TerminalOutputResponse.model_validate(response)

    async def releaseTerminal(self, params: ReleaseTerminalRequest) -> ReleaseTerminalResponse | None:
        response = await self._conn.send_request(
            CLIENT_METHODS["terminal_release"],
            _dump_params(params),
        )
        return ReleaseTerminalResponse.model_validate(response) if isinstance(response, dict) else None

    async def waitForTerminalExit(self, params: WaitForTerminalExitRequest) -> WaitForTerminalExitResponse:
        response = await self._conn.send_request(
            CLIENT_METHODS["terminal_wait_for_exit"],
            _dump_params(params),
        )
        return WaitForTerminalExitResponse.model_validate(response)

    async def killTerminal(self, params: KillTerminalCommandRequest) -> KillTerminalCommandResponse | None:
        response = await self._conn.send_request(
            CLIENT_METHODS["terminal_kill"],
            _dump_params(params),
        )
        return KillTerminalCommandResponse.model_validate(response) if isinstance(response, dict) else None

    async def extMethod(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return await self._conn.send_request(f"_{method}", params)

    async def extNotification(self, method: str, params: dict[str, Any]) -> None:
        await self._conn.send_notification(f"_{method}", params)


class ClientSideConnection:
    """Client-side connection wrapper that dispatches JSON-RPC messages to an Agent implementation."""

    def __init__(
        self,
        to_client: Callable[[Agent], Client],
        input_stream: Any,
        output_stream: Any,
    ) -> None:
        if not isinstance(input_stream, asyncio.StreamWriter) or not isinstance(output_stream, asyncio.StreamReader):
            raise TypeError(_CLIENT_CONNECTION_ERROR)

        client = to_client(self)  # type: ignore[arg-type]
        handler = _create_client_handler(client)
        self._conn = Connection(handler, input_stream, output_stream)

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        response = await self._conn.send_request(
            AGENT_METHODS["initialize"],
            _dump_params(params),
        )
        return InitializeResponse.model_validate(response)

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:
        response = await self._conn.send_request(
            AGENT_METHODS["session_new"],
            _dump_params(params),
        )
        return NewSessionResponse.model_validate(response)

    async def loadSession(self, params: LoadSessionRequest) -> LoadSessionResponse:
        response = await self._conn.send_request(
            AGENT_METHODS["session_load"],
            _dump_params(params),
        )
        payload = response if isinstance(response, dict) else {}
        return LoadSessionResponse.model_validate(payload)

    async def setSessionMode(self, params: SetSessionModeRequest) -> SetSessionModeResponse:
        response = await self._conn.send_request(
            AGENT_METHODS["session_set_mode"],
            _dump_params(params),
        )
        payload = response if isinstance(response, dict) else {}
        return SetSessionModeResponse.model_validate(payload)

    async def setSessionModel(self, params: SetSessionModelRequest) -> SetSessionModelResponse:
        response = await self._conn.send_request(
            AGENT_METHODS["session_set_model"],
            _dump_params(params),
        )
        payload = response if isinstance(response, dict) else {}
        return SetSessionModelResponse.model_validate(payload)

    async def authenticate(self, params: AuthenticateRequest) -> AuthenticateResponse:
        response = await self._conn.send_request(
            AGENT_METHODS["authenticate"],
            _dump_params(params),
        )
        payload = response if isinstance(response, dict) else {}
        return AuthenticateResponse.model_validate(payload)

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        response = await self._conn.send_request(
            AGENT_METHODS["session_prompt"],
            _dump_params(params),
        )
        return PromptResponse.model_validate(response)

    async def cancel(self, params: CancelNotification) -> None:
        await self._conn.send_notification(
            AGENT_METHODS["session_cancel"],
            _dump_params(params),
        )

    async def extMethod(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return await self._conn.send_request(f"_{method}", params)

    async def extNotification(self, method: str, params: dict[str, Any]) -> None:
        await self._conn.send_notification(f"_{method}", params)


class TerminalHandle:
    def __init__(self, terminal_id: str, session_id: str, conn: Connection) -> None:
        self.id = terminal_id
        self._session_id = session_id
        self._conn = conn

    async def current_output(self) -> TerminalOutputResponse:
        response = await self._conn.send_request(
            CLIENT_METHODS["terminal_output"],
            {"sessionId": self._session_id, "terminalId": self.id},
        )
        return TerminalOutputResponse.model_validate(response)

    async def wait_for_exit(self) -> WaitForTerminalExitResponse:
        response = await self._conn.send_request(
            CLIENT_METHODS["terminal_wait_for_exit"],
            {"sessionId": self._session_id, "terminalId": self.id},
        )
        return WaitForTerminalExitResponse.model_validate(response)

    async def kill(self) -> KillTerminalCommandResponse:
        response = await self._conn.send_request(
            CLIENT_METHODS["terminal_kill"],
            {"sessionId": self._session_id, "terminalId": self.id},
        )
        payload = response if isinstance(response, dict) else {}
        return KillTerminalCommandResponse.model_validate(payload)

    async def release(self) -> ReleaseTerminalResponse:
        response = await self._conn.send_request(
            CLIENT_METHODS["terminal_release"],
            {"sessionId": self._session_id, "terminalId": self.id},
        )
        payload = response if isinstance(response, dict) else {}
        return ReleaseTerminalResponse.model_validate(payload)


async def _handle_agent_init_methods(agent: Agent, method: str, params: Any | None) -> Any:
    if method == AGENT_METHODS["initialize"]:
        request = InitializeRequest.model_validate(params)
        return await agent.initialize(request)
    if method == AGENT_METHODS["session_new"]:
        request = NewSessionRequest.model_validate(params)
        return await agent.newSession(request)
    return _NO_MATCH


async def _handle_agent_session_methods(agent: Agent, method: str, params: Any | None) -> Any:
    if method == AGENT_METHODS["session_load"]:
        if not hasattr(agent, "loadSession"):
            raise RequestError.method_not_found(method)
        request = LoadSessionRequest.model_validate(params)
        result = await agent.loadSession(request)
        return _optional_result(result)
    if method == AGENT_METHODS["session_set_mode"]:
        if not hasattr(agent, "setSessionMode"):
            raise RequestError.method_not_found(method)
        request = SetSessionModeRequest.model_validate(params)
        result = await agent.setSessionMode(request)
        return _optional_result(result)
    if method == AGENT_METHODS["session_prompt"]:
        request = PromptRequest.model_validate(params)
        return await agent.prompt(request)
    if method == AGENT_METHODS["session_set_model"]:
        if not hasattr(agent, "setSessionModel"):
            raise RequestError.method_not_found(method)
        request = SetSessionModelRequest.model_validate(params)
        result = await agent.setSessionModel(request)
        return _optional_result(result)
    if method == AGENT_METHODS["session_cancel"]:
        request = CancelNotification.model_validate(params)
        return await agent.cancel(request)
    return _NO_MATCH


async def _handle_agent_auth_methods(agent: Agent, method: str, params: Any | None) -> Any:
    if method == AGENT_METHODS["authenticate"]:
        if not hasattr(agent, "authenticate"):
            raise RequestError.method_not_found(method)
        request = AuthenticateRequest.model_validate(params)
        result = await agent.authenticate(request)
        return _optional_result(result)
    return _NO_MATCH


async def _handle_agent_extension_methods(agent: Agent, method: str, params: Any | None, is_notification: bool) -> Any:
    if isinstance(method, str) and method.startswith("_"):
        ext_name = method[1:]
        if is_notification:
            if hasattr(agent, "extNotification"):
                await agent.extNotification(ext_name, params or {})  # type: ignore[arg-type]
                return None
            return None
        if hasattr(agent, "extMethod"):
            return await agent.extMethod(ext_name, params or {})  # type: ignore[arg-type]
        return _NO_MATCH
    return _NO_MATCH


async def _handle_agent_method(agent: Agent, method: str, params: Any | None, is_notification: bool) -> Any:
    for resolver in (
        _handle_agent_init_methods,
        _handle_agent_session_methods,
        _handle_agent_auth_methods,
    ):
        result = await resolver(agent, method, params)
        if result is not _NO_MATCH:
            return result
    ext_result = await _handle_agent_extension_methods(agent, method, params, is_notification)
    if ext_result is not _NO_MATCH:
        return ext_result
    raise RequestError.method_not_found(method)


def _create_agent_handler(agent: Agent) -> MethodHandler:
    async def handler(method: str, params: Any | None, is_notification: bool) -> Any:
        return await _handle_agent_method(agent, method, params, is_notification)

    return handler


async def _handle_client_core_methods(client: Client, method: str, params: Any | None) -> Any:
    if method == CLIENT_METHODS["fs_write_text_file"]:
        request = WriteTextFileRequest.model_validate(params)
        return await client.writeTextFile(request)
    if method == CLIENT_METHODS["fs_read_text_file"]:
        request = ReadTextFileRequest.model_validate(params)
        return await client.readTextFile(request)
    if method == CLIENT_METHODS["session_request_permission"]:
        request = RequestPermissionRequest.model_validate(params)
        return await client.requestPermission(request)
    if method == CLIENT_METHODS["session_update"]:
        notification = SessionNotification.model_validate(params)
        await client.sessionUpdate(notification)
        return None
    return _NO_MATCH


async def _handle_client_terminal_methods(client: Client, method: str, params: Any | None) -> Any:  # noqa: C901
    if method == CLIENT_METHODS["terminal_create"]:
        if not hasattr(client, "createTerminal"):
            return None
        request = CreateTerminalRequest.model_validate(params)
        return await client.createTerminal(request)
    if method == CLIENT_METHODS["terminal_output"]:
        if not hasattr(client, "terminalOutput"):
            return None
        request = TerminalOutputRequest.model_validate(params)
        return await client.terminalOutput(request)
    if method == CLIENT_METHODS["terminal_release"]:
        if not hasattr(client, "releaseTerminal"):
            return {}
        request = ReleaseTerminalRequest.model_validate(params)
        result = await client.releaseTerminal(request)
        return _optional_result(result)
    if method == CLIENT_METHODS["terminal_wait_for_exit"]:
        if not hasattr(client, "waitForTerminalExit"):
            return None
        request = WaitForTerminalExitRequest.model_validate(params)
        return await client.waitForTerminalExit(request)
    if method == CLIENT_METHODS["terminal_kill"]:
        if not hasattr(client, "killTerminal"):
            return {}
        request = KillTerminalCommandRequest.model_validate(params)
        result = await client.killTerminal(request)
        return _optional_result(result)
    return _NO_MATCH


async def _handle_client_extension_methods(
    client: Client, method: str, params: Any | None, is_notification: bool
) -> Any:
    if isinstance(method, str) and method.startswith("_"):
        ext_name = method[1:]
        if is_notification:
            if hasattr(client, "extNotification"):
                await client.extNotification(ext_name, params or {})  # type: ignore[arg-type]
                return None
            return None
        if hasattr(client, "extMethod"):
            return await client.extMethod(ext_name, params or {})  # type: ignore[arg-type]
        return _NO_MATCH
    return _NO_MATCH


async def _handle_client_method(client: Client, method: str, params: Any | None, is_notification: bool) -> Any:
    for resolver in (
        _handle_client_core_methods,
        _handle_client_terminal_methods,
    ):
        result = await resolver(client, method, params)
        if result is not _NO_MATCH:
            return result
    ext_result = await _handle_client_extension_methods(client, method, params, is_notification)
    if ext_result is not _NO_MATCH:
        return ext_result
    raise RequestError.method_not_found(method)


def _create_client_handler(client: Client) -> MethodHandler:
    async def handler(method: str, params: Any | None, is_notification: bool) -> Any:
        return await _handle_client_method(client, method, params, is_notification)

    return handler
