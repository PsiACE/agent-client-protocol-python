# Agent Client Protocol (Python)

Python SDK for the Agent Client Protocol (ACP). Build agents that speak ACP over stdio so tools like Zed can orchestrate them.

> Each release tracks the matching ACP schema version. Contributions that improve coverage or tooling are very welcome.

**Highlights**

- Typed dataclasses generated from the upstream ACP schema (`acp.schema`)
- Async agent base class plus stdio transport helpers for quick bootstrapping
- Included examples that stream content updates and tool calls end-to-end

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

### Minimal agent sketch

```python
import asyncio

from acp import Agent, AgentSideConnection, PromptRequest, PromptResponse, SessionNotification, stdio_streams
from acp.schema import AgentMessageChunk, TextContentBlock


class EchoAgent(Agent):
    def __init__(self, conn):
        self._conn = conn

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        for block in params.prompt:
            text = getattr(block, "text", "")
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

- `examples/mini_swe_agent`: bridges mini-swe-agent into ACP, including a duet launcher and Textual TUI client
- Additional transport helpers are documented in the [Mini SWE guide](docs/mini-swe-agent.md)

## Documentation

- Project docs (MkDocs): https://psiace.github.io/agent-client-protocol-python/
- Local sources: `docs/`
  - [Quickstart](docs/quickstart.md)
  - [Mini SWE Agent bridge](docs/mini-swe-agent.md)

## Development workflow

```bash
make install                     # create uv virtualenv and install hooks
ACP_SCHEMA_VERSION=<ref> make gen-all  # refresh generated schema bindings
make check                       # lint, types, dependency analysis
make test                        # run pytest + doctests
```

After local changes, consider updating docs/examples if the public API surface shifts.
