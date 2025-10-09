import asyncio
import logging
from typing import Any

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


class ExampleAgent(Agent):
    def __init__(self, conn: AgentSideConnection) -> None:
        self._conn = conn
        self._next_session_id = 0

    async def _send_chunk(self, session_id: str, content: Any) -> None:
        await self._conn.sessionUpdate(
            SessionNotification(
                sessionId=session_id,
                update=AgentMessageChunk(
                    sessionUpdate="agent_message_chunk",
                    content=content,
                ),
            )
        )

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:  # noqa: ARG002
        logging.info("Received initialize request")
        return InitializeResponse(
            protocolVersion=PROTOCOL_VERSION,
            agentCapabilities=AgentCapabilities(
                loadSession=False,
                mcpCapabilities=McpCapabilities(http=False, sse=False),
                promptCapabilities=PromptCapabilities(audio=False, embeddedContext=False, image=False),
            ),
        )

    async def authenticate(self, params: AuthenticateRequest) -> AuthenticateResponse | None:  # noqa: ARG002
        logging.info("Received authenticate request")
        return AuthenticateResponse()

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:  # noqa: ARG002
        logging.info("Received new session request")
        session_id = str(self._next_session_id)
        self._next_session_id += 1
        return NewSessionResponse(sessionId=session_id)

    async def loadSession(self, params: LoadSessionRequest) -> LoadSessionResponse | None:  # noqa: ARG002
        logging.info("Received load session request")
        return LoadSessionResponse()

    async def setSessionMode(self, params: SetSessionModeRequest) -> SetSessionModeResponse | None:  # noqa: ARG002
        logging.info("Received set session mode request")
        return SetSessionModeResponse()

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        logging.info("Received prompt request")

        # Notify the client what it just sent and then echo each content block back.
        await self._send_chunk(
            params.sessionId,
            TextContentBlock(type="text", text="Client sent:"),
        )
        for block in params.prompt:
            await self._send_chunk(params.sessionId, block)

        return PromptResponse(stopReason="end_turn")

    async def cancel(self, params: CancelNotification) -> None:  # noqa: ARG002
        logging.info("Received cancel notification")

    async def extMethod(self, method: str, params: dict) -> dict:  # noqa: ARG002
        logging.info("Received extension method call: %s", method)
        return {"example": "response"}

    async def extNotification(self, method: str, params: dict) -> None:  # noqa: ARG002
        logging.info("Received extension notification: %s", method)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    reader, writer = await stdio_streams()
    AgentSideConnection(ExampleAgent, writer, reader)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
