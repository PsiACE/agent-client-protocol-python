import asyncio

from acp import (
    Agent,
    AgentSideConnection,
    InitializeRequest,
    InitializeResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    SessionNotification,
    stdio_streams,
)
from acp.schema import TextContentBlock, AgentMessageChunk


class EchoAgent(Agent):
    def __init__(self, conn):
        self._conn = conn

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        return InitializeResponse(protocolVersion=params.protocolVersion)

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:
        return NewSessionResponse(sessionId="sess-1")

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        for block in params.prompt:
            text = block.get("text", "") if isinstance(block, dict) else getattr(block, "text", "")
            await self._conn.sessionUpdate(
                SessionNotification(
                    sessionId=params.sessionId,
                    update=AgentMessageChunk(
                        sessionUpdate="agent_message_chunk",
                        content=TextContentBlock(type="text", text=text),
                    ),
                )
            )
        return PromptResponse(stopReason="end_turn")


async def main() -> None:
    reader, writer = await stdio_streams()
    AgentSideConnection(lambda conn: EchoAgent(conn), writer, reader)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
