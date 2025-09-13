import asyncio
import contextlib
import json

import pytest

from acp import (
    Agent,
    AgentSideConnection,
    CancelNotification,
    Client,
    ClientSideConnection,
    InitializeRequest,
    InitializeResponse,
    LoadSessionRequest,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SessionNotification,
    SetSessionModeRequest,
    WriteTextFileRequest,
)
from acp.schema import ContentBlock1, SessionUpdate1, SessionUpdate2

# --------------------- Test Utilities ---------------------


class _Server:
    def __init__(self) -> None:
        self._server: asyncio.AbstractServer | None = None
        self.server_reader: asyncio.StreamReader | None = None
        self.server_writer: asyncio.StreamWriter | None = None
        self.client_reader: asyncio.StreamReader | None = None
        self.client_writer: asyncio.StreamWriter | None = None

    async def __aenter__(self):
        async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            self.server_reader = reader
            self.server_writer = writer

        self._server = await asyncio.start_server(handle, host="127.0.0.1", port=0)
        host, port = self._server.sockets[0].getsockname()[:2]
        self.client_reader, self.client_writer = await asyncio.open_connection(host, port)

        # wait until server side is set
        for _ in range(100):
            if self.server_reader and self.server_writer:
                break
            await asyncio.sleep(0.01)
        assert self.server_reader and self.server_writer
        assert self.client_reader and self.client_writer
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.client_writer:
            self.client_writer.close()
            with contextlib.suppress(Exception):
                await self.client_writer.wait_closed()
        if self.server_writer:
            self.server_writer.close()
            with contextlib.suppress(Exception):
                await self.server_writer.wait_closed()
        if self._server:
            self._server.close()
            await self._server.wait_closed()


# --------------------- Test Doubles -----------------------


class TestClient(Client):
    __test__ = False  # prevent pytest from collecting this class

    def __init__(self) -> None:
        self.permission_outcomes: list[dict] = []
        self.files: dict[str, str] = {}
        self.notifications: list[SessionNotification] = []
        self.ext_calls: list[tuple[str, dict]] = []
        self.ext_notes: list[tuple[str, dict]] = []

    async def requestPermission(self, params: RequestPermissionRequest) -> RequestPermissionResponse:
        outcome = self.permission_outcomes.pop() if self.permission_outcomes else {"outcome": "cancelled"}
        return RequestPermissionResponse.model_validate({"outcome": outcome})

    async def writeTextFile(self, params: WriteTextFileRequest) -> None:
        self.files[str(params.path)] = params.content

    async def readTextFile(self, params: ReadTextFileRequest) -> ReadTextFileResponse:
        content = self.files.get(str(params.path), "default content")
        return ReadTextFileResponse(content=content)

    async def sessionUpdate(self, params: SessionNotification) -> None:
        self.notifications.append(params)

    # Optional terminal methods (not implemented in this test client)
    async def createTerminal(self, params) -> None:  # pragma: no cover - placeholder
        pass

    async def terminalOutput(self, params) -> None:  # pragma: no cover - placeholder
        pass

    async def releaseTerminal(self, params) -> None:  # pragma: no cover - placeholder
        pass

    async def waitForTerminalExit(self, params) -> None:  # pragma: no cover - placeholder
        pass

    async def killTerminal(self, params) -> None:  # pragma: no cover - placeholder
        pass

    async def extMethod(self, method: str, params: dict) -> dict:
        self.ext_calls.append((method, params))
        return {"ok": True, "method": method}

    async def extNotification(self, method: str, params: dict) -> None:
        self.ext_notes.append((method, params))


class TestAgent(Agent):
    __test__ = False  # prevent pytest from collecting this class

    def __init__(self) -> None:
        self.prompts: list[PromptRequest] = []
        self.cancellations: list[str] = []
        self.ext_calls: list[tuple[str, dict]] = []
        self.ext_notes: list[tuple[str, dict]] = []

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        # Avoid serializer warnings by omitting defaults
        return InitializeResponse(protocolVersion=params.protocolVersion, agentCapabilities=None, authMethods=[])

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:
        return NewSessionResponse(sessionId="test-session-123")

    async def loadSession(self, params: LoadSessionRequest) -> None:
        return None

    async def authenticate(self, params) -> None:
        return None

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        self.prompts.append(params)
        return PromptResponse(stopReason="end_turn")

    async def cancel(self, params: CancelNotification) -> None:
        self.cancellations.append(params.sessionId)

    async def setSessionMode(self, params):
        return {}

    async def extMethod(self, method: str, params: dict) -> dict:
        self.ext_calls.append((method, params))
        return {"ok": True, "method": method}

    async def extNotification(self, method: str, params: dict) -> None:
        self.ext_notes.append((method, params))


# ------------------------ Tests --------------------------


@pytest.mark.asyncio
async def test_initialize_and_new_session():
    async with _Server() as s:
        agent = TestAgent()
        client = TestClient()
        # server side is agent; client side is client
        agent_conn = ClientSideConnection(lambda _conn: client, s.client_writer, s.client_reader)
        _client_conn = AgentSideConnection(lambda _conn: agent, s.server_writer, s.server_reader)

        resp = await agent_conn.initialize(InitializeRequest(protocolVersion=1))
        assert isinstance(resp, InitializeResponse)
        assert resp.protocolVersion == 1

        new_sess = await agent_conn.newSession(NewSessionRequest(mcpServers=[], cwd="/test"))
        assert new_sess.sessionId == "test-session-123"


@pytest.mark.asyncio
async def test_bidirectional_file_ops():
    async with _Server() as s:
        agent = TestAgent()
        client = TestClient()
        client.files["/test/file.txt"] = "Hello, World!"
        _agent_conn = ClientSideConnection(lambda _conn: client, s.client_writer, s.client_reader)
        client_conn = AgentSideConnection(lambda _conn: agent, s.server_writer, s.server_reader)

        # Agent asks client to read
        res = await client_conn.readTextFile(ReadTextFileRequest(sessionId="sess", path="/test/file.txt"))
        assert res.content == "Hello, World!"

        # Agent asks client to write
        await client_conn.writeTextFile(
            WriteTextFileRequest(sessionId="sess", path="/test/file.txt", content="Updated")
        )
        assert client.files["/test/file.txt"] == "Updated"


@pytest.mark.asyncio
async def test_cancel_notification_and_capture_wire():
    async with _Server() as s:
        # Build only agent-side (server) connection. Client side: raw reader to inspect wire
        agent = TestAgent()
        client = TestClient()
        agent_conn = ClientSideConnection(lambda _conn: client, s.client_writer, s.client_reader)
        _client_conn = AgentSideConnection(lambda _conn: agent, s.server_writer, s.server_reader)

        # Send cancel notification from client-side connection to agent
        await agent_conn.cancel(CancelNotification(sessionId="test-123"))

        # Read raw line from server peer (it will be consumed by agent receive loop quickly).
        # Instead, wait a brief moment and assert agent recorded it.
        for _ in range(50):
            if agent.cancellations:
                break
            await asyncio.sleep(0.01)
        assert agent.cancellations == ["test-123"]


@pytest.mark.asyncio
async def test_session_notifications_flow():
    async with _Server() as s:
        agent = TestAgent()
        client = TestClient()
        _agent_conn = ClientSideConnection(lambda _conn: client, s.client_writer, s.client_reader)
        client_conn = AgentSideConnection(lambda _conn: agent, s.server_writer, s.server_reader)

        # Agent -> Client notifications
        await client_conn.sessionUpdate(
            SessionNotification(
                sessionId="sess",
                update=SessionUpdate2(
                    sessionUpdate="agent_message_chunk",
                    content=ContentBlock1(type="text", text="Hello"),
                ),
            )
        )
        await client_conn.sessionUpdate(
            SessionNotification(
                sessionId="sess",
                update=SessionUpdate1(
                    sessionUpdate="user_message_chunk",
                    content=ContentBlock1(type="text", text="World"),
                ),
            )
        )

        # Wait for async dispatch
        for _ in range(50):
            if len(client.notifications) >= 2:
                break
            await asyncio.sleep(0.01)
        assert len(client.notifications) >= 2
        assert client.notifications[0].sessionId == "sess"


@pytest.mark.asyncio
async def test_concurrent_reads():
    async with _Server() as s:
        agent = TestAgent()
        client = TestClient()
        for i in range(5):
            client.files[f"/test/file{i}.txt"] = f"Content {i}"
        _agent_conn = ClientSideConnection(lambda _conn: client, s.client_writer, s.client_reader)
        client_conn = AgentSideConnection(lambda _conn: agent, s.server_writer, s.server_reader)

        async def read_one(i: int):
            return await client_conn.readTextFile(ReadTextFileRequest(sessionId="sess", path=f"/test/file{i}.txt"))

        results = await asyncio.gather(*(read_one(i) for i in range(5)))
        for i, res in enumerate(results):
            assert res.content == f"Content {i}"


@pytest.mark.asyncio
async def test_invalid_params_results_in_error_response():
    async with _Server() as s:
        # Only start agent-side (server) so we can inject raw request from client socket
        agent = TestAgent()
        _server_conn = AgentSideConnection(lambda _conn: agent, s.server_writer, s.server_reader)

        # Send initialize with wrong param type (protocolVersion should be int)
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "oops"}}
        s.client_writer.write((json.dumps(req) + "\n").encode())
        await s.client_writer.drain()

        # Read response
        line = await asyncio.wait_for(s.client_reader.readline(), timeout=1)
        resp = json.loads(line)
        assert resp["id"] == 1
        assert "error" in resp
        assert resp["error"]["code"] == -32602  # invalid params


@pytest.mark.asyncio
async def test_method_not_found_results_in_error_response():
    async with _Server() as s:
        agent = TestAgent()
        _server_conn = AgentSideConnection(lambda _conn: agent, s.server_writer, s.server_reader)

        req = {"jsonrpc": "2.0", "id": 2, "method": "unknown/method", "params": {}}
        s.client_writer.write((json.dumps(req) + "\n").encode())
        await s.client_writer.drain()

        line = await asyncio.wait_for(s.client_reader.readline(), timeout=1)
        resp = json.loads(line)
        assert resp["id"] == 2
        assert resp["error"]["code"] == -32601  # method not found


@pytest.mark.asyncio
async def test_set_session_mode_and_extensions():
    async with _Server() as s:
        agent = TestAgent()
        client = TestClient()
        agent_conn = ClientSideConnection(lambda _conn: client, s.client_writer, s.client_reader)
        _client_conn = AgentSideConnection(lambda _conn: agent, s.server_writer, s.server_reader)

        # setSessionMode
        resp = await agent_conn.setSessionMode(SetSessionModeRequest(sessionId="sess", modeId="yolo"))
        # Either empty object or typed response depending on implementation
        assert resp is None or resp.__class__.__name__ == "SetSessionModeResponse"

        # extMethod
        res = await agent_conn.extMethod("ping", {"x": 1})
        assert res.get("ok") is True

        # extNotification
        await agent_conn.extNotification("note", {"y": 2})
        # allow dispatch
        await asyncio.sleep(0.05)
        assert agent.ext_notes and agent.ext_notes[-1][0] == "note"


@pytest.mark.asyncio
async def test_ignore_invalid_messages():
    async with _Server() as s:
        agent = TestAgent()
        _server_conn = AgentSideConnection(lambda _conn: agent, s.server_writer, s.server_reader)

        # Message without id and method
        msg1 = {"jsonrpc": "2.0"}
        s.client_writer.write((json.dumps(msg1) + "\n").encode())
        await s.client_writer.drain()

        # Message without jsonrpc and without id/method
        msg2 = {"foo": "bar"}
        s.client_writer.write((json.dumps(msg2) + "\n").encode())
        await s.client_writer.drain()

        # Should not receive any response lines
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(s.client_reader.readline(), timeout=0.1)
