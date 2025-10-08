import asyncio
import os
import sys
from dataclasses import dataclass

from acp import (
    Client,
    ClientSideConnection,
    PROTOCOL_VERSION,
    CancelNotification,
    InitializeRequest,
    NewSessionRequest,
    PromptRequest,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SessionNotification,
)
from acp.schema import AllowedOutcome, DeniedOutcome


@dataclass
class _PendingPermission:
    request: RequestPermissionRequest
    future: asyncio.Future[RequestPermissionResponse]


class ExampleClient(Client):
    def __init__(self) -> None:
        self._pending_permission: _PendingPermission | None = None
        self._active_prompt: asyncio.Task | None = None

    # --- Helpers -----------------------------------------------------------

    def _print(self, message: str) -> None:
        print(message)

    def prompt_in_progress(self) -> bool:
        task = self._active_prompt
        return task is not None and not task.done()

    def _attach_prompt_task(self, task: asyncio.Task) -> None:
        if self.prompt_in_progress():
            raise RuntimeError("prompt already running")
        self._active_prompt = task

        def _done_callback(fut: asyncio.Future) -> None:
            try:
                result = fut.result()
            except asyncio.CancelledError:
                self._print("| Prompt cancelled locally.")
            except Exception as exc:  # noqa: BLE001
                print(f"error: {exc}", file=sys.stderr)
            else:
                stop_reason = getattr(result, "stopReason", "<unknown>")
                self._print(f"| Prompt finished (stopReason={stop_reason}).")
            finally:
                self._active_prompt = None

        task.add_done_callback(_done_callback)

    def _set_pending_permission(self, params: RequestPermissionRequest) -> asyncio.Future[RequestPermissionResponse]:
        if self._pending_permission is not None:
            raise RuntimeError("permission already pending")
        fut: asyncio.Future[RequestPermissionResponse] = asyncio.get_running_loop().create_future()
        self._pending_permission = _PendingPermission(request=params, future=fut)
        return fut

    def pending_permission(self) -> _PendingPermission | None:
        return self._pending_permission

    def resolve_permission(self, allowed: bool) -> None:
        pending = self._pending_permission
        if pending is None:
            self._print("| No permission request to resolve.")
            return
        if pending.future.done():
            return
        allow_option = next((opt for opt in pending.request.options if opt.kind.startswith("allow")), None)
        deny_option = next((opt for opt in pending.request.options if opt.kind.startswith("reject")), None)

        if allowed and allow_option is not None:
            outcome = AllowedOutcome(optionId=allow_option.optionId, outcome="selected")
            self._print("| Permission granted.")
        elif not allowed and deny_option is not None:
            outcome = AllowedOutcome(optionId=deny_option.optionId, outcome="selected")
            self._print("| Permission denied.")
        else:
            outcome = DeniedOutcome(outcome="cancelled")
            self._print("| Permission response unavailable; treating as cancelled.")

        pending.future.set_result(RequestPermissionResponse(outcome=outcome))
        self._pending_permission = None

    # --- Client protocol callbacks ---------------------------------------

    async def sessionUpdate(self, params: SessionNotification) -> None:
        update = params.update
        kind = getattr(update, "sessionUpdate", None) if not isinstance(update, dict) else update.get("sessionUpdate")
        if kind == "agent_message_chunk":
            content = update["content"] if isinstance(update, dict) else getattr(update, "content", None)
            text = content.get("text") if isinstance(content, dict) else getattr(content, "text", "<content>")
            self._print(f"| Agent: {text}")

    async def requestPermission(self, params: RequestPermissionRequest) -> RequestPermissionResponse:
        preview_parts = []
        for item in params.toolCall.content or []:
            block = item["content"] if isinstance(item, dict) else getattr(item, "content", None)
            text = block.get("text") if isinstance(block, dict) else getattr(block, "text", None)
            if text:
                preview_parts.append(str(text))
        preview = preview_parts[0] if preview_parts else "<no preview>"

        self._print("| Agent requested permission:")
        self._print(f"|   Tool: {params.toolCall.title}")
        self._print(f"|   Preview: {preview}")
        self._print("|   Respond with '/allow' or '/deny'.")

        future = self._set_pending_permission(params)
        return await future

    async def read_console(self, prompt: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: input(prompt))


async def interactive_loop(conn: ClientSideConnection, session_id: str, ui: ExampleClient) -> None:
    ui._print(
        "Type text to send, '/allow' or '/deny' for permission requests, '/cancel' to stop the current prompt, '/quit' to exit."
    )
    while True:
        line: str
        try:
            line = await ui.read_console("> ")
        except EOFError:
            break
        command = line.strip()
        if not command:
            continue

        if ui.pending_permission() is not None:
            cmd = command.lower()
            if cmd in {"/allow", "allow", "y", "yes"}:
                ui.resolve_permission(True)
            elif cmd in {"/deny", "deny", "n", "no"}:
                ui.resolve_permission(False)
            else:
                ui._print("| Awaiting permission decision. Use '/allow' or '/deny'.")
            continue

        cmd_lower = command.lower()
        if cmd_lower in {"/quit", "quit", "exit"}:
            break
        if cmd_lower in {"/allow", "allow", "y", "yes"}:
            ui._print("| Nothing to allow right now.")
            continue
        if cmd_lower in {"/deny", "deny", "n", "no"}:
            ui._print("| Nothing to deny right now.")
            continue
        if cmd_lower == "/cancel":
            if ui.prompt_in_progress():
                await conn.cancel(CancelNotification(sessionId=session_id))
                ui._print("| Sent cancel request.")
            else:
                ui._print("| No active prompt.")
            continue

        if ui.prompt_in_progress():
            ui._print("| Prompt already running. Use '/cancel' or wait for completion.")
            continue

        ui._print("| Sending prompt to agent...")
        task = asyncio.create_task(
            conn.prompt(PromptRequest(sessionId=session_id, prompt=[{"type": "text", "text": command}]))
        )
        ui._attach_prompt_task(task)


async def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python examples/client.py AGENT_PROGRAM [ARGS...]", file=sys.stderr)
        return 2

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        *argv[1:],
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    assert proc.stdin and proc.stdout

    client_impl = ExampleClient()
    conn = ClientSideConnection(lambda _agent: client_impl, proc.stdin, proc.stdout)

    await conn.initialize(InitializeRequest(protocolVersion=PROTOCOL_VERSION, clientCapabilities=None))
    session = await conn.newSession(NewSessionRequest(mcpServers=[], cwd=os.getcwd()))

    await interactive_loop(conn, session.sessionId, client_impl)

    try:
        proc.terminate()
    except ProcessLookupError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv)))
