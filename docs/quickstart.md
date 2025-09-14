# Quickstart

Use the published package to build an ACP agent, or run the included example.

## Install the SDK

```bash
pip install agent-client-protocol
```

## Minimal agent

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

Run this program from your ACP-capable client.

## Run the Mini SWE Agent bridge in Zed

Install `mini-swe-agent` (or at least its core dependencies) into the same environment that will run the example:

```bash
pip install mini-swe-agent
```

Add an agent server to Zed’s `settings.json`:

```json
{
  "agent_servers": {
    "Mini SWE Agent (Python)": {
      "command": "/abs/path/to/python",
      "args": [
        "/abs/path/to/agent-client-protocol-python/examples/mini_swe_agent/agent.py"
      ],
      "env": {
        "MINI_SWE_MODEL": "openrouter/openai/gpt-4o-mini",
        "OPENROUTER_API_KEY": "sk-or-..."
      }
    }
  }
}
```

- For OpenRouter, `api_base` is set automatically to `https://openrouter.ai/api/v1` if not provided.
- Alternatively, use native providers by setting `MINI_SWE_MODEL` accordingly and providing `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.

In Zed, open the Agents panel and select "Mini SWE Agent (Python)".

See [mini-swe-agent.md](mini-swe-agent.md) for behavior and message mapping details.

## Run locally with a TUI

Use the duet launcher to run both the agent and the local Textual client over dedicated pipes:

```bash
python examples/mini_swe_agent/duet.py
```

The launcher loads `.env` from the repo root so both processes share the same configuration (requires python-dotenv).
