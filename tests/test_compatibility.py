import pytest

from acp import (
    AuthenticateResponse,
    InitializeResponse,
    LoadSessionResponse,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    ReadTextFileResponse,
    RequestError,
    RequestPermissionResponse,
    SessionNotification,
    SetSessionModelResponse,
    SetSessionModeResponse,
    WriteTextFileResponse,
)
from acp.schema import (
    AllowedOutcome,
    AuthenticateRequest,
    CancelNotification,
    DeniedOutcome,
    InitializeRequest,
    LoadSessionRequest,
    NewSessionRequest,
    ReadTextFileRequest,
    RequestPermissionRequest,
    SetSessionModelRequest,
    SetSessionModeRequest,
    WriteTextFileRequest,
)


class LegacyAgent:
    def __init__(self) -> None:
        self.prompts: list[PromptRequest] = []
        self.cancellations: list[str] = []
        self.ext_calls: list[tuple[str, dict]] = []
        self.ext_notes: list[tuple[str, dict]] = []

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        # Avoid serializer warnings by omitting defaults
        return InitializeResponse(protocol_version=params.protocol_version, agent_capabilities=None, auth_methods=[])

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:
        return NewSessionResponse(session_id="test-session-123")

    async def loadSession(self, params: LoadSessionRequest) -> LoadSessionResponse | None:
        return LoadSessionResponse()

    async def authenticate(self, params: AuthenticateRequest) -> AuthenticateResponse | None:
        return AuthenticateResponse()

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        self.prompts.append(params)
        return PromptResponse(stop_reason="end_turn")

    async def cancel(self, params: CancelNotification) -> None:
        self.cancellations.append(params.session_id)

    async def setSessionMode(self, params: SetSessionModeRequest) -> SetSessionModeResponse | None:
        return SetSessionModeResponse()

    async def setSessionModel(self, params: SetSessionModelRequest) -> SetSessionModelResponse | None:
        return SetSessionModelResponse()

    async def extMethod(self, method: str, params: dict) -> dict:
        self.ext_calls.append((method, params))
        if method == "example.com/echo":
            return {"echo": params}
        raise RequestError.method_not_found(method)

    async def extNotification(self, method: str, params: dict) -> None:
        self.ext_notes.append((method, params))


class LegacyClient:
    __test__ = False  # prevent pytest from collecting this class

    def __init__(self) -> None:
        self.permission_outcomes: list[RequestPermissionResponse] = []
        self.files: dict[str, str] = {}
        self.notifications: list[SessionNotification] = []
        self.ext_calls: list[tuple[str, dict]] = []
        self.ext_notes: list[tuple[str, dict]] = []

    def queue_permission_cancelled(self) -> None:
        self.permission_outcomes.append(RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled")))

    def queue_permission_selected(self, option_id: str) -> None:
        self.permission_outcomes.append(
            RequestPermissionResponse(outcome=AllowedOutcome(option_id=option_id, outcome="selected"))
        )

    async def requestPermission(self, params: RequestPermissionRequest) -> RequestPermissionResponse:
        if self.permission_outcomes:
            return self.permission_outcomes.pop()
        return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))

    async def writeTextFile(self, params: WriteTextFileRequest) -> WriteTextFileResponse:
        self.files[str(params.path)] = params.content
        return WriteTextFileResponse()

    async def readTextFile(self, params: ReadTextFileRequest) -> ReadTextFileResponse:
        content = self.files.get(str(params.path), "default content")
        return ReadTextFileResponse(content=content)

    async def sessionUpdate(self, params: SessionNotification) -> None:
        self.notifications.append(params)

    # Optional terminal methods (not implemented in this test client)
    async def createTerminal(self, params):  # pragma: no cover - placeholder
        raise NotImplementedError

    async def terminalOutput(self, params):  # pragma: no cover - placeholder
        raise NotImplementedError

    async def releaseTerminal(self, params):  # pragma: no cover - placeholder
        raise NotImplementedError

    async def waitForTerminalExit(self, params):  # pragma: no cover - placeholder
        raise NotImplementedError

    async def killTerminal(self, params):  # pragma: no cover - placeholder
        raise NotImplementedError

    async def extMethod(self, method: str, params: dict) -> dict:
        self.ext_calls.append((method, params))
        if method == "example.com/ping":
            return {"response": "pong", "params": params}
        raise RequestError.method_not_found(method)

    async def extNotification(self, method: str, params: dict) -> None:
        self.ext_notes.append((method, params))


@pytest.mark.asyncio
@pytest.mark.parametrize("agent,client", [(LegacyAgent(), LegacyClient())])
async def test_initialize_and_new_session_compat(connect, client):
    client_conn, agent_conn = connect()

    with pytest.warns(DeprecationWarning) as record:
        resp = await agent_conn.newSession(NewSessionRequest(cwd="/home/tmp", mcp_servers=[]))

    assert len(record) == 2
    assert "Calling new_session with NewSessionRequest parameter is deprecated" in str(record[0].message)
    assert "The old style method LegacyAgent.newSession is deprecated" in str(record[1].message)

    assert isinstance(resp, NewSessionResponse)
    assert resp.session_id == "test-session-123"

    with pytest.warns(DeprecationWarning) as record:
        resp = await agent_conn.new_session(cwd="/home/tmp", mcp_servers=[])
    assert len(record) == 1
    assert "The old style method LegacyAgent.newSession is deprecated" in str(record[0].message)

    with pytest.warns(DeprecationWarning) as record:
        await client_conn.writeTextFile(
            WriteTextFileRequest(path="test.txt", content="Hello, World!", session_id="test-session-123")
        )

    assert len(record) == 2
    assert client.files["test.txt"] == "Hello, World!"

    with pytest.warns(DeprecationWarning) as record:
        resp = await client_conn.read_text_file(path="test.txt", session_id="test-session-123")

    assert len(record) == 1
    assert resp.content == "Hello, World!"
