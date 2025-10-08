import asyncio
from dataclasses import dataclass, field
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
from acp.schema import (
    AgentMessageChunk,
    AllowedOutcome,
    ContentToolCallContent,
    PermissionOption,
    RequestPermissionRequest,
    TextContentBlock,
    ToolCallUpdate,
)


@dataclass
class SessionState:
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    prompt_counter: int = 0

    def begin_prompt(self) -> None:
        self.prompt_counter += 1
        self.cancel_event.clear()

    def cancel(self) -> None:
        self.cancel_event.set()


class ExampleAgent(Agent):
    def __init__(self, conn: AgentSideConnection) -> None:
        self._conn = conn
        self._next_session_id = 0
        self._sessions: dict[str, SessionState] = {}

    def _session(self, session_id: str) -> SessionState:
        state = self._sessions.get(session_id)
        if state is None:
            state = SessionState()
            self._sessions[session_id] = state
        return state

    async def _send_text(self, session_id: str, text: str) -> None:
        await self._conn.sessionUpdate(
            SessionNotification(
                sessionId=session_id,
                update=AgentMessageChunk(
                    sessionUpdate="agent_message_chunk",
                    content=TextContentBlock(type="text", text=text),
                ),
            )
        )

    def _format_prompt_preview(self, blocks: list[Any]) -> str:
        parts: list[str] = []
        for block in blocks:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                else:
                    parts.append(f"<{block.get('type', 'content')}>")
            else:
                parts.append(getattr(block, "text", "<content>"))
        preview = " \n".join(filter(None, parts)).strip()
        return preview or "<empty prompt>"

    async def _request_permission(self, session_id: str, preview: str, state: SessionState) -> str:
        state.prompt_counter += 1
        request = RequestPermissionRequest(
            sessionId=session_id,
            toolCall=ToolCallUpdate(
                toolCallId=f"echo-{state.prompt_counter}",
                title="Echo input",
                kind="echo",
                status="pending",
                content=[
                    ContentToolCallContent(
                        type="content",
                        content=TextContentBlock(type="text", text=preview),
                    )
                ],
            ),
            options=[
                PermissionOption(optionId="allow-once", name="Allow once", kind="allow_once"),
                PermissionOption(optionId="deny", name="Deny", kind="reject_once"),
            ],
        )

        permission_task = asyncio.create_task(self._conn.requestPermission(request))
        cancel_task = asyncio.create_task(state.cancel_event.wait())

        done, pending = await asyncio.wait({permission_task, cancel_task}, return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()

        if cancel_task in done:
            permission_task.cancel()
            return "cancelled"

        try:
            response = await permission_task
        except asyncio.CancelledError:
            return "cancelled"
        except Exception as exc:  # noqa: BLE001
            await self._send_text(session_id, f"Permission failed: {exc}")
            return "error"

        if isinstance(response.outcome, AllowedOutcome):
            option_id = response.outcome.optionId
            if option_id.startswith("allow"):
                return "allowed"
            return "denied"
        return "cancelled"

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        return InitializeResponse(protocolVersion=PROTOCOL_VERSION, agentCapabilities=None, authMethods=[])

    async def authenticate(self, params: AuthenticateRequest) -> AuthenticateResponse | None:  # noqa: ARG002
        return {}

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:  # noqa: ARG002
        session_id = f"sess-{self._next_session_id}"
        self._next_session_id += 1
        self._sessions[session_id] = SessionState()
        return NewSessionResponse(sessionId=session_id)

    async def loadSession(self, params):  # type: ignore[override]
        return None

    async def setSessionMode(self, params: SetSessionModeRequest) -> SetSessionModeResponse | None:  # noqa: ARG002
        return {}

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        state = self._session(params.sessionId)
        state.begin_prompt()

        preview = self._format_prompt_preview(list(params.prompt))
        await self._send_text(params.sessionId, "Agent received a prompt. Checking permissions...")

        decision = await self._request_permission(params.sessionId, preview, state)
        if decision == "cancelled":
            await self._send_text(params.sessionId, "Prompt cancelled before permission decided.")
            return PromptResponse(stopReason="cancelled")
        if decision == "denied":
            await self._send_text(params.sessionId, "Permission denied by the client.")
            return PromptResponse(stopReason="permission_denied")
        if decision == "error":
            return PromptResponse(stopReason="error")

        await self._send_text(params.sessionId, "Permission granted. Echoing content:")

        for block in params.prompt:
            if state.cancel_event.is_set():
                await self._send_text(params.sessionId, "Prompt interrupted by cancellation.")
                return PromptResponse(stopReason="cancelled")
            text = self._format_prompt_preview([block])
            await self._send_text(params.sessionId, text)
            await asyncio.sleep(0.4)

        return PromptResponse(stopReason="end_turn")

    async def cancel(self, params: CancelNotification) -> None:  # noqa: ARG002
        state = self._sessions.get(params.sessionId)
        if state:
            state.cancel()
        await self._send_text(params.sessionId, "Agent received cancel signal.")

    async def extMethod(self, method: str, params: dict) -> dict:  # noqa: ARG002
        return {"example": "response"}

    async def extNotification(self, method: str, params: dict) -> None:  # noqa: ARG002
        return None


async def main() -> None:
    reader, writer = await stdio_streams()
    AgentSideConnection(lambda conn: ExampleAgent(conn), writer, reader)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
