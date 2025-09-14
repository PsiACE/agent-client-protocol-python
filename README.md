# Agent Client Protocol (Python)

A Python implementation of the Agent Client Protocol (ACP). Use it to build agents that communicate with ACP-capable clients (e.g. Zed) over stdio.

- Package name: `agent-client-protocol` (import as `acp`)
- Repository: https://github.com/psiace/agent-client-protocol-python
- Docs: https://psiace.github.io/agent-client-protocol-python/
- Featured: Listed as the first third-party SDK on the official ACP site — see https://agentclientprotocol.com/libraries/community

## Install

```bash
pip install agent-client-protocol
# or
uv add agent-client-protocol
```

## Development (contributors)

```bash
make install   # set up venv
make check     # lint + typecheck
make test      # run tests
```

## Minimal agent example

See a complete streaming echo example in [examples/echo_agent.py](examples/echo_agent.py). It streams back each text block using `session/update` and ends the turn.

```python
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
from acp.schema import ContentBlock1, SessionUpdate2


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
                    update=SessionUpdate2(
                        sessionUpdate="agent_message_chunk",
                        content=ContentBlock1(type="text", text=text),
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
```

Run this executable from your ACP-capable client (e.g. configure Zed to launch it). The library takes care of the stdio JSON-RPC transport.

## Example: Mini SWE Agent bridge

A minimal ACP bridge for mini-swe-agent is provided under [`examples/mini_swe_agent`](examples/mini_swe_agent/README.md). It demonstrates:

- Parsing a prompt from ACP content blocks
- Streaming agent output via `session/update`
- Mapping command execution to `tool_call` and `tool_call_update`

## Documentation

- Quickstart: [docs/quickstart.md](docs/quickstart.md)
- Mini SWE Agent example: [docs/mini-swe-agent.md](docs/mini-swe-agent.md)
