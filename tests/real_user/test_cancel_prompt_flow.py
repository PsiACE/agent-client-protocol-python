import asyncio
from typing import Any

import pytest

from acp.schema import (
    AudioContentBlock,
    EmbeddedResourceContentBlock,
    ImageContentBlock,
    PromptRequest,
    PromptResponse,
    ResourceContentBlock,
    TextContentBlock,
)
from tests.conftest import TestAgent

# Regression from a real user session where cancel needed to interrupt a long-running prompt.


class LongRunningAgent(TestAgent):
    """Agent variant whose prompt waits for a cancel notification."""

    def __init__(self) -> None:
        super().__init__()
        self.prompt_started = asyncio.Event()
        self.cancel_received = asyncio.Event()

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
        self.prompt_started.set()
        try:
            await asyncio.wait_for(self.cancel_received.wait(), timeout=1.0)
        except asyncio.TimeoutError as exc:
            msg = "Cancel notification did not arrive while prompt pending"
            raise AssertionError(msg) from exc
        return PromptResponse(stop_reason="cancelled")

    async def cancel(self, session_id: str, **kwargs: Any) -> None:
        await super().cancel(session_id, **kwargs)
        self.cancel_received.set()


@pytest.mark.asyncio
@pytest.mark.parametrize("agent", [LongRunningAgent()])
async def test_cancel_reaches_agent_during_prompt(connect, agent) -> None:
    _, agent_conn = connect()

    prompt_task = asyncio.create_task(
        agent_conn.prompt(
            session_id="sess-xyz",
            prompt=[TextContentBlock(type="text", text="hello")],
        )
    )

    await agent.prompt_started.wait()
    assert not prompt_task.done(), "Prompt finished before cancel was sent"

    await agent_conn.cancel(session_id="sess-xyz")

    await asyncio.wait_for(agent.cancel_received.wait(), timeout=1.0)

    response = await asyncio.wait_for(prompt_task, timeout=1.0)
    assert response.stop_reason == "cancelled"
    assert agent.cancellations == ["sess-xyz"]
