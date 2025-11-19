import asyncio
import contextlib
import json
import sys
from pathlib import Path

import pytest

from acp import (
    Agent,
    AgentSideConnection,
    AuthenticateRequest,
    AuthenticateResponse,
    CancelNotification,
    Client,
    ClientSideConnection,
    InitializeRequest,
    InitializeResponse,
    LoadSessionRequest,
    LoadSessionResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    RequestError,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SessionNotification,
    SetSessionModelRequest,
    SetSessionModelResponse,
    SetSessionModeRequest,
    SetSessionModeResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
    session_notification,
    spawn_agent_process,
    start_tool_call,
    update_agent_message_text,
    update_tool_call,
)
from acp.schema import (
    AgentMessageChunk,
    AllowedOutcome,
    DeniedOutcome,
    PermissionOption,
    TextContentBlock,
    ToolCall,
    ToolCallLocation,
    ToolCallProgress,
    ToolCallStart,
    UserMessageChunk,
)

# --------------------- Test Utilities ---------------------


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


# --------------------- Test Doubles -----------------------


class TestClient(Client):
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


class TestAgent(Agent):
    __test__ = False  # prevent pytest from collecting this class

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

    async def loadSession(self, params: LoadSessionRequest) -> LoadSessionResponse:
        return LoadSessionResponse()

    async def authenticate(self, params: AuthenticateRequest) -> AuthenticateResponse:
        return AuthenticateResponse()

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        self.prompts.append(params)
        return PromptResponse(stop_reason="end_turn")

    async def cancel(self, params: CancelNotification) -> None:
        self.cancellations.append(params.session_id)

    async def setSessionMode(self, params: SetSessionModeRequest) -> SetSessionModeResponse:
        return SetSessionModeResponse()

    async def setSessionModel(self, params: SetSessionModelRequest) -> SetSessionModelResponse:
        return SetSessionModelResponse()

    async def extMethod(self, method: str, params: dict) -> dict:
        self.ext_calls.append((method, params))
        if method == "example.com/echo":
            return {"echo": params}
        raise RequestError.method_not_found(method)

    async def extNotification(self, method: str, params: dict) -> None:
        self.ext_notes.append((method, params))


# ------------------------ Tests --------------------------


@pytest.mark.asyncio
async def test_initialize_and_new_session():
    async with _Server() as s:
        agent = TestAgent()
        client = TestClient()
        # server side is agent; client side is client
        agent_conn = ClientSideConnection(lambda _conn: client, s._client_writer, s._client_reader)
        _client_conn = AgentSideConnection(lambda _conn: agent, s._server_writer, s._server_reader)

        resp = await agent_conn.initialize(InitializeRequest(protocol_version=1))
        assert isinstance(resp, InitializeResponse)
        assert resp.protocol_version == 1

        new_sess = await agent_conn.newSession(NewSessionRequest(mcp_servers=[], cwd="/test"))
        assert new_sess.session_id == "test-session-123"

        load_resp = await agent_conn.loadSession(
            LoadSessionRequest(session_id=new_sess.session_id, cwd="/test", mcp_servers=[])
        )
        assert isinstance(load_resp, LoadSessionResponse)

        auth_resp = await agent_conn.authenticate(AuthenticateRequest(method_id="password"))
        assert isinstance(auth_resp, AuthenticateResponse)

        mode_resp = await agent_conn.setSessionMode(
            SetSessionModeRequest(session_id=new_sess.session_id, mode_id="ask")
        )
        assert isinstance(mode_resp, SetSessionModeResponse)

        model_resp = await agent_conn.setSessionModel(
            SetSessionModelRequest(session_id=new_sess.session_id, model_id="gpt-4o")
        )
        assert isinstance(model_resp, SetSessionModelResponse)


@pytest.mark.asyncio
async def test_bidirectional_file_ops():
    async with _Server() as s:
        agent = TestAgent()
        client = TestClient()
        client.files["/test/file.txt"] = "Hello, World!"
        _agent_conn = ClientSideConnection(lambda _conn: client, s._client_writer, s._client_reader)
        client_conn = AgentSideConnection(lambda _conn: agent, s._server_writer, s._server_reader)

        # Agent asks client to read
        res = await client_conn.readTextFile(ReadTextFileRequest(session_id="sess", path="/test/file.txt"))
        assert res.content == "Hello, World!"

        # Agent asks client to write
        write_result = await client_conn.writeTextFile(
            WriteTextFileRequest(session_id="sess", path="/test/file.txt", content="Updated")
        )
        assert isinstance(write_result, WriteTextFileResponse)
        assert client.files["/test/file.txt"] == "Updated"


@pytest.mark.asyncio
async def test_cancel_notification_and_capture_wire():
    async with _Server() as s:
        # Build only agent-side (server) connection. Client side: raw reader to inspect wire
        agent = TestAgent()
        client = TestClient()
        agent_conn = ClientSideConnection(lambda _conn: client, s._client_writer, s._client_reader)
        _client_conn = AgentSideConnection(lambda _conn: agent, s._server_writer, s._server_reader)

        # Send cancel notification from client-side connection to agent
        await agent_conn.cancel(CancelNotification(session_id="test-123"))

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
        _agent_conn = ClientSideConnection(lambda _conn: client, s._client_writer, s._client_reader)
        client_conn = AgentSideConnection(lambda _conn: agent, s._server_writer, s._server_reader)

        # Agent -> Client notifications
        await client_conn.sessionUpdate(
            SessionNotification(
                session_id="sess",
                update=AgentMessageChunk(
                    session_update="agent_message_chunk",
                    content=TextContentBlock(type="text", text="Hello"),
                ),
            )
        )
        await client_conn.sessionUpdate(
            SessionNotification(
                session_id="sess",
                update=UserMessageChunk(
                    session_update="user_message_chunk",
                    content=TextContentBlock(type="text", text="World"),
                ),
            )
        )

        # Wait for async dispatch
        for _ in range(50):
            if len(client.notifications) >= 2:
                break
            await asyncio.sleep(0.01)
        assert len(client.notifications) >= 2
        assert client.notifications[0].session_id == "sess"


@pytest.mark.asyncio
async def test_concurrent_reads():
    async with _Server() as s:
        agent = TestAgent()
        client = TestClient()
        for i in range(5):
            client.files[f"/test/file{i}.txt"] = f"Content {i}"
        _agent_conn = ClientSideConnection(lambda _conn: client, s._client_writer, s._client_reader)
        client_conn = AgentSideConnection(lambda _conn: agent, s._server_writer, s._server_reader)

        async def read_one(i: int):
            return await client_conn.readTextFile(ReadTextFileRequest(session_id="sess", path=f"/test/file{i}.txt"))

        results = await asyncio.gather(*(read_one(i) for i in range(5)))
        for i, res in enumerate(results):
            assert res.content == f"Content {i}"


@pytest.mark.asyncio
async def test_invalid_params_results_in_error_response():
    async with _Server() as s:
        # Only start agent-side (server) so we can inject raw request from client socket
        agent = TestAgent()
        _server_conn = AgentSideConnection(lambda _conn: agent, s._server_writer, s._server_reader)

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
        _server_conn = AgentSideConnection(lambda _conn: agent, s._server_writer, s._server_reader)

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
        agent_conn = ClientSideConnection(lambda _conn: client, s._client_writer, s._client_reader)
        client_conn = AgentSideConnection(lambda _conn: agent, s._server_writer, s._server_reader)

        # setSessionMode
        resp = await agent_conn.setSessionMode(SetSessionModeRequest(session_id="sess", mode_id="yolo"))
        assert isinstance(resp, SetSessionModeResponse)

        model_resp = await agent_conn.setSessionModel(SetSessionModelRequest(session_id="sess", model_id="gpt-4o-mini"))
        assert isinstance(model_resp, SetSessionModelResponse)

        # extMethod
        echo = await agent_conn.extMethod("example.com/echo", {"x": 1})
        assert echo == {"echo": {"x": 1}}

        # extNotification
        await agent_conn.extNotification("note", {"y": 2})
        # allow dispatch
        await asyncio.sleep(0.05)
        assert agent.ext_notes and agent.ext_notes[-1][0] == "note"

        # client extension method
        ping = await client_conn.extMethod("example.com/ping", {"k": 3})
        assert ping == {"response": "pong", "params": {"k": 3}}
        assert client.ext_calls and client.ext_calls[-1] == ("example.com/ping", {"k": 3})


@pytest.mark.asyncio
async def test_ignore_invalid_messages():
    async with _Server() as s:
        agent = TestAgent()
        _server_conn = AgentSideConnection(lambda _conn: agent, s._server_writer, s._server_reader)

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


class _ExampleAgent(Agent):
    __test__ = False

    def __init__(self) -> None:
        self._conn: AgentSideConnection | None = None
        self.permission_response: RequestPermissionResponse | None = None
        self.prompt_requests: list[PromptRequest] = []

    def bind(self, conn: AgentSideConnection) -> "_ExampleAgent":
        self._conn = conn
        return self

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        return InitializeResponse(protocol_version=params.protocol_version)

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:
        return NewSessionResponse(session_id="sess_demo")

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        assert self._conn is not None
        self.prompt_requests.append(params)

        await self._conn.sessionUpdate(
            session_notification(
                params.session_id,
                update_agent_message_text("I'll help you with that."),
            )
        )

        await self._conn.sessionUpdate(
            session_notification(
                params.session_id,
                start_tool_call(
                    "call_1",
                    "Modifying configuration",
                    kind="edit",
                    status="pending",
                    locations=[ToolCallLocation(path="/project/config.json")],
                    raw_input={"path": "/project/config.json"},
                ),
            )
        )

        permission_request = RequestPermissionRequest(
            session_id=params.session_id,
            tool_call=ToolCall(
                tool_call_id="call_1",
                title="Modifying configuration",
                kind="edit",
                status="pending",
                locations=[ToolCallLocation(path="/project/config.json")],
                raw_input={"path": "/project/config.json"},
            ),
            options=[
                PermissionOption(kind="allow_once", name="Allow", option_id="allow"),
                PermissionOption(kind="reject_once", name="Reject", option_id="reject"),
            ],
        )
        response = await self._conn.requestPermission(permission_request)
        self.permission_response = response

        if isinstance(response.outcome, AllowedOutcome) and response.outcome.option_id == "allow":
            await self._conn.sessionUpdate(
                session_notification(
                    params.session_id,
                    update_tool_call(
                        "call_1",
                        status="completed",
                        raw_output={"success": True},
                    ),
                )
            )
            await self._conn.sessionUpdate(
                session_notification(
                    params.session_id,
                    update_agent_message_text("Done."),
                )
            )

        return PromptResponse(stop_reason="end_turn")


class _ExampleClient(TestClient):
    __test__ = False

    def __init__(self) -> None:
        super().__init__()
        self.permission_requests: list[RequestPermissionRequest] = []

    async def requestPermission(self, params: RequestPermissionRequest) -> RequestPermissionResponse:
        self.permission_requests.append(params)
        if not params.options:
            return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
        option = params.options[0]
        return RequestPermissionResponse(outcome=AllowedOutcome(option_id=option.option_id, outcome="selected"))


@pytest.mark.asyncio
async def test_example_agent_permission_flow():
    async with _Server() as s:
        agent = _ExampleAgent()
        client = _ExampleClient()

        agent_conn = ClientSideConnection(lambda _conn: client, s._client_writer, s._client_reader)
        AgentSideConnection(lambda conn: agent.bind(conn), s._server_writer, s._server_reader)

        init = await agent_conn.initialize(InitializeRequest(protocol_version=1))
        assert init.protocol_version == 1

        session = await agent_conn.newSession(NewSessionRequest(mcp_servers=[], cwd="/workspace"))
        assert session.session_id == "sess_demo"
        prompt = PromptRequest(
            session_id=session.session_id,
            prompt=[TextContentBlock(type="text", text="Please edit config")],
        )
        resp = await agent_conn.prompt(prompt)
        assert resp.stop_reason == "end_turn"
        for _ in range(50):
            if len(client.notifications) >= 4:
                break
            await asyncio.sleep(0.02)

        assert len(client.notifications) >= 4
        session_updates = [getattr(note.update, "session_update", None) for note in client.notifications]
        assert session_updates[:4] == ["agent_message_chunk", "tool_call", "tool_call_update", "agent_message_chunk"]

        first_message = client.notifications[0].update
        assert isinstance(first_message, AgentMessageChunk)
        assert isinstance(first_message.content, TextContentBlock)
        assert first_message.content.text == "I'll help you with that."

        tool_call = client.notifications[1].update
        assert isinstance(tool_call, ToolCallStart)
        assert tool_call.title == "Modifying configuration"
        assert tool_call.status == "pending"

        tool_update = client.notifications[2].update
        assert isinstance(tool_update, ToolCallProgress)
        assert tool_update.status == "completed"
        assert tool_update.raw_output == {"success": True}

        final_message = client.notifications[3].update
        assert isinstance(final_message, AgentMessageChunk)
        assert isinstance(final_message.content, TextContentBlock)
        assert final_message.content.text == "Done."

        assert len(client.permission_requests) == 1
        options = client.permission_requests[0].options
        assert [opt.option_id for opt in options] == ["allow", "reject"]

        assert agent.permission_response is not None
        assert isinstance(agent.permission_response.outcome, AllowedOutcome)
        assert agent.permission_response.outcome.option_id == "allow"


@pytest.mark.asyncio
async def test_spawn_agent_process_roundtrip(tmp_path):
    script = Path(__file__).parents[1] / "examples" / "echo_agent.py"
    assert script.exists()

    test_client = TestClient()

    async with spawn_agent_process(lambda _agent: test_client, sys.executable, str(script)) as (client_conn, process):
        init = await client_conn.initialize(InitializeRequest(protocol_version=1))
        assert isinstance(init, InitializeResponse)
        session = await client_conn.newSession(NewSessionRequest(cwd=str(tmp_path), mcp_servers=[]))
        prompt = PromptRequest(
            session_id=session.session_id,
            prompt=[TextContentBlock(type="text", text="hi spawn")],
        )
        await client_conn.prompt(prompt)

        # Wait for echo agent notification to arrive
        for _ in range(50):
            if test_client.notifications:
                break
            await asyncio.sleep(0.02)

        assert test_client.notifications

    assert process.returncode is not None
