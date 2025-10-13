import asyncio
from uuid import uuid4

from acp import (
    Agent,
    AgentSideConnection,
    InitializeRequest,
    InitializeResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    session_notification,
    stdio_streams,
    text_block,
    update_agent_message,
)


class EchoAgent(Agent):
    def __init__(self, conn):
        self._conn = conn

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        return InitializeResponse(protocolVersion=params.protocolVersion)

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:
        return NewSessionResponse(sessionId=uuid4().hex)

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        for block in params.prompt:
            text = getattr(block, "text", "")
            await self._conn.sessionUpdate(
                session_notification(
                    params.sessionId,
                    update_agent_message(text_block(text)),
                )
            )
        return PromptResponse(stopReason="end_turn")


async def main() -> None:
    reader, writer = await stdio_streams()
    AgentSideConnection(lambda conn: EchoAgent(conn), writer, reader)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
