from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from ..connection import Connection, MethodHandler
from ..interfaces import Agent
from ..meta import CLIENT_METHODS
from ..schema import (
    CreateTerminalRequest,
    CreateTerminalResponse,
    KillTerminalCommandRequest,
    KillTerminalCommandResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    ReleaseTerminalRequest,
    ReleaseTerminalResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SessionNotification,
    TerminalOutputRequest,
    TerminalOutputResponse,
    WaitForTerminalExitRequest,
    WaitForTerminalExitResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
)
from ..terminal import TerminalHandle
from ..utils import notify_model, request_model, request_optional_model
from .router import build_agent_router

__all__ = ["AgentSideConnection"]

_AGENT_CONNECTION_ERROR = "AgentSideConnection requires asyncio StreamWriter/StreamReader"


class AgentSideConnection:
    """Agent-side connection wrapper that dispatches JSON-RPC messages to a Client implementation."""

    def __init__(
        self,
        to_agent: Callable[[AgentSideConnection], Agent],
        input_stream: Any,
        output_stream: Any,
        **connection_kwargs: Any,
    ) -> None:
        agent = to_agent(self)
        handler = self._create_handler(agent)

        if not isinstance(input_stream, asyncio.StreamWriter) or not isinstance(output_stream, asyncio.StreamReader):
            raise TypeError(_AGENT_CONNECTION_ERROR)
        self._conn = Connection(handler, input_stream, output_stream, **connection_kwargs)

    def _create_handler(self, agent: Agent) -> MethodHandler:
        router = build_agent_router(agent)

        async def handler(method: str, params: Any | None, is_notification: bool) -> Any:
            if is_notification:
                await router.dispatch_notification(method, params)
                return None
            return await router.dispatch_request(method, params)

        return handler

    async def sessionUpdate(self, params: SessionNotification) -> None:
        await notify_model(self._conn, CLIENT_METHODS["session_update"], params)

    async def requestPermission(self, params: RequestPermissionRequest) -> RequestPermissionResponse:
        return await request_model(
            self._conn,
            CLIENT_METHODS["session_request_permission"],
            params,
            RequestPermissionResponse,
        )

    async def readTextFile(self, params: ReadTextFileRequest) -> ReadTextFileResponse:
        return await request_model(
            self._conn,
            CLIENT_METHODS["fs_read_text_file"],
            params,
            ReadTextFileResponse,
        )

    async def writeTextFile(self, params: WriteTextFileRequest) -> WriteTextFileResponse | None:
        return await request_optional_model(
            self._conn,
            CLIENT_METHODS["fs_write_text_file"],
            params,
            WriteTextFileResponse,
        )

    async def createTerminal(self, params: CreateTerminalRequest) -> TerminalHandle:
        create_response = await request_model(
            self._conn,
            CLIENT_METHODS["terminal_create"],
            params,
            CreateTerminalResponse,
        )
        return TerminalHandle(create_response.terminalId, params.sessionId, self._conn)

    async def terminalOutput(self, params: TerminalOutputRequest) -> TerminalOutputResponse:
        return await request_model(
            self._conn,
            CLIENT_METHODS["terminal_output"],
            params,
            TerminalOutputResponse,
        )

    async def releaseTerminal(self, params: ReleaseTerminalRequest) -> ReleaseTerminalResponse | None:
        return await request_optional_model(
            self._conn,
            CLIENT_METHODS["terminal_release"],
            params,
            ReleaseTerminalResponse,
        )

    async def waitForTerminalExit(self, params: WaitForTerminalExitRequest) -> WaitForTerminalExitResponse:
        return await request_model(
            self._conn,
            CLIENT_METHODS["terminal_wait_for_exit"],
            params,
            WaitForTerminalExitResponse,
        )

    async def killTerminal(self, params: KillTerminalCommandRequest) -> KillTerminalCommandResponse | None:
        return await request_optional_model(
            self._conn,
            CLIENT_METHODS["terminal_kill"],
            params,
            KillTerminalCommandResponse,
        )

    async def extMethod(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return await self._conn.send_request(f"_{method}", params)

    async def extNotification(self, method: str, params: dict[str, Any]) -> None:
        await self._conn.send_notification(f"_{method}", params)

    async def close(self) -> None:
        await self._conn.close()

    async def __aenter__(self) -> AgentSideConnection:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
