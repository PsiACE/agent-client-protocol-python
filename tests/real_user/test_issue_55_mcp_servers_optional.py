import asyncio
from typing import Any

import pytest

from acp import InitializeResponse, LoadSessionResponse, NewSessionResponse
from acp.core import AgentSideConnection, ClientSideConnection
from acp.schema import HttpMcpServer, McpServerStdio, SseMcpServer
from tests.conftest import TestAgent, TestClient

# Regression from a real-world client run where `mcpServers` is omitted from session requests.


class Issue55Agent(TestAgent):
    def __init__(self) -> None:
        super().__init__()
        self.seen_new_session: tuple[str, Any] | None = None
        self.seen_load_session: tuple[str, str, Any] | None = None

    async def new_session(
        self,
        cwd: str,
        mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio] | None = None,
        **kwargs: Any,
    ) -> NewSessionResponse:
        self.seen_new_session = (cwd, mcp_servers)
        return await super().new_session(cwd=cwd, mcp_servers=mcp_servers, **kwargs)

    async def load_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio] | None = None,
        **kwargs: Any,
    ) -> LoadSessionResponse | None:
        self.seen_load_session = (cwd, session_id, mcp_servers)
        return await super().load_session(cwd=cwd, session_id=session_id, mcp_servers=mcp_servers, **kwargs)


@pytest.mark.asyncio
async def test_session_requests_allow_missing_mcp_servers(server) -> None:
    client = TestClient()
    captured_agent: list[Issue55Agent] = []

    agent_conn = ClientSideConnection(client, server._client_writer, server._client_reader)  # type: ignore[arg-type]
    _agent_side = AgentSideConnection(
        lambda _conn: captured_agent.append(Issue55Agent()) or captured_agent[-1],
        server._server_writer,
        server._server_reader,
        listening=True,
    )

    init = await asyncio.wait_for(agent_conn.initialize(protocol_version=1), timeout=1.0)
    assert isinstance(init, InitializeResponse)

    new_session = await asyncio.wait_for(agent_conn.new_session(cwd="/workspace"), timeout=1.0)
    assert isinstance(new_session, NewSessionResponse)

    load_session = await asyncio.wait_for(
        agent_conn.load_session(cwd="/workspace", session_id=new_session.session_id),
        timeout=1.0,
    )
    assert isinstance(load_session, LoadSessionResponse)

    assert captured_agent, "Agent was not constructed"
    [agent] = captured_agent
    assert agent.seen_new_session == ("/workspace", None)
    assert agent.seen_load_session == ("/workspace", new_session.session_id, None)
