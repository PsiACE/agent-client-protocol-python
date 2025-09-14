# Mini SWE Agent bridge

This example wraps mini-swe-agent behind ACP so Zed can run it as an external agent over stdio. It also includes a local Textual UI client connected via a duet launcher.

## Behavior

- Prompts: text blocks are concatenated into a single task string; referenced resources (`resource_link` / `resource`) are surfaced as hints in the task.
- Streaming: incremental text is sent via `session/update` with `agent_message_chunk`.
- Tool calls: when the agent executes a shell command, the bridge sends:
  - `tool_call` with `kind=execute`, pending status, and a bash code block containing the command
  - `tool_call_update` upon completion, including output and a `rawOutput` object with `output` and `returncode`
- Final result: on task submission (mini-swe-agent prints `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` as the first line), a final `agent_message_chunk` with the submission content is sent.

Non-terminating events (e.g. user rejection or timeouts) are surfaced both as a `tool_call_update` with `status=cancelled|failed` and as a text chunk so the session can continue.

## Configuration

Environment variables control the model:

- `MINI_SWE_MODEL`: model ID (e.g. `openrouter/openai/gpt-4o-mini`)
- `OPENROUTER_API_KEY` for OpenRouter; or `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` for native providers
- Optional `MINI_SWE_MODEL_KWARGS`: JSON, e.g. `{ "api_base": "https://openrouter.ai/api/v1" }` (auto-injected for OpenRouter if missing)

Agent behavior automatically maps the appropriate API key based on the chosen model and available environment variables.

If `mini-swe-agent` is not installed in the venv, the bridge attempts to import a vendored reference copy under `reference/mini-swe-agent/src`.

## How to run

- In Zed (editor integration): configure an agent server to launch `examples/mini_swe_agent/agent.py` and set the environment variables there.
- In terminal (local TUI): run the duet launcher to start both the agent and the Textual client with the same environment and dedicated pipes:

```bash
python examples/mini_swe_agent/duet.py
```

The launcher loads `.env` from the repo root (using python-dotenv) so both processes share the same configuration.

## Files

- Agent entry: [`examples/mini_swe_agent/agent.py`](https://github.com/psiace/agent-client-protocol-python/blob/main/examples/mini_swe_agent/agent.py)
- Duet launcher: [`examples/mini_swe_agent/duet.py`](https://github.com/psiace/agent-client-protocol-python/blob/main/examples/mini_swe_agent/duet.py)
- Textual client: [`examples/mini_swe_agent/client.py`](https://github.com/psiace/agent-client-protocol-python/blob/main/examples/mini_swe_agent/client.py)
