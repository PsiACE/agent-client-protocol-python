from __future__ import annotations

from typing import Any

from ..exceptions import RequestError
from ..interfaces import Client
from ..meta import CLIENT_METHODS
from ..router import MessageRouter, RouterBuilder
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

__all__ = ["build_client_router"]


def build_client_router(client: Client) -> MessageRouter:
    builder = RouterBuilder()

    builder.request_attr(CLIENT_METHODS["fs_write_text_file"], WriteTextFileRequest, client, "writeTextFile")
    builder.request_attr(CLIENT_METHODS["fs_read_text_file"], ReadTextFileRequest, client, "readTextFile")
    builder.request_attr(
        CLIENT_METHODS["session_request_permission"],
        RequestPermissionRequest,
        client,
        "requestPermission",
    )
    builder.request_attr(
        CLIENT_METHODS["terminal_create"],
        CreateTerminalRequest,
        client,
        "createTerminal",
        optional=True,
        default_result=None,
    )
    builder.request_attr(
        CLIENT_METHODS["terminal_output"],
        TerminalOutputRequest,
        client,
        "terminalOutput",
        optional=True,
        default_result=None,
    )
    builder.request_attr(
        CLIENT_METHODS["terminal_release"],
        ReleaseTerminalRequest,
        client,
        "releaseTerminal",
        optional=True,
        default_result={},
        adapt_result=normalize_result,
    )
    builder.request_attr(
        CLIENT_METHODS["terminal_wait_for_exit"],
        WaitForTerminalExitRequest,
        client,
        "waitForTerminalExit",
        optional=True,
        default_result=None,
    )
    builder.request_attr(
        CLIENT_METHODS["terminal_kill"],
        KillTerminalCommandRequest,
        client,
        "killTerminal",
        optional=True,
        default_result={},
        adapt_result=normalize_result,
    )

    builder.notification_attr(CLIENT_METHODS["session_update"], SessionNotification, client, "sessionUpdate")

    async def handle_extension_request(name: str, payload: dict[str, Any]) -> Any:
        ext = getattr(client, "extMethod", None)
        if ext is None:
            raise RequestError.method_not_found(f"_{name}")
        return await ext(name, payload)

    async def handle_extension_notification(name: str, payload: dict[str, Any]) -> None:
        ext = getattr(client, "extNotification", None)
        if ext is None:
            return
        await ext(name, payload)

    return builder.build(
        request_extensions=handle_extension_request,
        notification_extensions=handle_extension_notification,
    )
