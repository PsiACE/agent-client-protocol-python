from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, cast, final

from ..connection import Connection
from ..interfaces import Agent, Client
from ..meta import CLIENT_METHODS
from ..schema import (
    AgentMessageChunk,
    AgentPlanUpdate,
    AgentThoughtChunk,
    AvailableCommandsUpdate,
    CreateTerminalRequest,
    CreateTerminalResponse,
    CurrentModeUpdate,
    EnvVariable,
    KillTerminalCommandRequest,
    KillTerminalCommandResponse,
    PermissionOption,
    ReadTextFileRequest,
    ReadTextFileResponse,
    ReleaseTerminalRequest,
    ReleaseTerminalResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SessionInfoUpdate,
    SessionNotification,
    TerminalOutputRequest,
    TerminalOutputResponse,
    ToolCallProgress,
    ToolCallStart,
    ToolCallUpdate,
    UserMessageChunk,
    WaitForTerminalExitRequest,
    WaitForTerminalExitResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
)
from ..terminal import TerminalHandle
from ..utils import compatible_class, notify_model, param_model, request_model, request_optional_model
from .router import build_agent_router

__all__ = ["AgentSideConnection"]
_AGENT_CONNECTION_ERROR = "AgentSideConnection requires asyncio StreamWriter/StreamReader"


@final
@compatible_class
class AgentSideConnection:
    """Agent-side connection wrapper that dispatches JSON-RPC messages to a Client implementation."""

    def __init__(
        self,
        to_agent: Callable[[Client], Agent] | Agent,
        input_stream: Any,
        output_stream: Any,
        listening: bool = True,
        *,
        use_unstable_protocol: bool = False,
        **connection_kwargs: Any,
    ) -> None:
        agent = to_agent(cast(Client, self)) if callable(to_agent) else to_agent
        if not isinstance(input_stream, asyncio.StreamWriter) or not isinstance(output_stream, asyncio.StreamReader):
            raise TypeError(_AGENT_CONNECTION_ERROR)
        handler = build_agent_router(cast(Agent, agent), use_unstable_protocol=use_unstable_protocol)
        self._conn = Connection(handler, input_stream, output_stream, listening=listening, **connection_kwargs)
        if on_connect := getattr(agent, "on_connect", None):
            on_connect(self)

    async def listen(self) -> None:
        """Start listening for incoming messages."""
        await self._conn.main_loop()

    @param_model(SessionNotification)
    async def session_update(
        self,
        session_id: str,
        update: UserMessageChunk
        | AgentMessageChunk
        | AgentThoughtChunk
        | ToolCallStart
        | ToolCallProgress
        | AgentPlanUpdate
        | AvailableCommandsUpdate
        | CurrentModeUpdate
        | SessionInfoUpdate,
        **kwargs: Any,
    ) -> None:
        await notify_model(
            self._conn,
            CLIENT_METHODS["session_update"],
            SessionNotification(session_id=session_id, update=update, field_meta=kwargs or None),
        )

    @param_model(RequestPermissionRequest)
    async def request_permission(
        self, options: list[PermissionOption], session_id: str, tool_call: ToolCallUpdate, **kwargs: Any
    ) -> RequestPermissionResponse:
        return await request_model(
            self._conn,
            CLIENT_METHODS["session_request_permission"],
            RequestPermissionRequest(
                options=options, session_id=session_id, tool_call=tool_call, field_meta=kwargs or None
            ),
            RequestPermissionResponse,
        )

    @param_model(ReadTextFileRequest)
    async def read_text_file(
        self, path: str, session_id: str, limit: int | None = None, line: int | None = None, **kwargs: Any
    ) -> ReadTextFileResponse:
        return await request_model(
            self._conn,
            CLIENT_METHODS["fs_read_text_file"],
            ReadTextFileRequest(path=path, session_id=session_id, limit=limit, line=line, field_meta=kwargs or None),
            ReadTextFileResponse,
        )

    @param_model(WriteTextFileRequest)
    async def write_text_file(
        self, content: str, path: str, session_id: str, **kwargs: Any
    ) -> WriteTextFileResponse | None:
        return await request_optional_model(
            self._conn,
            CLIENT_METHODS["fs_write_text_file"],
            WriteTextFileRequest(content=content, path=path, session_id=session_id, field_meta=kwargs or None),
            WriteTextFileResponse,
        )

    @param_model(CreateTerminalRequest)
    async def create_terminal(
        self,
        command: str,
        session_id: str,
        args: list[str] | None = None,
        cwd: str | None = None,
        env: list[EnvVariable] | None = None,
        output_byte_limit: int | None = None,
        **kwargs: Any,
    ) -> TerminalHandle:
        create_response = await request_model(
            self._conn,
            CLIENT_METHODS["terminal_create"],
            CreateTerminalRequest(
                command=command,
                session_id=session_id,
                args=args,
                cwd=cwd,
                env=env,
                output_byte_limit=output_byte_limit,
                field_meta=kwargs or None,
            ),
            CreateTerminalResponse,
        )
        return TerminalHandle(create_response.terminal_id, session_id, self._conn)

    @param_model(TerminalOutputRequest)
    async def terminal_output(self, session_id: str, terminal_id: str, **kwargs: Any) -> TerminalOutputResponse:
        return await request_model(
            self._conn,
            CLIENT_METHODS["terminal_output"],
            TerminalOutputRequest(session_id=session_id, terminal_id=terminal_id, field_meta=kwargs or None),
            TerminalOutputResponse,
        )

    @param_model(ReleaseTerminalRequest)
    async def release_terminal(
        self, session_id: str, terminal_id: str, **kwargs: Any
    ) -> ReleaseTerminalResponse | None:
        return await request_optional_model(
            self._conn,
            CLIENT_METHODS["terminal_release"],
            ReleaseTerminalRequest(session_id=session_id, terminal_id=terminal_id, field_meta=kwargs or None),
            ReleaseTerminalResponse,
        )

    @param_model(WaitForTerminalExitRequest)
    async def wait_for_terminal_exit(
        self, session_id: str, terminal_id: str, **kwargs: Any
    ) -> WaitForTerminalExitResponse:
        return await request_model(
            self._conn,
            CLIENT_METHODS["terminal_wait_for_exit"],
            WaitForTerminalExitRequest(session_id=session_id, terminal_id=terminal_id, field_meta=kwargs or None),
            WaitForTerminalExitResponse,
        )

    @param_model(KillTerminalCommandRequest)
    async def kill_terminal(
        self, session_id: str, terminal_id: str, **kwargs: Any
    ) -> KillTerminalCommandResponse | None:
        return await request_optional_model(
            self._conn,
            CLIENT_METHODS["terminal_kill"],
            KillTerminalCommandRequest(session_id=session_id, terminal_id=terminal_id, field_meta=kwargs or None),
            KillTerminalCommandResponse,
        )

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return await self._conn.send_request(f"_{method}", params)

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        await self._conn.send_notification(f"_{method}", params)

    async def close(self) -> None:
        await self._conn.close()

    async def __aenter__(self) -> AgentSideConnection:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
