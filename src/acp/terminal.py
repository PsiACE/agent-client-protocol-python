from __future__ import annotations

from contextlib import suppress

from .connection import Connection
from .meta import CLIENT_METHODS
from .schema import (
    KillTerminalCommandResponse,
    ReleaseTerminalResponse,
    TerminalOutputResponse,
    WaitForTerminalExitResponse,
)

__all__ = ["TerminalHandle"]


class TerminalHandle:
    def __init__(self, terminal_id: str, session_id: str, conn: Connection) -> None:
        self.id = terminal_id
        self._session_id = session_id
        self._conn = conn

    @property
    def terminal_id(self) -> str:
        return self.id

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

    async def aclose(self) -> None:
        """Release the terminal, ignoring errors that occur during shutdown."""
        with suppress(Exception):
            await self.release()

    async def close(self) -> None:
        await self.aclose()

    async def __aenter__(self) -> TerminalHandle:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()
