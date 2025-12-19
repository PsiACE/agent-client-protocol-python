import asyncio
import contextlib
from collections.abc import AsyncGenerator, Callable
from typing import Any

import pytest
import pytest_asyncio

from acp import (
    AuthenticateResponse,
    CreateTerminalResponse,
    InitializeResponse,
    KillTerminalCommandResponse,
    LoadSessionResponse,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    ReadTextFileResponse,
    ReleaseTerminalResponse,
    RequestError,
    RequestPermissionResponse,
    SessionNotification,
    SetSessionModeResponse,
    TerminalOutputResponse,
    WaitForTerminalExitResponse,
    WriteTextFileResponse,
)
from acp.core import AgentSideConnection, ClientSideConnection
from acp.schema import (
    AgentMessageChunk,
    AgentPlanUpdate,
    AgentThoughtChunk,
    AllowedOutcome,
    AudioContentBlock,
    AvailableCommandsUpdate,
    ClientCapabilities,
    CurrentModeUpdate,
    DeniedOutcome,
    EmbeddedResourceContentBlock,
    EnvVariable,
    HttpMcpServer,
    ImageContentBlock,
    Implementation,
    McpServerStdio,
    PermissionOption,
    ResourceContentBlock,
    SessionInfoUpdate,
    SseMcpServer,
    TextContentBlock,
    ToolCallProgress,
    ToolCallStart,
    ToolCallUpdate,
    UserMessageChunk,
)


class _Server:
    def __init__(self) -> None:
        self._server: asyncio.AbstractServer | None = None
        self._server_reader: asyncio.StreamReader | None = None
        self._server_writer: asyncio.StreamWriter | None = None
        self._client_reader: asyncio.StreamReader | None = None
        self._client_writer: asyncio.StreamWriter | None = None

    async def __aenter__(self):
        async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            self._server_reader = reader
            self._server_writer = writer

        self._server = await asyncio.start_server(handle, host="127.0.0.1", port=0)
        host, port = self._server.sockets[0].getsockname()[:2]
        self._client_reader, self._client_writer = await asyncio.open_connection(host, port)

        # wait until server side is set
        for _ in range(100):
            if self._server_reader and self._server_writer:
                break
            await asyncio.sleep(0.01)
        assert self._server_reader and self._server_writer
        assert self._client_reader and self._client_writer
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client_writer:
            self._client_writer.close()
            with contextlib.suppress(Exception):
                await self._client_writer.wait_closed()
        if self._server_writer:
            self._server_writer.close()
            with contextlib.suppress(Exception):
                await self._server_writer.wait_closed()
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    @property
    def server_writer(self) -> asyncio.StreamWriter:
        assert self._server_writer is not None
        return self._server_writer

    @property
    def server_reader(self) -> asyncio.StreamReader:
        assert self._server_reader is not None
        return self._server_reader

    @property
    def client_writer(self) -> asyncio.StreamWriter:
        assert self._client_writer is not None
        return self._client_writer

    @property
    def client_reader(self) -> asyncio.StreamReader:
        assert self._client_reader is not None
        return self._client_reader


@pytest_asyncio.fixture
async def server() -> AsyncGenerator[_Server, None]:
    """Provides a server-client connection pair for testing."""
    async with _Server() as server_instance:
        yield server_instance


class TestClient:
    __test__ = False  # prevent pytest from collecting this class

    def __init__(self) -> None:
        self.permission_outcomes: list[RequestPermissionResponse] = []
        self.files: dict[str, str] = {}
        self.notifications: list[SessionNotification] = []
        self.ext_calls: list[tuple[str, dict]] = []
        self.ext_notes: list[tuple[str, dict]] = []
        self._agent_conn = None

    def on_connect(self, conn) -> None:
        self._agent_conn = conn

    def queue_permission_cancelled(self) -> None:
        self.permission_outcomes.append(RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled")))

    def queue_permission_selected(self, option_id: str) -> None:
        self.permission_outcomes.append(
            RequestPermissionResponse(outcome=AllowedOutcome(option_id=option_id, outcome="selected"))
        )

    async def request_permission(
        self, options: list[PermissionOption], session_id: str, tool_call: ToolCallUpdate, **kwargs: Any
    ) -> RequestPermissionResponse:
        if self.permission_outcomes:
            return self.permission_outcomes.pop()
        return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))

    async def write_text_file(
        self, content: str, path: str, session_id: str, **kwargs: Any
    ) -> WriteTextFileResponse | None:
        self.files[str(path)] = content
        return WriteTextFileResponse()

    async def read_text_file(
        self, path: str, session_id: str, limit: int | None = None, line: int | None = None, **kwargs: Any
    ) -> ReadTextFileResponse:
        content = self.files.get(str(path), "default content")
        return ReadTextFileResponse(content=content)

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
    ) -> None:
        self.notifications.append(SessionNotification(session_id=session_id, update=update, field_meta=kwargs or None))

    # Optional terminal methods (not implemented in this test client)
    async def create_terminal(
        self,
        command: str,
        session_id: str,
        args: list[str] | None = None,
        cwd: str | None = None,
        env: list[EnvVariable] | None = None,
        output_byte_limit: int | None = None,
        **kwargs: Any,
    ) -> CreateTerminalResponse:
        raise NotImplementedError

    async def terminal_output(
        self, session_id: str, terminal_id: str | None = None, **kwargs: Any
    ) -> TerminalOutputResponse:  # pragma: no cover - placeholder
        raise NotImplementedError

    async def release_terminal(
        self, session_id: str, terminal_id: str | None = None, **kwargs: Any
    ) -> ReleaseTerminalResponse | None:
        raise NotImplementedError

    async def wait_for_terminal_exit(
        self, session_id: str, terminal_id: str | None = None, **kwargs: Any
    ) -> WaitForTerminalExitResponse:
        raise NotImplementedError

    async def kill_terminal(
        self, session_id: str, terminal_id: str | None = None, **kwargs: Any
    ) -> KillTerminalCommandResponse | None:
        raise NotImplementedError

    async def ext_method(self, method: str, params: dict) -> dict:
        self.ext_calls.append((method, params))
        if method == "example.com/ping":
            return {"response": "pong", "params": params}
        raise RequestError.method_not_found(method)

    async def ext_notification(self, method: str, params: dict) -> None:
        self.ext_notes.append((method, params))


class TestAgent:
    __test__ = False  # prevent pytest from collecting this class

    def __init__(self) -> None:
        self.prompts: list[PromptRequest] = []
        self.cancellations: list[str] = []
        self.ext_calls: list[tuple[str, dict]] = []
        self.ext_notes: list[tuple[str, dict]] = []

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: ClientCapabilities | None = None,
        client_info: Implementation | None = None,
        **kwargs: Any,
    ) -> InitializeResponse:
        # Avoid serializer warnings by omitting defaults
        return InitializeResponse(protocol_version=protocol_version, agent_capabilities=None, auth_methods=[])

    async def new_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio], **kwargs: Any
    ) -> NewSessionResponse:
        return NewSessionResponse(session_id="test-session-123")

    async def load_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio], session_id: str, **kwargs: Any
    ) -> LoadSessionResponse | None:
        return LoadSessionResponse()

    async def authenticate(self, method_id: str, **kwargs: Any) -> AuthenticateResponse | None:
        return AuthenticateResponse()

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
        self.prompts.append(PromptRequest(prompt=prompt, session_id=session_id, field_meta=kwargs or None))
        return PromptResponse(stop_reason="end_turn")

    async def cancel(self, session_id: str, **kwargs: Any) -> None:
        self.cancellations.append(session_id)

    async def set_session_mode(self, mode_id: str, session_id: str, **kwargs: Any) -> SetSessionModeResponse | None:
        return SetSessionModeResponse()

    async def ext_method(self, method: str, params: dict) -> dict:
        self.ext_calls.append((method, params))
        if method == "example.com/echo":
            return {"echo": params}
        raise RequestError.method_not_found(method)

    async def ext_notification(self, method: str, params: dict) -> None:
        self.ext_notes.append((method, params))


@pytest.fixture(name="agent")
def agent_fixture() -> TestAgent:
    return TestAgent()


@pytest.fixture(name="client")
def client_fixture() -> TestClient:
    return TestClient()


@pytest.fixture(name="connect")
def connect_func(server, agent, client) -> Callable[[bool, bool], tuple[AgentSideConnection, ClientSideConnection]]:
    def _connect(
        connect_agent: bool = True, connect_client: bool = True, use_unstable_protocol: bool = False
    ) -> tuple[AgentSideConnection, ClientSideConnection]:
        agent_conn = None
        client_conn = None
        if connect_agent:
            agent_conn = AgentSideConnection(
                agent,
                server.server_writer,
                server.server_reader,
                listening=True,
                use_unstable_protocol=use_unstable_protocol,
            )
        if connect_client:
            client_conn = ClientSideConnection(
                client, server.client_writer, server.client_reader, use_unstable_protocol=use_unstable_protocol
            )
        return agent_conn, client_conn  # type: ignore[return-value]

    return _connect
