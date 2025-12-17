from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, cast, final

from ..connection import Connection
from ..interfaces import Agent, Client
from ..meta import AGENT_METHODS
from ..schema import (
    AudioContentBlock,
    AuthenticateRequest,
    AuthenticateResponse,
    CancelNotification,
    ClientCapabilities,
    EmbeddedResourceContentBlock,
    ForkSessionRequest,
    ForkSessionResponse,
    HttpMcpServer,
    ImageContentBlock,
    Implementation,
    InitializeRequest,
    InitializeResponse,
    ListSessionsRequest,
    ListSessionsResponse,
    LoadSessionRequest,
    LoadSessionResponse,
    McpServerStdio,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    ResourceContentBlock,
    ResumeSessionRequest,
    ResumeSessionResponse,
    SetSessionModelRequest,
    SetSessionModelResponse,
    SetSessionModeRequest,
    SetSessionModeResponse,
    SseMcpServer,
    TextContentBlock,
)
from ..utils import compatible_class, notify_model, param_model, request_model, request_model_from_dict
from .router import build_client_router

__all__ = ["ClientSideConnection"]
_CLIENT_CONNECTION_ERROR = "ClientSideConnection requires asyncio StreamWriter/StreamReader"


@final
@compatible_class
class ClientSideConnection:
    """Client-side connection wrapper that dispatches JSON-RPC messages to an Agent implementation."""

    def __init__(
        self,
        to_client: Callable[[Agent], Client] | Client,
        input_stream: Any,
        output_stream: Any,
        *,
        use_unstable_protocol: bool = False,
        **connection_kwargs: Any,
    ) -> None:
        if not isinstance(input_stream, asyncio.StreamWriter) or not isinstance(output_stream, asyncio.StreamReader):
            raise TypeError(_CLIENT_CONNECTION_ERROR)
        client = to_client(cast(Agent, self)) if callable(to_client) else to_client
        handler = build_client_router(cast(Client, client), use_unstable_protocol=use_unstable_protocol)
        self._conn = Connection(handler, input_stream, output_stream, **connection_kwargs)
        if on_connect := getattr(client, "on_connect", None):
            on_connect(self)

    @param_model(InitializeRequest)
    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: ClientCapabilities | None = None,
        client_info: Implementation | None = None,
        **kwargs: Any,
    ) -> InitializeResponse:
        return await request_model(
            self._conn,
            AGENT_METHODS["initialize"],
            InitializeRequest(
                protocol_version=protocol_version,
                client_capabilities=client_capabilities or ClientCapabilities(),
                client_info=client_info,
                field_meta=kwargs or None,
            ),
            InitializeResponse,
        )

    @param_model(NewSessionRequest)
    async def new_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio], **kwargs: Any
    ) -> NewSessionResponse:
        return await request_model(
            self._conn,
            AGENT_METHODS["session_new"],
            NewSessionRequest(cwd=cwd, mcp_servers=mcp_servers, field_meta=kwargs or None),
            NewSessionResponse,
        )

    @param_model(LoadSessionRequest)
    async def load_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio], session_id: str, **kwargs: Any
    ) -> LoadSessionResponse:
        return await request_model_from_dict(
            self._conn,
            AGENT_METHODS["session_load"],
            LoadSessionRequest(cwd=cwd, mcp_servers=mcp_servers, session_id=session_id, field_meta=kwargs or None),
            LoadSessionResponse,
        )

    @param_model(ListSessionsRequest)
    async def list_sessions(
        self, cursor: str | None = None, cwd: str | None = None, **kwargs: Any
    ) -> ListSessionsResponse:
        return await request_model_from_dict(
            self._conn,
            AGENT_METHODS["session_list"],
            ListSessionsRequest(cursor=cursor, cwd=cwd, field_meta=kwargs or None),
            ListSessionsResponse,
        )

    @param_model(SetSessionModeRequest)
    async def set_session_mode(self, mode_id: str, session_id: str, **kwargs: Any) -> SetSessionModeResponse:
        return await request_model_from_dict(
            self._conn,
            AGENT_METHODS["session_set_mode"],
            SetSessionModeRequest(mode_id=mode_id, session_id=session_id, field_meta=kwargs or None),
            SetSessionModeResponse,
        )

    @param_model(SetSessionModelRequest)
    async def set_session_model(self, model_id: str, session_id: str, **kwargs: Any) -> SetSessionModelResponse:
        return await request_model_from_dict(
            self._conn,
            AGENT_METHODS["session_set_model"],
            SetSessionModelRequest(model_id=model_id, session_id=session_id, field_meta=kwargs or None),
            SetSessionModelResponse,
        )

    @param_model(AuthenticateRequest)
    async def authenticate(self, method_id: str, **kwargs: Any) -> AuthenticateResponse:
        return await request_model_from_dict(
            self._conn,
            AGENT_METHODS["authenticate"],
            AuthenticateRequest(method_id=method_id, field_meta=kwargs or None),
            AuthenticateResponse,
        )

    @param_model(PromptRequest)
    async def prompt(
        self,
        prompt: list[
            TextContentBlock
            | ImageContentBlock
            | AudioContentBlock
            | ResourceContentBlock
            | EmbeddedResourceContentBlock
        ],
        session_id: str,
        **kwargs: Any,
    ) -> PromptResponse:
        return await request_model(
            self._conn,
            AGENT_METHODS["session_prompt"],
            PromptRequest(prompt=prompt, session_id=session_id, field_meta=kwargs or None),
            PromptResponse,
        )

    @param_model(ForkSessionRequest)
    async def fork_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio] | None = None,
        **kwargs: Any,
    ) -> ForkSessionResponse:
        return await request_model(
            self._conn,
            AGENT_METHODS["session_fork"],
            ForkSessionRequest(session_id=session_id, cwd=cwd, mcp_servers=mcp_servers, field_meta=kwargs or None),
            ForkSessionResponse,
        )

    @param_model(ResumeSessionRequest)
    async def resume_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio] | None = None,
        **kwargs: Any,
    ) -> ResumeSessionResponse:
        return await request_model(
            self._conn,
            AGENT_METHODS["session_resume"],
            ResumeSessionRequest(session_id=session_id, cwd=cwd, mcp_servers=mcp_servers, field_meta=kwargs or None),
            ResumeSessionResponse,
        )

    @param_model(CancelNotification)
    async def cancel(self, session_id: str, **kwargs: Any) -> None:
        await notify_model(
            self._conn,
            AGENT_METHODS["session_cancel"],
            CancelNotification(session_id=session_id, field_meta=kwargs or None),
        )

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return await self._conn.send_request(f"_{method}", params)

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        await self._conn.send_notification(f"_{method}", params)

    async def close(self) -> None:
        await self._conn.close()

    async def __aenter__(self) -> ClientSideConnection:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
