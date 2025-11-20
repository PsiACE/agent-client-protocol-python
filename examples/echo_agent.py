import asyncio
from typing import Any
from uuid import uuid4

from acp import (
    Agent,
    AgentSideConnection,
    InitializeResponse,
    NewSessionResponse,
    PromptResponse,
    stdio_streams,
    text_block,
    update_agent_message,
)
from acp.schema import (
    AudioContentBlock,
    ClientCapabilities,
    EmbeddedResourceContentBlock,
    HttpMcpServer,
    ImageContentBlock,
    Implementation,
    ResourceContentBlock,
    SseMcpServer,
    StdioMcpServer,
    TextContentBlock,
)


class EchoAgent(Agent):
    def __init__(self, conn: AgentSideConnection) -> None:
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
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | StdioMcpServer], **kwargs: Any
    ) -> NewSessionResponse:
        return NewSessionResponse(session_id=uuid4().hex)

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
        for block in prompt:
            text = block.get("text", "") if isinstance(block, dict) else getattr(block, "text", "")
            chunk = update_agent_message(text_block(text))
            chunk.field_meta = {"echo": True}
            chunk.content.field_meta = {"echo": True}

            await self._conn.session_update(session_id=session_id, update=chunk, source="echo_agent")
        return PromptResponse(stop_reason="end_turn")


async def main() -> None:
    reader, writer = await stdio_streams()
    AgentSideConnection(EchoAgent, writer, reader)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
