from __future__ import annotations

from typing import Any

from ..exceptions import RequestError
from ..interfaces import Client
from ..meta import CLIENT_METHODS
from ..router import MessageRouter
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


def build_client_router(client: Client, use_unstable_protocol: bool = False) -> MessageRouter:
    router = MessageRouter(use_unstable_protocol=use_unstable_protocol)

    router.route_request(CLIENT_METHODS["fs_write_text_file"], WriteTextFileRequest, client, "write_text_file")
    router.route_request(CLIENT_METHODS["fs_read_text_file"], ReadTextFileRequest, client, "read_text_file")
    router.route_request(
        CLIENT_METHODS["session_request_permission"],
        RequestPermissionRequest,
        client,
        "request_permission",
    )
    router.route_request(
        CLIENT_METHODS["terminal_create"],
        CreateTerminalRequest,
        client,
        "create_terminal",
        optional=True,
        default_result=None,
    )
    router.route_request(
        CLIENT_METHODS["terminal_output"],
        TerminalOutputRequest,
        client,
        "terminal_output",
        optional=True,
        default_result=None,
    )
    router.route_request(
        CLIENT_METHODS["terminal_release"],
        ReleaseTerminalRequest,
        client,
        "release_terminal",
        optional=True,
        default_result={},
        adapt_result=normalize_result,
    )
    router.route_request(
        CLIENT_METHODS["terminal_wait_for_exit"],
        WaitForTerminalExitRequest,
        client,
        "wait_for_terminal_exit",
        optional=True,
        default_result=None,
    )
    router.route_request(
        CLIENT_METHODS["terminal_kill"],
        KillTerminalCommandRequest,
        client,
        "kill_terminal",
        optional=True,
        default_result={},
        adapt_result=normalize_result,
    )

    router.route_notification(CLIENT_METHODS["session_update"], SessionNotification, client, "session_update")

    @router.handle_extension_request
    async def _handle_extension_request(name: str, payload: dict[str, Any]) -> Any:
        ext = getattr(client, "ext_method", None)
        if ext is None:
            raise RequestError.method_not_found(f"_{name}")
        return await ext(name, payload)

    @router.handle_extension_notification
    async def _handle_extension_notification(name: str, payload: dict[str, Any]) -> None:
        ext = getattr(client, "ext_notification", None)
        if ext is None:
            return
        await ext(name, payload)

    return router
