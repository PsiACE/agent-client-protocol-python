from __future__ import annotations

from typing import Any, Protocol

from .schema import (
    AuthenticateRequest,
    AuthenticateResponse,
    CancelNotification,
    CreateTerminalRequest,
    CreateTerminalResponse,
    InitializeRequest,
    InitializeResponse,
    KillTerminalCommandRequest,
    KillTerminalCommandResponse,
    LoadSessionRequest,
    LoadSessionResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    ReleaseTerminalRequest,
    ReleaseTerminalResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SessionNotification,
    SetSessionModelRequest,
    SetSessionModelResponse,
    SetSessionModeRequest,
    SetSessionModeResponse,
    TerminalOutputRequest,
    TerminalOutputResponse,
    WaitForTerminalExitRequest,
    WaitForTerminalExitResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
)

__all__ = ["Agent", "Client"]


class Client(Protocol):
    async def requestPermission(self, params: RequestPermissionRequest) -> RequestPermissionResponse: ...

    async def sessionUpdate(self, params: SessionNotification) -> None: ...

    async def writeTextFile(self, params: WriteTextFileRequest) -> WriteTextFileResponse | None: ...

    async def readTextFile(self, params: ReadTextFileRequest) -> ReadTextFileResponse: ...

    async def createTerminal(self, params: CreateTerminalRequest) -> CreateTerminalResponse: ...

    async def terminalOutput(self, params: TerminalOutputRequest) -> TerminalOutputResponse: ...

    async def releaseTerminal(self, params: ReleaseTerminalRequest) -> ReleaseTerminalResponse | None: ...

    async def waitForTerminalExit(self, params: WaitForTerminalExitRequest) -> WaitForTerminalExitResponse: ...

    async def killTerminal(self, params: KillTerminalCommandRequest) -> KillTerminalCommandResponse | None: ...

    async def extMethod(self, method: str, params: dict[str, Any]) -> dict[str, Any]: ...

    async def extNotification(self, method: str, params: dict[str, Any]) -> None: ...


class Agent(Protocol):
    async def initialize(self, params: InitializeRequest) -> InitializeResponse: ...

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse: ...

    async def loadSession(self, params: LoadSessionRequest) -> LoadSessionResponse | None: ...

    async def setSessionMode(self, params: SetSessionModeRequest) -> SetSessionModeResponse | None: ...

    async def setSessionModel(self, params: SetSessionModelRequest) -> SetSessionModelResponse | None: ...

    async def authenticate(self, params: AuthenticateRequest) -> AuthenticateResponse | None: ...

    async def prompt(self, params: PromptRequest) -> PromptResponse: ...

    async def cancel(self, params: CancelNotification) -> None: ...

    async def extMethod(self, method: str, params: dict[str, Any]) -> dict[str, Any]: ...

    async def extNotification(self, method: str, params: dict[str, Any]) -> None: ...
