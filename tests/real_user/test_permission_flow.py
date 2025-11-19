import asyncio

import pytest

from acp import AgentSideConnection, ClientSideConnection, PromptRequest, PromptResponse, RequestPermissionRequest
from acp.schema import PermissionOption, TextContentBlock, ToolCall
from tests.test_rpc import TestAgent, TestClient, _Server

# Regression from real-world runs where agents paused prompts to obtain user permission.


class PermissionRequestAgent(TestAgent):
    """Agent that asks the client for permission during a prompt."""

    def __init__(self, conn: AgentSideConnection) -> None:
        super().__init__()
        self._conn = conn
        self.permission_responses = []

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        permission = await self._conn.requestPermission(
            RequestPermissionRequest(
                session_id=params.session_id,
                options=[
                    PermissionOption(option_id="allow", name="Allow", kind="allow_once"),
                    PermissionOption(option_id="deny", name="Deny", kind="reject_once"),
                ],
                tool_call=ToolCall(tool_call_id="call-1", title="Write File"),
            )
        )
        self.permission_responses.append(permission)
        return await super().prompt(params)


@pytest.mark.asyncio
async def test_agent_request_permission_roundtrip() -> None:
    async with _Server() as server:
        client = TestClient()
        client.queue_permission_selected("allow")

        captured_agent = []

        agent_conn = ClientSideConnection(lambda _conn: client, server._client_writer, server._client_reader)
        _agent_conn = AgentSideConnection(
            lambda conn: captured_agent.append(PermissionRequestAgent(conn)) or captured_agent[-1],
            server._server_writer,
            server._server_reader,
        )

        response = await asyncio.wait_for(
            agent_conn.prompt(
                PromptRequest(
                    session_id="sess-perm",
                    prompt=[TextContentBlock(type="text", text="needs approval")],
                )
            ),
            timeout=1.0,
        )
        assert response.stop_reason == "end_turn"

        assert captured_agent, "Agent was not constructed"
        [agent] = captured_agent
        assert agent.permission_responses, "Agent did not receive permission response"
        permission_response = agent.permission_responses[0]
        assert permission_response.outcome.outcome == "selected"
        assert permission_response.outcome.option_id == "allow"
