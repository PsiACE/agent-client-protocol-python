# Mini SWE Agent (Python) — ACP Bridge

> Just a show of the bridge in action. Not a best-effort or absolutely-correct implementation of the agent.

A minimal Agent Client Protocol (ACP) bridge that wraps mini-swe-agent so it can be run by Zed as an external agent over stdio, and also provides a local Textual UI client.

## Configure in Zed (recommended for editor integration)

Add an `agent_servers` entry to Zed’s `settings.json`. Point `command` to the Python interpreter that has both `agent-client-protocol` and `mini-swe-agent` installed, and `args` to this example script:

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
        "MINI_SWE_MODEL_KWARGS": "{\"api_base\":\"https://openrouter.ai/api/v1\"}",
        "OPENROUTER_API_KEY": "sk-or-..."
      }
    }
  }
}
```

Notes
- If you install `agent-client-protocol` from PyPI, you do not need to set `PYTHONPATH`.
- Using OpenRouter:
  - Set `MINI_SWE_MODEL` to a model supported by OpenRouter (e.g. `openrouter/openai/gpt-4o-mini`, `openrouter/anthropic/claude-3.5-sonnet`).
  - Set `MINI_SWE_MODEL_KWARGS` to a JSON containing `api_base`: `{ "api_base": "https://openrouter.ai/api/v1" }`.
  - Set `OPENROUTER_API_KEY` to your API key.
- Alternatively, you can use native OpenAI/Anthropic APIs. Set `MINI_SWE_MODEL` accordingly and provide the vendor-specific API key; `MINI_SWE_MODEL_KWARGS` is optional.

## Run locally with a TUI (Textual)

Use the duet launcher to run both the ACP agent and the local Textual client connected over dedicated pipes. The client keeps your terminal stdio; ACP messages flow over separate FDs.

```bash
# From repo root
python examples/mini_swe_agent/duet.py
```

Environment
- The launcher loads `.env` from the repo root using python-dotenv (override=True) so both child processes inherit the same environment.
- Minimum for OpenRouter:
  - `MINI_SWE_MODEL="openrouter/openai/gpt-4o-mini"`
  - `OPENROUTER_API_KEY="sk-or-..."`
  - Optional: `MINI_SWE_MODEL_KWARGS='{"api_base":"https://openrouter.ai/api/v1"}'` (auto-injected if missing)

Quit behavior
- Quit from the TUI cleanly ends the background loop; duet will terminate both processes gracefully and force-kill after a short timeout if needed.

## Behavior overview

- User prompt handling
  - Text blocks are concatenated into a task and passed to mini-swe-agent.
- Streaming updates
  - The agent sends `session/update` with `agent_message_chunk` for incremental messages.
- Command execution visualization
  - Each bash execution is reported with a `tool_call` (start) and a `tool_call_update` (complete) including command and output (`returncode` in rawOutput).
- Final result
  - A final `agent_message_chunk` is sent at the end of the turn with the submitted output.

Use Zed’s “open acp logs” command to inspect ACP traffic if needed.
