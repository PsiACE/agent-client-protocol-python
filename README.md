# Agent Client Protocol (Python)

Python SDK for the Agent Client Protocol (ACP). Build agents that speak ACP over stdio so tools like Zed can orchestrate them.

> Each release tracks the matching ACP schema version. Contributions that improve coverage or tooling are very welcome.

**Highlights**

- Generated `pydantic` models that track the upstream ACP schema (`acp.schema`)
- Async base classes and JSON-RPC plumbing that keep stdio agents tiny
- Process helpers such as `spawn_agent_process` for embedding agents and clients directly in Python
- Batteries-included examples that exercise streaming updates, file I/O, and permission flows

## Install

```bash
pip install agent-client-protocol
# or with uv
uv add agent-client-protocol
```

## Quickstart

1. Install the package and point your ACP-capable client at the provided echo agent:
   ```bash
   pip install agent-client-protocol
   python examples/echo_agent.py
   ```
2. Wire it into your client (e.g. Zed → Agents panel) so stdio is connected; the SDK handles JSON-RPC framing and lifecycle messages.

Prefer a step-by-step walkthrough? Read the [Quickstart guide](docs/quickstart.md) or the hosted docs: https://psiace.github.io/agent-client-protocol-python/.

### Launching from Python

Embed the agent inside another Python process without spawning your own pipes:

```python
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
```

Full example with streaming and lifecycle hooks lives in [examples/echo_agent.py](examples/echo_agent.py).

## Examples

- `examples/echo_agent.py`: the canonical streaming agent with lifecycle hooks
- `examples/client.py`: interactive console client that can launch any ACP agent via stdio
- `examples/agent.py`: richer agent showcasing initialization, authentication, and chunked updates
- `examples/duet.py`: launches both example agent and client using `spawn_agent_process`

## Documentation

- Project docs (MkDocs): https://psiace.github.io/agent-client-protocol-python/
- Local sources: `docs/`
  - [Quickstart](docs/quickstart.md)

## Development workflow

```bash
make install                     # create uv virtualenv and install hooks
ACP_SCHEMA_VERSION=<ref> make gen-all  # refresh generated schema bindings
make check                       # lint, types, dependency analysis
make test                        # run pytest + doctests
```

After local changes, consider updating docs/examples if the public API surface shifts.
