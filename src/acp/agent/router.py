from __future__ import annotations

from typing import Any

from ..exceptions import RequestError
from ..interfaces import Agent
from ..meta import AGENT_METHODS
from ..router import MessageRouter, RouterBuilder
from ..schema import (
    AuthenticateRequest,
    CancelNotification,
    InitializeRequest,
    LoadSessionRequest,
    NewSessionRequest,
    PromptRequest,
    SetSessionModelRequest,
    SetSessionModeRequest,
)
from ..utils import normalize_result

__all__ = ["build_agent_router"]


def build_agent_router(agent: Agent) -> MessageRouter:
    builder = RouterBuilder()

    builder.request_attr(AGENT_METHODS["initialize"], InitializeRequest, agent, "initialize")
    builder.request_attr(AGENT_METHODS["session_new"], NewSessionRequest, agent, "newSession")
    builder.request_attr(
        AGENT_METHODS["session_load"],
        LoadSessionRequest,
        agent,
        "loadSession",
        adapt_result=normalize_result,
    )
    builder.request_attr(
        AGENT_METHODS["session_set_mode"],
        SetSessionModeRequest,
        agent,
        "setSessionMode",
        adapt_result=normalize_result,
    )
    builder.request_attr(AGENT_METHODS["session_prompt"], PromptRequest, agent, "prompt")
    builder.request_attr(
        AGENT_METHODS["session_set_model"],
        SetSessionModelRequest,
        agent,
        "setSessionModel",
        adapt_result=normalize_result,
    )
    builder.request_attr(
        AGENT_METHODS["authenticate"],
        AuthenticateRequest,
        agent,
        "authenticate",
        adapt_result=normalize_result,
    )

    builder.notification_attr(AGENT_METHODS["session_cancel"], CancelNotification, agent, "cancel")

    async def handle_extension_request(name: str, payload: dict[str, Any]) -> Any:
        ext = getattr(agent, "extMethod", None)
        if ext is None:
            raise RequestError.method_not_found(f"_{name}")
        return await ext(name, payload)

    async def handle_extension_notification(name: str, payload: dict[str, Any]) -> None:
        ext = getattr(agent, "extNotification", None)
        if ext is None:
            return
        await ext(name, payload)

    return builder.build(
        request_extensions=handle_extension_request,
        notification_extensions=handle_extension_notification,
    )
