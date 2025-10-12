import asyncio

from acp import (
    Agent,
    AgentSideConnection,
    AuthenticateRequest,
    AuthenticateResponse,
    CancelNotification,
    InitializeRequest,
    InitializeResponse,
    LoadSessionRequest,
    LoadSessionResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    SetSessionModeRequest,
    SetSessionModeResponse,
    stdio_streams,
    PROTOCOL_VERSION,
)
from acp.schema import (
    AgentCapabilities,
    AgentMessageChunk,
    McpCapabilities,
    PromptCapabilities,
    SessionNotification,
    TextContentBlock,
)


class EchoAgent(Agent):
    def __init__(self, conn):
        self._conn = conn

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        mcp_caps: McpCapabilities = McpCapabilities(http=False, sse=False)
        prompt_caps: PromptCapabilities = PromptCapabilities(audio=False, embeddedContext=False, image=False)
        agent_caps: AgentCapabilities = AgentCapabilities(
            loadSession=False,
            mcpCapabilities=mcp_caps,
            promptCapabilities=prompt_caps,
        )
        return InitializeResponse(
            protocolVersion=PROTOCOL_VERSION,
            agentCapabilities=agent_caps,
        )

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
