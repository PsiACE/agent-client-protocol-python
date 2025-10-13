from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from ..connection import Connection, MethodHandler
from ..interfaces import Agent, Client
from ..meta import AGENT_METHODS
from ..schema import (
    AuthenticateRequest,
    AuthenticateResponse,
    CancelNotification,
    InitializeRequest,
    InitializeResponse,
    LoadSessionRequest,
    LoadSessionResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    SetSessionModelRequest,
    SetSessionModelResponse,
    SetSessionModeRequest,
    SetSessionModeResponse,
)
from ..utils import (
    notify_model,
    request_model,
    request_model_from_dict,
)
from .router import build_client_router

__all__ = ["ClientSideConnection"]

_CLIENT_CONNECTION_ERROR = "ClientSideConnection requires asyncio StreamWriter/StreamReader"


class ClientSideConnection:
    """Client-side connection wrapper that dispatches JSON-RPC messages to an Agent implementation."""

    def __init__(
        self,
        to_client: Callable[[Agent], Client],
        input_stream: Any,
        output_stream: Any,
        **connection_kwargs: Any,
    ) -> None:
        if not isinstance(input_stream, asyncio.StreamWriter) or not isinstance(output_stream, asyncio.StreamReader):
            raise TypeError(_CLIENT_CONNECTION_ERROR)

        client = to_client(self)  # type: ignore[arg-type]
        handler = self._create_handler(client)
        self._conn = Connection(handler, input_stream, output_stream, **connection_kwargs)

    def _create_handler(self, client: Client) -> MethodHandler:
        router = build_client_router(client)

        async def handler(method: str, params: Any | None, is_notification: bool) -> Any:
            if is_notification:
                await router.dispatch_notification(method, params)
                return None
            return await router.dispatch_request(method, params)

        return handler

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        return await request_model(
            self._conn,
            AGENT_METHODS["initialize"],
            params,
            InitializeResponse,
        )

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:
        return await request_model(
            self._conn,
            AGENT_METHODS["session_new"],
            params,
            NewSessionResponse,
        )

    async def loadSession(self, params: LoadSessionRequest) -> LoadSessionResponse:
        return await request_model_from_dict(
            self._conn,
            AGENT_METHODS["session_load"],
            params,
            LoadSessionResponse,
        )

    async def setSessionMode(self, params: SetSessionModeRequest) -> SetSessionModeResponse:
        return await request_model_from_dict(
            self._conn,
            AGENT_METHODS["session_set_mode"],
            params,
            SetSessionModeResponse,
        )

    async def setSessionModel(self, params: SetSessionModelRequest) -> SetSessionModelResponse:
        return await request_model_from_dict(
            self._conn,
            AGENT_METHODS["session_set_model"],
            params,
            SetSessionModelResponse,
        )

    async def authenticate(self, params: AuthenticateRequest) -> AuthenticateResponse:
        return await request_model_from_dict(
            self._conn,
            AGENT_METHODS["authenticate"],
            params,
            AuthenticateResponse,
        )

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        return await request_model(
            self._conn,
            AGENT_METHODS["session_prompt"],
            params,
            PromptResponse,
        )

    async def cancel(self, params: CancelNotification) -> None:
        await notify_model(self._conn, AGENT_METHODS["session_cancel"], params)

    async def extMethod(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return await self._conn.send_request(f"_{method}", params)

    async def extNotification(self, method: str, params: dict[str, Any]) -> None:
        await self._conn.send_notification(f"_{method}", params)

    async def close(self) -> None:
        await self._conn.close()

    async def __aenter__(self) -> ClientSideConnection:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
