# Quickstart

This guide gets you from a clean environment to streaming ACP messages from a Python agent.

## Prerequisites

- Python 3.10+ and either `pip` or `uv`
- An ACP-capable client such as Zed (optional but recommended for testing)

## 1. Install the SDK

```bash
pip install agent-client-protocol
# or
uv add agent-client-protocol
```

## 2. Launch the Echo agent (terminal)

Start the ready-made echo example — it streams text blocks back to any ACP client:

```bash
python examples/echo_agent.py
```

Leave this process running while you connect from an editor or another program.

## 3. Connect from an editor

### Zed

Add an Agent Server entry in `settings.json` (Zed → Settings → Agents panel):

```json
{
  "agent_servers": {
    "Echo Agent (Python)": {
      "command": "/abs/path/to/python",
      "args": [
        "/abs/path/to/agent-client-protocol-python/examples/echo_agent.py"
      ]
    }
  }
}
```

Open the Agents panel and start the session. Each message you send should be echoed back via streamed `session/update` notifications.

### Other clients

Any ACP client that communicates over stdio can spawn the same script; no additional transport configuration is required.

### Programmatic launch

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

## 4. Extend the agent

Create your own agent by subclassing `acp.Agent`. The pattern mirrors the echo example:

```python
from acp import Agent, PromptRequest, PromptResponse


class MyAgent(Agent):
    async def prompt(self, params: PromptRequest) -> PromptResponse:
        # inspect params.prompt, stream updates, then finish the turn
        return PromptResponse(stopReason="end_turn")
```

Hook it up with `AgentSideConnection` inside an async entrypoint and wire it to your client. Refer to:

- [`examples/echo_agent.py`](https://github.com/psiace/agent-client-protocol-python/blob/main/examples/echo_agent.py) for the smallest streaming agent
- [`examples/agent.py`](https://github.com/psiace/agent-client-protocol-python/blob/main/examples/agent.py) for an implementation that negotiates capabilities and streams richer updates
- [`examples/duet.py`](https://github.com/psiace/agent-client-protocol-python/blob/main/examples/duet.py) to see `spawn_agent_process` in action alongside the interactive client
- [`examples/gemini.py`](https://github.com/psiace/agent-client-protocol-python/blob/main/examples/gemini.py) to drive the Gemini CLI (`--experimental-acp`) directly from Python

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

## 5. Optional: Talk to the Gemini CLI

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
