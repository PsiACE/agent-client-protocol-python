import asyncio
import logging
from typing import Any

from acp import (
    PROTOCOL_VERSION,
    Agent,
    AuthenticateResponse,
    InitializeResponse,
    LoadSessionResponse,
    NewSessionResponse,
    PromptResponse,
    SetSessionModeResponse,
    run_agent,
    text_block,
    update_agent_message,
)
from acp.interfaces import Client
from acp.schema import (
    AgentCapabilities,
    AgentMessageChunk,
    AudioContentBlock,
    ClientCapabilities,
    EmbeddedResourceContentBlock,
    HttpMcpServer,
    ImageContentBlock,
    Implementation,
    McpServerStdio,
    ResourceContentBlock,
    SseMcpServer,
    TextContentBlock,
)


class ExampleAgent(Agent):
    _conn: Client

    def __init__(self) -> None:
        self._next_session_id = 0
        self._sessions: set[str] = set()

    def on_connect(self, conn: Client) -> None:
        self._conn = conn

    async def _send_agent_message(self, session_id: str, content: Any) -> None:
        update = content if isinstance(content, AgentMessageChunk) else update_agent_message(content)
        await self._conn.session_update(session_id, update)

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: ClientCapabilities | None = None,
        client_info: Implementation | None = None,
        **kwargs: Any,
    ) -> InitializeResponse:
        logging.info("Received initialize request")
        return InitializeResponse(
            protocol_version=PROTOCOL_VERSION,
            agent_capabilities=AgentCapabilities(),
            agent_info=Implementation(name="example-agent", title="Example Agent", version="0.1.0"),
        )

    async def authenticate(self, method_id: str, **kwargs: Any) -> AuthenticateResponse | None:
        logging.info("Received authenticate request %s", method_id)
        return AuthenticateResponse()

    async def new_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio], **kwargs: Any
    ) -> NewSessionResponse:
        logging.info("Received new session request")
        session_id = str(self._next_session_id)
        self._next_session_id += 1
        self._sessions.add(session_id)
        return NewSessionResponse(session_id=session_id, modes=None)

    async def load_session(
        self, cwd: str, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio], session_id: str, **kwargs: Any
    ) -> LoadSessionResponse | None:
        logging.info("Received load session request %s", session_id)
        self._sessions.add(session_id)
        return LoadSessionResponse()

    async def set_session_mode(self, mode_id: str, session_id: str, **kwargs: Any) -> SetSessionModeResponse | None:
        logging.info("Received set session mode request %s -> %s", session_id, mode_id)
        return SetSessionModeResponse()

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
        logging.info("Received prompt request for session %s", session_id)
        if session_id not in self._sessions:
            self._sessions.add(session_id)

        await self._send_agent_message(session_id, text_block("Client sent:"))
        for block in prompt:
            await self._send_agent_message(session_id, block)
        return PromptResponse(stop_reason="end_turn")

    async def cancel(self, session_id: str, **kwargs: Any) -> None:
        logging.info("Received cancel notification for session %s", session_id)

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        logging.info("Received extension method call: %s", method)
        return {"example": "response"}

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        logging.info("Received extension notification: %s", method)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await run_agent(ExampleAgent())


if __name__ == "__main__":
    asyncio.run(main())
