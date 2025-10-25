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
    session_notification,
    stdio_streams,
    text_block,
    update_agent_message,
    PROTOCOL_VERSION,
)
from acp.schema import AgentCapabilities, AgentMessageChunk, Implementation


class ExampleAgent(Agent):
    def __init__(self, conn: AgentSideConnection) -> None:
        self._conn = conn
        self._next_session_id = 0
        self._sessions: set[str] = set()

    async def _send_agent_message(self, session_id: str, content: Any) -> None:
        update = content if isinstance(content, AgentMessageChunk) else update_agent_message(content)
        await self._conn.sessionUpdate(session_notification(session_id, update))

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:  # noqa: ARG002
        logging.info("Received initialize request")
        return InitializeResponse(
            protocolVersion=PROTOCOL_VERSION,
            agentCapabilities=AgentCapabilities(),
            agentInfo=Implementation(name="example-agent", title="Example Agent", version="0.1.0"),
        )

    async def authenticate(self, params: AuthenticateRequest) -> AuthenticateResponse | None:  # noqa: ARG002
        logging.info("Received authenticate request %s", params.methodId)
        return AuthenticateResponse()

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:  # noqa: ARG002
        logging.info("Received new session request")
        session_id = str(self._next_session_id)
        self._next_session_id += 1
        self._sessions.add(session_id)
        return NewSessionResponse(sessionId=session_id, modes=None)

    async def loadSession(self, params: LoadSessionRequest) -> LoadSessionResponse | None:  # noqa: ARG002
        logging.info("Received load session request %s", params.sessionId)
        self._sessions.add(params.sessionId)
        return LoadSessionResponse()

    async def setSessionMode(self, params: SetSessionModeRequest) -> SetSessionModeResponse | None:  # noqa: ARG002
        logging.info("Received set session mode request %s -> %s", params.sessionId, params.modeId)
        return SetSessionModeResponse()

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        logging.info("Received prompt request for session %s", params.sessionId)
        if params.sessionId not in self._sessions:
            self._sessions.add(params.sessionId)

        await self._send_agent_message(params.sessionId, text_block("Client sent:"))
        for block in params.prompt:
            await self._send_agent_message(params.sessionId, block)

        return PromptResponse(stopReason="end_turn")

    async def cancel(self, params: CancelNotification) -> None:  # noqa: ARG002
        logging.info("Received cancel notification for session %s", params.sessionId)

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
