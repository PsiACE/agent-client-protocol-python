from __future__ import annotations

from typing import Any, Protocol

from .schema import (
    AgentMessageChunk,
    AgentPlanUpdate,
    AgentThoughtChunk,
    AudioContentBlock,
    AuthenticateRequest,
    AuthenticateResponse,
    AvailableCommandsUpdate,
    CancelNotification,
    ClientCapabilities,
    CreateTerminalRequest,
    CreateTerminalResponse,
    CurrentModeUpdate,
    EmbeddedResourceContentBlock,
    EnvVariable,
    ForkSessionRequest,
    ForkSessionResponse,
    HttpMcpServer,
    ImageContentBlock,
    Implementation,
    InitializeRequest,
    InitializeResponse,
    KillTerminalCommandRequest,
    KillTerminalCommandResponse,
    ListSessionsRequest,
    ListSessionsResponse,
    LoadSessionRequest,
    LoadSessionResponse,
    McpServerStdio,
    NewSessionRequest,
    NewSessionResponse,
    PermissionOption,
    PromptRequest,
    PromptResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    ReleaseTerminalRequest,
    ReleaseTerminalResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    ResourceContentBlock,
    ResumeSessionRequest,
    ResumeSessionResponse,
    SessionInfoUpdate,
    SessionNotification,
    SetSessionModelRequest,
    SetSessionModelResponse,
    SetSessionModeRequest,
    SetSessionModeResponse,
    SseMcpServer,
    TerminalOutputRequest,
    TerminalOutputResponse,
    TextContentBlock,
    ToolCallProgress,
    ToolCallStart,
    ToolCallUpdate,
    UserMessageChunk,
    WaitForTerminalExitRequest,
    WaitForTerminalExitResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
)
from .terminal import TerminalHandle
from .utils import param_model

__all__ = ["Agent", "Client"]


class Client(Protocol):
    @param_model(RequestPermissionRequest)
    async def request_permission(
        self, options: list[PermissionOption], session_id: str, tool_call: ToolCallUpdate, **kwargs: Any
    ) -> RequestPermissionResponse: ...

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
    ) -> None: ...

    @param_model(WriteTextFileRequest)
    async def write_text_file(
        self, content: str, path: str, session_id: str, **kwargs: Any
    ) -> WriteTextFileResponse | None: ...

    @param_model(ReadTextFileRequest)
    async def read_text_file(
        self, path: str, session_id: str, limit: int | None = None, line: int | None = None, **kwargs: Any
    ) -> ReadTextFileResponse: ...

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
    ) -> CreateTerminalResponse | TerminalHandle: ...

    @param_model(TerminalOutputRequest)
    async def terminal_output(self, session_id: str, terminal_id: str, **kwargs: Any) -> TerminalOutputResponse: ...

    @param_model(ReleaseTerminalRequest)
    async def release_terminal(
        self, session_id: str, terminal_id: str, **kwargs: Any
    ) -> ReleaseTerminalResponse | None: ...

    @param_model(WaitForTerminalExitRequest)
    async def wait_for_terminal_exit(
        self, session_id: str, terminal_id: str, **kwargs: Any
    ) -> WaitForTerminalExitResponse: ...

    @param_model(KillTerminalCommandRequest)
    async def kill_terminal(
        self, session_id: str, terminal_id: str, **kwargs: Any
    ) -> KillTerminalCommandResponse | None: ...

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]: ...

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None: ...

    def on_connect(self, conn: Agent) -> None: ...


class Agent(Protocol):
    @param_model(InitializeRequest)
    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: ClientCapabilities | None = None,
        client_info: Implementation | None = None,
        **kwargs: Any,
    ) -> InitializeResponse: ...

    @param_model(NewSessionRequest)
    async def new_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio], **kwargs: Any
    ) -> NewSessionResponse: ...

    @param_model(LoadSessionRequest)
    async def load_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio], session_id: str, **kwargs: Any
    ) -> LoadSessionResponse | None: ...

    @param_model(ListSessionsRequest)
    async def list_sessions(
        self, cursor: str | None = None, cwd: str | None = None, **kwargs: Any
    ) -> ListSessionsResponse: ...

    @param_model(SetSessionModeRequest)
    async def set_session_mode(self, mode_id: str, session_id: str, **kwargs: Any) -> SetSessionModeResponse | None: ...

    @param_model(SetSessionModelRequest)
    async def set_session_model(
        self, model_id: str, session_id: str, **kwargs: Any
    ) -> SetSessionModelResponse | None: ...

    @param_model(AuthenticateRequest)
    async def authenticate(self, method_id: str, **kwargs: Any) -> AuthenticateResponse | None: ...

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
    ) -> PromptResponse: ...

    @param_model(ForkSessionRequest)
    async def fork_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio] | None = None,
        **kwargs: Any,
    ) -> ForkSessionResponse: ...

    @param_model(ResumeSessionRequest)
    async def resume_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio] | None = None,
        **kwargs: Any,
    ) -> ResumeSessionResponse: ...

    @param_model(CancelNotification)
    async def cancel(self, session_id: str, **kwargs: Any) -> None: ...

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]: ...

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None: ...

    def on_connect(self, conn: Client) -> None: ...
