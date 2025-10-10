from __future__ import annotations

from typing import Any

from ..exceptions import RequestError
from ..interfaces import Agent
from ..meta import AGENT_METHODS
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

__all__ = [
    "NO_MATCH",
    "dispatch_agent_method",
]


class _NoMatch:
    """Sentinel returned by routing helpers when no handler matches."""


NO_MATCH = _NoMatch()


async def _handle_agent_init(agent: Agent, method: str, params: Any | None) -> Any:
    if method == AGENT_METHODS["initialize"]:
        request = InitializeRequest.model_validate(params)
        return await agent.initialize(request)
    if method == AGENT_METHODS["session_new"]:
        request = NewSessionRequest.model_validate(params)
        return await agent.newSession(request)
    return NO_MATCH


async def _handle_agent_session(agent: Agent, method: str, params: Any | None) -> Any:
    if method == AGENT_METHODS["session_load"]:
        if not hasattr(agent, "loadSession"):
            raise RequestError.method_not_found(method)
        request = LoadSessionRequest.model_validate(params)
        result = await agent.loadSession(request)
        return normalize_result(result)
    if method == AGENT_METHODS["session_set_mode"]:
        if not hasattr(agent, "setSessionMode"):
            raise RequestError.method_not_found(method)
        request = SetSessionModeRequest.model_validate(params)
        result = await agent.setSessionMode(request)
        return normalize_result(result)
    if method == AGENT_METHODS["session_prompt"]:
        request = PromptRequest.model_validate(params)
        return await agent.prompt(request)
    if method == AGENT_METHODS["session_set_model"]:
        if not hasattr(agent, "setSessionModel"):
            raise RequestError.method_not_found(method)
        request = SetSessionModelRequest.model_validate(params)
        result = await agent.setSessionModel(request)
        return normalize_result(result)
    if method == AGENT_METHODS["session_cancel"]:
        request = CancelNotification.model_validate(params)
        return await agent.cancel(request)
    return NO_MATCH


async def _handle_agent_auth(agent: Agent, method: str, params: Any | None) -> Any:
    if method == AGENT_METHODS["authenticate"]:
        if not hasattr(agent, "authenticate"):
            raise RequestError.method_not_found(method)
        request = AuthenticateRequest.model_validate(params)
        result = await agent.authenticate(request)
        return normalize_result(result)
    return NO_MATCH


async def _handle_agent_extensions(agent: Agent, method: str, params: Any | None, is_notification: bool) -> Any:
    if isinstance(method, str) and method.startswith("_"):
        ext_name = method[1:]
        if is_notification:
            if hasattr(agent, "extNotification"):
                await agent.extNotification(ext_name, params or {})  # type: ignore[arg-type]
                return None
            return None
        if hasattr(agent, "extMethod"):
            return await agent.extMethod(ext_name, params or {})  # type: ignore[arg-type]
        return NO_MATCH
    return NO_MATCH


async def dispatch_agent_method(agent: Agent, method: str, params: Any | None, is_notification: bool) -> Any:
    """Dispatch agent-bound methods, mirroring the upstream ACP routing."""
    for resolver in (_handle_agent_init, _handle_agent_session, _handle_agent_auth):
        result = await resolver(agent, method, params)
        if result is not NO_MATCH:
            return result
    extension_result = await _handle_agent_extensions(agent, method, params, is_notification)
    if extension_result is not NO_MATCH:
        return extension_result
    raise RequestError.method_not_found(method)
