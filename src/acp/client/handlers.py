from __future__ import annotations

from typing import Any

from ..exceptions import RequestError
from ..interfaces import Client
from ..meta import CLIENT_METHODS
from ..schema import (
    CreateTerminalRequest,
    KillTerminalCommandRequest,
    ReadTextFileRequest,
    ReleaseTerminalRequest,
    RequestPermissionRequest,
    SessionNotification,
    TerminalOutputRequest,
    WaitForTerminalExitRequest,
    WriteTextFileRequest,
)
from ..utils import normalize_result

__all__ = ["NO_MATCH", "dispatch_client_method"]


class _NoMatch:
    """Sentinel returned by routing helpers when no handler matches."""


NO_MATCH = _NoMatch()


async def _handle_client_core(client: Client, method: str, params: Any | None) -> Any:
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
    return NO_MATCH


async def _handle_client_terminal(client: Client, method: str, params: Any | None) -> Any:  # noqa: C901
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
        return normalize_result(result)
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
        return normalize_result(result)
    return NO_MATCH


async def _handle_client_extensions(client: Client, method: str, params: Any | None, is_notification: bool) -> Any:
    if isinstance(method, str) and method.startswith("_"):
        ext_name = method[1:]
        if is_notification:
            if hasattr(client, "extNotification"):
                await client.extNotification(ext_name, params or {})  # type: ignore[arg-type]
                return None
            return None
        if hasattr(client, "extMethod"):
            return await client.extMethod(ext_name, params or {})  # type: ignore[arg-type]
        return NO_MATCH
    return NO_MATCH


async def dispatch_client_method(client: Client, method: str, params: Any | None, is_notification: bool) -> Any:
    """Dispatch client-bound methods mirroring upstream ACP routing."""
    for resolver in (_handle_client_core, _handle_client_terminal):
        result = await resolver(client, method, params)
        if result is not NO_MATCH:
            return result
    extension_result = await _handle_client_extensions(client, method, params, is_notification)
    if extension_result is not NO_MATCH:
        return extension_result
    raise RequestError.method_not_found(method)
