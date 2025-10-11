import asyncio

import pytest

from acp import AgentSideConnection, CancelNotification, ClientSideConnection, PromptRequest, PromptResponse
from acp.schema import TextContentBlock
from tests.test_rpc import TestAgent, TestClient, _Server

# Regression from a real user session where cancel needed to interrupt a long-running prompt.


class LongRunningAgent(TestAgent):
    """Agent variant whose prompt waits for a cancel notification."""

    def __init__(self) -> None:
        super().__init__()
        self.prompt_started = asyncio.Event()
        self.cancel_received = asyncio.Event()

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        self.prompts.append(params)
        self.prompt_started.set()
        try:
            await asyncio.wait_for(self.cancel_received.wait(), timeout=1.0)
        except asyncio.TimeoutError as exc:
            msg = "Cancel notification did not arrive while prompt pending"
            raise AssertionError(msg) from exc
        return PromptResponse(stopReason="cancelled")

    async def cancel(self, params: CancelNotification) -> None:
        await super().cancel(params)
        self.cancel_received.set()


@pytest.mark.asyncio
async def test_cancel_reaches_agent_during_prompt() -> None:
    async with _Server() as server:
        agent = LongRunningAgent()
        client = TestClient()
        agent_conn = ClientSideConnection(lambda _conn: client, server.client_writer, server.client_reader)
        _client_conn = AgentSideConnection(lambda _conn: agent, server.server_writer, server.server_reader)

        prompt_request = PromptRequest(
            sessionId="sess-xyz",
            prompt=[TextContentBlock(type="text", text="hello")],
        )
        prompt_task = asyncio.create_task(agent_conn.prompt(prompt_request))

        await agent.prompt_started.wait()
        assert not prompt_task.done(), "Prompt finished before cancel was sent"

        await agent_conn.cancel(CancelNotification(sessionId="sess-xyz"))

        await asyncio.wait_for(agent.cancel_received.wait(), timeout=1.0)

        response = await asyncio.wait_for(prompt_task, timeout=1.0)
        assert response.stopReason == "cancelled"
        assert agent.cancellations == ["sess-xyz"]
