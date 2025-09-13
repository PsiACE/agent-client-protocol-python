import asyncio
import os
import sys
from typing import Optional

from acp import (
    Client,
    PROTOCOL_VERSION,
    ClientSideConnection,
    InitializeRequest,
    NewSessionRequest,
    PromptRequest,
    SessionNotification,
)


class ExampleClient(Client):
    async def sessionUpdate(self, params: SessionNotification) -> None:
        update = params.update
        kind = getattr(update, "sessionUpdate", None) if not isinstance(update, dict) else update.get("sessionUpdate")
        if kind == "agent_message_chunk":
            # Handle both dict and model shapes
            content = update["content"] if isinstance(update, dict) else getattr(update, "content", None)
            text = content.get("text") if isinstance(content, dict) else getattr(content, "text", "<content>")
            print(f"| Agent: {text}")


async def interactive_loop(conn: ClientSideConnection, session_id: str) -> None:
    loop = asyncio.get_running_loop()
    while True:
        try:
            line = await loop.run_in_executor(None, lambda: input("> "))
        except EOFError:
            break
        if not line:
            continue
        try:
            await conn.prompt(PromptRequest(sessionId=session_id, prompt=[{"type": "text", "text": line}]))
        except Exception as e:  # noqa: BLE001
            print(f"error: {e}", file=sys.stderr)


async def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python examples/client.py AGENT_PROGRAM [ARGS...]", file=sys.stderr)
        return 2

    # Spawn agent subprocess
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        *argv[1:],
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    assert proc.stdin and proc.stdout

    # Connect to agent stdio
    conn = ClientSideConnection(lambda _agent: ExampleClient(), proc.stdin, proc.stdout)

    # Initialize and create session
    await conn.initialize(InitializeRequest(protocolVersion=PROTOCOL_VERSION, clientCapabilities=None))
    new_sess = await conn.newSession(NewSessionRequest(mcpServers=[], cwd=os.getcwd()))

    # Run REPL until EOF
    await interactive_loop(conn, new_sess.sessionId)

    try:
        proc.terminate()
    except ProcessLookupError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv)))
