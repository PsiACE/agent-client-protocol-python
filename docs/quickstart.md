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

## 2. Run the echo agent

Launch the ready-made echo example, which streams text blocks back over ACP:

```bash
python examples/echo_agent.py
```

Keep it running while you connect your client.

## 3. Connect from your client

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

You can also embed the agent inside another Python process without shelling out manually. Use
`acp.spawn_agent_process` to bootstrap the child and receive a `ClientSideConnection`:

```python
import asyncio
import sys
from pathlib import Path

from acp import spawn_agent_process
from acp.interfaces import Client
from acp.schema import (
    DeniedOutcome,
    InitializeRequest,
    NewSessionRequest,
    PromptRequest,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SessionNotification,
    TextContentBlock,
)


class SimpleClient(Client):
    async def requestPermission(self, params: RequestPermissionRequest) -> RequestPermissionResponse:
        return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))

    async def sessionUpdate(self, params: SessionNotification) -> None:  # noqa: D401 - logging only
        print("update:", params)

    # Optional client methods omitted for brevity


async def main() -> None:
    script = Path("examples/echo_agent.py").resolve()

    async with spawn_agent_process(lambda agent: SimpleClient(), sys.executable, str(script)) as (
        conn,
        _process,
    ):
        await conn.initialize(InitializeRequest(protocolVersion=1))
        session = await conn.newSession(NewSessionRequest(cwd=str(script.parent), mcpServers=[]))
        await conn.prompt(
            PromptRequest(
                sessionId=session.sessionId,
                prompt=[TextContentBlock(type="text", text="Hello from spawn!")],
            )
        )

asyncio.run(main())
```

Inside the context manager the subprocess is monitored, stdin/stdout are tied into ACP, and the
connection cleans itself up on exit.

## 4. Extend the agent

Create your own agent by subclassing `acp.Agent`. The pattern mirrors the echo example:

```python
from acp import Agent, PromptRequest, PromptResponse


class MyAgent(Agent):
    async def prompt(self, params: PromptRequest) -> PromptResponse:
        # inspect params.prompt, stream updates, then finish the turn
        return PromptResponse(stopReason="end_turn")
```

Hook it up with `AgentSideConnection` inside an async entrypoint and wire it to your client. Refer to [examples/echo_agent.py](https://github.com/psiace/agent-client-protocol-python/blob/main/examples/echo_agent.py) for the complete structure, including lifetime hooks (`initialize`, `newSession`) and streaming responses.
