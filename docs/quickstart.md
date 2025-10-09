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

## Optional: Mini SWE Agent bridge

The repository also ships a bridge for [mini-swe-agent](https://github.com/groundx-ai/mini-swe-agent). To try it:

1. Install the dependency:
   ```bash
   pip install mini-swe-agent
   ```
2. Configure Zed to run `examples/mini_swe_agent/agent.py` and supply environment variables such as `MINI_SWE_MODEL` and `OPENROUTER_API_KEY`.
3. Review the [Mini SWE Agent guide](mini-swe-agent.md) for environment options, tool-call mapping, and a duet launcher that starts both the bridge and a Textual client (`python examples/mini_swe_agent/duet.py`).
