<a href="https://agentclientprotocol.com/" >
  <img alt="Agent Client Protocol" src="https://zed.dev/img/acp/banner-dark.webp">
</a>

# Agent Client Protocol (Python)

Python SDK for the Agent Client Protocol (ACP). Build agents that speak ACP over stdio so tools like Zed can orchestrate them.

> Each release tracks the matching ACP schema version. Contributions that improve coverage or tooling are very welcome.

**Highlights**

- Generated `pydantic` models that track the upstream ACP schema (`acp.schema`)
- Async base classes and JSON-RPC plumbing that keep stdio agents tiny
- Process helpers such as `spawn_agent_process` for embedding agents and clients directly in Python
- Batteries-included examples that exercise streaming updates, file I/O, and permission flows
- Optional Gemini CLI bridge (`examples/gemini.py`) for the `gemini --experimental-acp` integration
- Experimental contrib modules (`acp.contrib`) that streamline session state, tool call tracking, and permission prompts

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
import sys
from pathlib import Path

from acp import spawn_agent_process, text_block
from acp.schema import InitializeRequest, NewSessionRequest, PromptRequest


async def main() -> None:
    agent_script = Path("examples/echo_agent.py")
    async with spawn_agent_process(lambda _agent: YourClient(), sys.executable, str(agent_script)) as (conn, _proc):
        await conn.initialize(InitializeRequest(protocolVersion=1))
        session = await conn.newSession(NewSessionRequest(cwd=str(agent_script.parent), mcpServers=[]))
        await conn.prompt(
            PromptRequest(
                sessionId=session.sessionId,
                prompt=[text_block("Hello!")],
            )
        )


asyncio.run(main())
```

`spawn_client_process` mirrors this pattern for the inverse direction.

### Minimal agent sketch

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
    session_notification,
    stdio_streams,
    text_block,
    update_agent_message,
)


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
                session_notification(
                    params.sessionId,
                    update_agent_message(text_block(text)),
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
- `examples/gemini.py`: connects to the Gemini CLI in `--experimental-acp` mode, with optional auto-approval and sandbox flags

## Helper APIs

Use `acp.helpers` to build protocol payloads without manually shaping dictionaries:

```python
from acp import (
    start_read_tool_call,
    text_block,
    tool_content,
    update_available_commands,
    update_tool_call,
)

start = start_read_tool_call("call-1", "Inspect config", path="config.toml")
commands = update_available_commands([])
update = update_tool_call("call-1", status="completed", content=[tool_content(text_block("Done."))])
```

Helpers cover content blocks (`text_block`, `resource_link_block`), embedded resources, tool calls (`start_edit_tool_call`, `update_tool_call`), and session updates (`update_agent_message_text`, `update_available_commands`, `update_current_mode`, `session_notification`).

## Contrib helpers

The experimental `acp.contrib` package captures patterns from reference integrations:

- `SessionAccumulator` (`acp.contrib.session_state`) merges `SessionNotification` streams into immutable snapshots for UI rendering.
- `ToolCallTracker` (`acp.contrib.tool_calls`) generates consistent tool call starts/updates and buffers streamed content.
- `PermissionBroker` (`acp.contrib.permissions`) wraps permission requests with sensible default option sets.

Read more in [docs/contrib.md](docs/contrib.md).

## Documentation

- Project docs (MkDocs): https://psiace.github.io/agent-client-protocol-python/
- Local sources: `docs/`
  - [Quickstart](docs/quickstart.md)
  - [Contrib helpers](docs/contrib.md)
  - [Releasing](docs/releasing.md)

## Gemini CLI bridge

Want to exercise the `gemini` CLI over ACP? The repository includes a Python replica of the Go SDK's REPL:

```bash
python examples/gemini.py --yolo  # auto-approve permissions
python examples/gemini.py --sandbox --model gemini-2.5-pro
```

Defaults assume the CLI is discoverable via `PATH`; override with `--gemini` or `ACP_GEMINI_BIN=/path/to/gemini`.

The smoke test (`tests/test_gemini_example.py`) is opt-in to avoid false negatives when the CLI is unavailable or lacks credentials. Enable it locally with:

```bash
ACP_ENABLE_GEMINI_TESTS=1 ACP_GEMINI_BIN=/path/to/gemini uv run python -m pytest tests/test_gemini_example.py
```

The test gracefully skips when authentication prompts (e.g. missing `GOOGLE_CLOUD_PROJECT`) block the interaction.

## Development workflow

```bash
make install                     # create uv virtualenv and install hooks
ACP_SCHEMA_VERSION=<ref> make gen-all  # refresh generated schema bindings
make check                       # lint, types, dependency analysis
make test                        # run pytest + doctests
```

After local changes, consider updating docs/examples if the public API surface shifts.
