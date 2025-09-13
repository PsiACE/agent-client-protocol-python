import asyncio
from typing import Any

from acp import (
    Agent,
    AgentSideConnection,
    AuthenticateRequest,
    AuthenticateResponse,
    CancelNotification,
    InitializeRequest,
    InitializeResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    SessionNotification,
    SetSessionModeRequest,
    SetSessionModeResponse,
    stdio_streams,
    PROTOCOL_VERSION,
)
from acp.schema import ContentBlock1, SessionUpdate2


class ExampleAgent(Agent):
    def __init__(self, conn: AgentSideConnection) -> None:
        self._conn = conn
        self._next_session_id = 0

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        return InitializeResponse(protocolVersion=PROTOCOL_VERSION, agentCapabilities=None, authMethods=[])

    async def authenticate(self, params: AuthenticateRequest) -> AuthenticateResponse | None:  # noqa: ARG002
        return {}

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:  # noqa: ARG002
        session_id = f"sess-{self._next_session_id}"
        self._next_session_id += 1
        return NewSessionResponse(sessionId=session_id)

    async def loadSession(self, params):  # type: ignore[override]
        return None

    async def setSessionMode(self, params: SetSessionModeRequest) -> SetSessionModeResponse | None:  # noqa: ARG002
        return {}

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        # Stream a couple of agent message chunks, then end the turn
        # 1) Prefix
        await self._conn.sessionUpdate(
            SessionNotification(
                sessionId=params.sessionId,
                update=SessionUpdate2(
                    sessionUpdate="agent_message_chunk",
                    content=ContentBlock1(type="text", text="Client sent: "),
                ),
            )
        )
        # 2) Echo text blocks
        for block in params.prompt:
            if isinstance(block, dict):
                # tolerate raw dicts
                if block.get("type") == "text":
                    text = str(block.get("text", ""))
                else:
                    text = f"<{block.get('type', 'content')}>"
            else:
                # pydantic model ContentBlock1
                text = getattr(block, "text", "<content>")
            await self._conn.sessionUpdate(
                SessionNotification(
                    sessionId=params.sessionId,
                    update=SessionUpdate2(
                        sessionUpdate="agent_message_chunk",
                        content=ContentBlock1(type="text", text=text),
                    ),
                )
            )
        return PromptResponse(stopReason="end_turn")

    async def cancel(self, params: CancelNotification) -> None:  # noqa: ARG002
        return None

    async def extMethod(self, method: str, params: dict) -> dict:  # noqa: ARG002
        return {"example": "response"}

    async def extNotification(self, method: str, params: dict) -> None:  # noqa: ARG002
        return None


async def main() -> None:
    reader, writer = await stdio_streams()
    # For an agent process, local writes go to client stdin (writer=stdout)
    AgentSideConnection(lambda conn: ExampleAgent(conn), writer, reader)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
