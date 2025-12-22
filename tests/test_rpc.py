import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from acp import (
    Agent,
    AuthenticateResponse,
    Client,
    CreateTerminalResponse,
    InitializeResponse,
    LoadSessionResponse,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SetSessionModeResponse,
    WriteTextFileResponse,
    spawn_agent_process,
    start_tool_call,
    update_agent_message_text,
    update_tool_call,
)
from acp.core import AgentSideConnection, ClientSideConnection
from acp.schema import (
    AgentMessageChunk,
    AllowedOutcome,
    AudioContentBlock,
    ClientCapabilities,
    DeniedOutcome,
    EmbeddedResourceContentBlock,
    EnvVariable,
    HttpMcpServer,
    ImageContentBlock,
    Implementation,
    McpServerStdio,
    PermissionOption,
    ResourceContentBlock,
    SseMcpServer,
    TextContentBlock,
    ToolCallLocation,
    ToolCallProgress,
    ToolCallStart,
    ToolCallUpdate,
    UserMessageChunk,
)
from tests.conftest import TestClient

# ------------------------ Tests --------------------------


@pytest.mark.asyncio
async def test_initialize_and_new_session(connect):
    _, agent_conn = connect()

    resp = await agent_conn.initialize(protocol_version=1)
    assert isinstance(resp, InitializeResponse)
    assert resp.protocol_version == 1

    new_sess = await agent_conn.new_session(mcp_servers=[], cwd="/test")
    assert new_sess.session_id == "test-session-123"

    load_resp = await agent_conn.load_session(session_id=new_sess.session_id, cwd="/test", mcp_servers=[])
    assert isinstance(load_resp, LoadSessionResponse)

    auth_resp = await agent_conn.authenticate(method_id="password")
    assert isinstance(auth_resp, AuthenticateResponse)

    mode_resp = await agent_conn.set_session_mode(session_id=new_sess.session_id, mode_id="ask")
    assert isinstance(mode_resp, SetSessionModeResponse)


@pytest.mark.asyncio
async def test_bidirectional_file_ops(client, connect):
    client.files["/test/file.txt"] = "Hello, World!"
    client_conn, _ = connect()

    # Agent asks client to read
    res = await client_conn.read_text_file(session_id="sess", path="/test/file.txt")
    assert res.content == "Hello, World!"

    # Agent asks client to write
    write_result = await client_conn.write_text_file(session_id="sess", path="/test/file.txt", content="Updated")
    assert isinstance(write_result, WriteTextFileResponse)
    assert client.files["/test/file.txt"] == "Updated"


@pytest.mark.asyncio
async def test_cancel_notification_and_capture_wire(connect, agent):
    _, agent_conn = connect()
    # Send cancel notification from client-side connection to agent
    await agent_conn.cancel(session_id="test-123")

    # Read raw line from server peer (it will be consumed by agent receive loop quickly).
    # Instead, wait a brief moment and assert agent recorded it.
    for _ in range(50):
        if agent.cancellations:
            break
        await asyncio.sleep(0.01)
    assert agent.cancellations == ["test-123"]


@pytest.mark.asyncio
async def test_session_notifications_flow(connect, client):
    client_conn, _ = connect()

    # Agent -> Client notifications
    await client_conn.session_update(
        session_id="sess",
        update=AgentMessageChunk(
            session_update="agent_message_chunk",
            content=TextContentBlock(type="text", text="Hello"),
        ),
    )
    await client_conn.session_update(
        session_id="sess",
        update=UserMessageChunk(
            session_update="user_message_chunk",
            content=TextContentBlock(type="text", text="World"),
        ),
    )

    # Wait for async dispatch
    for _ in range(50):
        if len(client.notifications) >= 2:
            break
        await asyncio.sleep(0.01)
    assert len(client.notifications) >= 2
    assert client.notifications[0].session_id == "sess"


@pytest.mark.asyncio
async def test_on_connect_create_terminal_handle(server):
    class _TerminalAgent(Agent):
        __test__ = False

        def __init__(self) -> None:
            self._conn: Client | None = None
            self.handle_id: str | None = None

        def on_connect(self, conn: Client) -> None:
            self._conn = conn

        async def prompt(
            self,
            prompt: list[TextContentBlock],
            session_id: str,
            **kwargs: Any,
        ) -> PromptResponse:
            assert self._conn is not None
            handle = await self._conn.create_terminal(command="echo", session_id=session_id)
            self.handle_id = handle.terminal_id
            return PromptResponse(stop_reason="end_turn")

    class _TerminalClient(TestClient):
        __test__ = False

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
            return CreateTerminalResponse(terminal_id="term-123")

    agent = _TerminalAgent()
    client = _TerminalClient()
    agent_conn = AgentSideConnection(agent, server.server_writer, server.server_reader, listening=True)
    client_conn = ClientSideConnection(client, server.client_writer, server.client_reader)

    await client_conn.prompt(session_id="sess", prompt=[TextContentBlock(type="text", text="start")])
    assert agent.handle_id == "term-123"

    await client_conn.close()
    await agent_conn.close()


@pytest.mark.asyncio
async def test_concurrent_reads(connect, client):
    for i in range(5):
        client.files[f"/test/file{i}.txt"] = f"Content {i}"
    client_conn, _ = connect()

    async def read_one(i: int):
        return await client_conn.read_text_file(session_id="sess", path=f"/test/file{i}.txt")

    results = await asyncio.gather(*(read_one(i) for i in range(5)))
    for i, res in enumerate(results):
        assert res.content == f"Content {i}"


@pytest.mark.asyncio
async def test_invalid_params_results_in_error_response(connect, server):
    # Only start agent-side (server) so we can inject raw request from client socket
    connect(connect_agent=True, connect_client=False)

    # Send initialize with wrong param type (protocolVersion should be int)
    req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "oops"}}
    server.client_writer.write((json.dumps(req) + "\n").encode())
    await server.client_writer.drain()

    # Read response
    line = await asyncio.wait_for(server.client_reader.readline(), timeout=1)
    resp = json.loads(line)
    assert resp["id"] == 1
    assert "error" in resp
    assert resp["error"]["code"] == -32602  # invalid params


@pytest.mark.asyncio
async def test_method_not_found_results_in_error_response(connect, server):
    connect(connect_agent=True, connect_client=False)

    req = {"jsonrpc": "2.0", "id": 2, "method": "unknown/method", "params": {}}
    server.client_writer.write((json.dumps(req) + "\n").encode())
    await server.client_writer.drain()

    line = await asyncio.wait_for(server.client_reader.readline(), timeout=1)
    resp = json.loads(line)
    assert resp["id"] == 2
    assert resp["error"]["code"] == -32601  # method not found


@pytest.mark.asyncio
async def test_set_session_mode_and_extensions(connect, agent, client):
    client_conn, agent_conn = connect()

    # setSessionMode
    resp = await agent_conn.set_session_mode(session_id="sess", mode_id="yolo")
    assert isinstance(resp, SetSessionModeResponse)

    # extMethod
    echo = await agent_conn.ext_method("example.com/echo", {"x": 1})
    assert echo == {"echo": {"x": 1}}

    # extNotification
    await agent_conn.ext_notification("note", {"y": 2})
    # allow dispatch
    await asyncio.sleep(0.05)
    assert agent.ext_notes and agent.ext_notes[-1][0] == "note"

    # client extension method
    ping = await client_conn.ext_method("example.com/ping", {"k": 3})
    assert ping == {"response": "pong", "params": {"k": 3}}
    assert client.ext_calls and client.ext_calls[-1] == ("example.com/ping", {"k": 3})


@pytest.mark.asyncio
async def test_ignore_invalid_messages(connect, server):
    connect(connect_agent=True, connect_client=False)

    # Message without id and method
    msg1 = {"jsonrpc": "2.0"}
    server.client_writer.write((json.dumps(msg1) + "\n").encode())
    await server.client_writer.drain()

    # Message without jsonrpc and without id/method
    msg2 = {"foo": "bar"}
    server.client_writer.write((json.dumps(msg2) + "\n").encode())
    await server.client_writer.drain()

    # Should not receive any response lines
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(server.client_reader.readline(), timeout=0.1)


class _ExampleAgent(Agent):
    __test__ = False

    def __init__(self) -> None:
        self._conn: Client | None = None
        self.permission_response: RequestPermissionResponse | None = None
        self.prompt_requests: list[PromptRequest] = []

    def on_connect(self, conn: Client) -> None:
        self._conn = conn

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: ClientCapabilities | None = None,
        client_info: Implementation | None = None,
        **kwargs: Any,
    ) -> InitializeResponse:
        return InitializeResponse(protocol_version=protocol_version)

    async def new_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio], **kwargs: Any
    ) -> NewSessionResponse:
        return NewSessionResponse(session_id="sess_demo")

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
        assert self._conn is not None
        self.prompt_requests.append(PromptRequest(prompt=prompt, session_id=session_id, field_meta=kwargs or None))

        await self._conn.session_update(
            session_id,
            update_agent_message_text("I'll help you with that."),
        )

        await self._conn.session_update(
            session_id,
            start_tool_call(
                "call_1",
                "Modifying configuration",
                kind="edit",
                status="pending",
                locations=[ToolCallLocation(path="/project/config.json")],
                raw_input={"path": "/project/config.json"},
            ),
        )

        permission_request = {
            "session_id": session_id,
            "tool_call": ToolCallUpdate(
                tool_call_id="call_1",
                title="Modifying configuration",
                kind="edit",
                status="pending",
                locations=[ToolCallLocation(path="/project/config.json")],
                raw_input={"path": "/project/config.json"},
            ),
            "options": [
                PermissionOption(kind="allow_once", name="Allow", option_id="allow"),
                PermissionOption(kind="reject_once", name="Reject", option_id="reject"),
            ],
        }
        response = await self._conn.request_permission(**permission_request)
        self.permission_response = response

        if isinstance(response.outcome, AllowedOutcome) and response.outcome.option_id == "allow":
            await self._conn.session_update(
                session_id,
                update_tool_call(
                    "call_1",
                    status="completed",
                    raw_output={"success": True},
                ),
            )
            await self._conn.session_update(
                session_id,
                update_agent_message_text("Done."),
            )

        return PromptResponse(stop_reason="end_turn")


class _ExampleClient(TestClient):
    __test__ = False

    def __init__(self) -> None:
        super().__init__()
        self.permission_requests: list[RequestPermissionRequest] = []

    async def request_permission(
        self,
        options: list[PermissionOption] | RequestPermissionRequest,
        session_id: str | None = None,
        tool_call: ToolCallUpdate | None = None,
        **kwargs: Any,
    ) -> RequestPermissionResponse:
        if isinstance(options, RequestPermissionRequest):
            params = options
        else:
            assert session_id is not None and tool_call is not None
            params = RequestPermissionRequest(
                options=options,
                session_id=session_id,
                tool_call=tool_call,
                field_meta=kwargs or None,
            )
        self.permission_requests.append(params)
        if not params.options:
            return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
        option = params.options[0]
        return RequestPermissionResponse(outcome=AllowedOutcome(option_id=option.option_id, outcome="selected"))


@pytest.mark.asyncio
@pytest.mark.parametrize("agent,client", [(_ExampleAgent(), _ExampleClient())])
async def test_example_agent_permission_flow(connect, client, agent):
    _, agent_conn = connect()

    init = await agent_conn.initialize(protocol_version=1)
    assert init.protocol_version == 1

    session = await agent_conn.new_session(mcp_servers=[], cwd="/workspace")
    assert session.session_id == "sess_demo"

    resp = await agent_conn.prompt(
        session_id=session.session_id,
        prompt=[TextContentBlock(type="text", text="Please edit config")],
    )
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

    async with spawn_agent_process(test_client, sys.executable, str(script)) as (client_conn, process):
        init = await client_conn.initialize(protocol_version=1)
        assert isinstance(init, InitializeResponse)
        session = await client_conn.new_session(mcp_servers=[], cwd=str(tmp_path))
        await client_conn.prompt(
            session_id=session.session_id,
            prompt=[TextContentBlock(type="text", text="hi spawn")],
        )

        # Wait for echo agent notification to arrive
        for _ in range(50):
            if test_client.notifications:
                break
            await asyncio.sleep(0.02)

        assert test_client.notifications

    assert process.returncode is not None
