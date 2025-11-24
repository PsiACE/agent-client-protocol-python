import asyncio
from typing import Any

import pytest

from acp import PromptResponse
from acp.core import AgentSideConnection, ClientSideConnection
from acp.schema import (
    AudioContentBlock,
    EmbeddedResourceContentBlock,
    ImageContentBlock,
    PermissionOption,
    ResourceContentBlock,
    TextContentBlock,
    ToolCallUpdate,
)
from tests.conftest import TestAgent, TestClient

# Regression from real-world runs where agents paused prompts to obtain user permission.


class PermissionRequestAgent(TestAgent):
    """Agent that asks the client for permission during a prompt."""

    def __init__(self, conn: AgentSideConnection) -> None:
        super().__init__()
        self._conn = conn
        self.permission_responses = []

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
        permission = await self._conn.request_permission(
            session_id=session_id,
            options=[
                PermissionOption(option_id="allow", name="Allow", kind="allow_once"),
                PermissionOption(option_id="deny", name="Deny", kind="reject_once"),
            ],
            tool_call=ToolCallUpdate(tool_call_id="call-1", title="Write File"),
        )
        self.permission_responses.append(permission)
        return await super().prompt(prompt, session_id, **kwargs)


@pytest.mark.asyncio
async def test_agent_request_permission_roundtrip(server) -> None:
    client = TestClient()
    client.queue_permission_selected("allow")

    captured_agent = []

    agent_conn = ClientSideConnection(client, server._client_writer, server._client_reader)  # type: ignore[arg-type]
    _agent_conn = AgentSideConnection(
        lambda conn: captured_agent.append(PermissionRequestAgent(conn)) or captured_agent[-1],
        server._server_writer,
        server._server_reader,
        listening=True,
    )

    response = await asyncio.wait_for(
        agent_conn.prompt(
            session_id="sess-perm",
            prompt=[TextContentBlock(type="text", text="needs approval")],
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
