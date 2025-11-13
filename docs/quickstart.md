# Quickstart

Spin up a working ACP agent/client loop in minutes. Keep this page beside the terminal and check off each section as you go. Want inspiration? Hop to the [Use Cases](use-cases.md) list to see how teams like kimi-cli or Zed apply the SDK in production.

## Quick checklist

| Goal | Command / Link |
| --- | --- |
| Install the SDK | `pip install agent-client-protocol` or `uv add agent-client-protocol` |
| Run the echo agent | `python examples/echo_agent.py` |
| Point Zed (or another client) at it | Update `settings.json` as shown below |
| Programmatically drive an agent | Copy the `spawn_agent_process` example |
| Run tests before hacking further | `make check && make test` |

## Before you begin

- Python 3.10–3.14 with `pip` or `uv`
- An ACP-capable client such as Zed (recommended for validation)
- Optional: the Gemini CLI (`gemini --experimental-acp`) for the bridge example

## Step 1 — Install the SDK

_Install the library from PyPI or add it to your uv workspace._

```bash
pip install agent-client-protocol
# or
uv add agent-client-protocol
```

## Step 2 — Launch the Echo agent

_Run the provided streaming agent so clients have something to talk to._

Start the ready-made echo example; it streams text blocks back to any ACP client. Leave it running in a terminal:

```bash
python examples/echo_agent.py
```

## Step 3 — Connect from an ACP-aware client

_Point a client at the script and confirm you can exchange streamed updates._

### Zed

Add an Agent Server entry in `settings.json` (Zed → Settings → Agents panel):

```json
{
  "agent_servers": {
    "Echo Agent (Python)": {
      "command": "/abs/path/to/python",
      "args": [
        "/abs/path/to/agentclientprotocol/python-sdk/examples/echo_agent.py"
      ]
    }
  }
}
```

Open the Agents panel and start the session. Each message you send should be echoed back via streamed `session/update` notifications.

### Other clients

Any ACP client that communicates over stdio can spawn the same script; no additional transport configuration is required.

### Programmatic launch

Prefer to drive agents directly from Python? The `spawn_agent_process` helper wires stdio and lifecycle management for you:

```python
import asyncio
import sys
from pathlib import Path

from acp import spawn_agent_process, text_block
from acp.interfaces import Client
from acp.schema import InitializeRequest, NewSessionRequest, PromptRequest, SessionNotification


class SimpleClient(Client):
    async def requestPermission(self, params):  # pragma: no cover - minimal stub
        return {"outcome": {"outcome": "cancelled"}}

    async def sessionUpdate(self, params: SessionNotification) -> None:
        print("update:", params.sessionId, params.update)


async def main() -> None:
    script = Path("examples/echo_agent.py")
    async with spawn_agent_process(lambda _agent: SimpleClient(), sys.executable, str(script)) as (conn, _proc):
        await conn.initialize(InitializeRequest(protocolVersion=1))
        session = await conn.newSession(NewSessionRequest(cwd=str(script.parent), mcpServers=[]))
        await conn.prompt(
            PromptRequest(
                sessionId=session.sessionId,
                prompt=[text_block("Hello from spawn!")],
            )
        )

asyncio.run(main())
```

`spawn_agent_process` manages the child process, wires its stdio into ACP framing, and closes everything when the block exits. The mirror helper `spawn_client_process` lets you drive an ACP client from Python as well.

## Step 4 — Extend the agent

_Swap the echo demo for your own `Agent` subclass._

Create your own agent by subclassing `acp.Agent`. The pattern mirrors the echo example:

```python
from acp import Agent, PromptRequest, PromptResponse


class MyAgent(Agent):
    async def prompt(self, params: PromptRequest) -> PromptResponse:
        # inspect params.prompt, stream updates, then finish the turn
        return PromptResponse(stopReason="end_turn")
```

Hook it up with `AgentSideConnection` inside an async entrypoint and wire it to your client. Refer to:

- [`examples/echo_agent.py`](https://github.com/agentclientprotocol/python-sdk/blob/main/examples/echo_agent.py) for the smallest streaming agent
- [`examples/agent.py`](https://github.com/agentclientprotocol/python-sdk/blob/main/examples/agent.py) for an implementation that negotiates capabilities and streams richer updates
- [`examples/duet.py`](https://github.com/agentclientprotocol/python-sdk/blob/main/examples/duet.py) to see `spawn_agent_process` in action alongside the interactive client
- [`examples/gemini.py`](https://github.com/agentclientprotocol/python-sdk/blob/main/examples/gemini.py) to drive the Gemini CLI (`--experimental-acp`) directly from Python

Need builders for common payloads? `acp.helpers` mirrors the Go/TS helper APIs:

```python
from acp import start_tool_call, update_tool_call, text_block, tool_content

start_update = start_tool_call("call-42", "Open file", kind="read", status="pending")
finish_update = update_tool_call(
    "call-42",
    status="completed",
    content=[tool_content(text_block("File opened."))],
)
```

Each helper wraps the generated Pydantic models in `acp.schema`, so the right discriminator fields (`type`, `sessionUpdate`, and friends) are always populated. That keeps examples readable while maintaining the same validation guarantees as constructing the models directly. Golden fixtures in `tests/test_golden.py` ensure the helpers stay in sync with future schema revisions.

## Optional — Talk to the Gemini CLI

_Have the Gemini CLI installed? Run the bridge to exercise permission flows._

If you have the Gemini CLI installed and authenticated:

```bash
python examples/gemini.py --yolo                # auto-approve permission prompts
python examples/gemini.py --sandbox --model gemini-1.5-pro
```

Environment helpers:

- `ACP_GEMINI_BIN` — override the CLI path (defaults to `PATH` lookup)
- `ACP_GEMINI_TEST_ARGS` — extra flags forwarded during the smoke test
- `ACP_ENABLE_GEMINI_TESTS=1` — opt-in toggle for `tests/test_gemini_example.py`

Authentication hiccups (e.g. missing `GOOGLE_CLOUD_PROJECT`) are surfaced but treated as skips during testing so the suite stays green on machines without credentials.

## Next steps

- Compare what you built with the real integrations listed on the [Use Cases](use-cases.md) page.
- Explore `docs/contrib.md` for higher-level utilities like session accumulators and permission brokers.
- Run `make check` / `make test` before committing changes, and regenerate schema artifacts with `make gen-all` when ACP versions advance.
- Need help? Start a thread in [GitHub Discussions](https://github.com/agentclientprotocol/python-sdk/discussions) or chat with other ACP developers at [agentclientprotocol.zulipchat.com](https://agentclientprotocol.zulipchat.com/).
