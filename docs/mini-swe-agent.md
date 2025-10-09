# Mini SWE Agent bridge

This example wraps mini-swe-agent behind ACP so editors such as Zed can interact with it over stdio. A duet launcher is included to run a local Textual client beside the bridge for quick experimentation.

## Overview

- Accepts ACP prompts, concatenates text blocks, and forwards them to mini-swe-agent
- Streams language-model output via `session/update` → `agent_message_chunk`
- Emits `tool_call` / `tool_call_update` pairs for shell execution, including stdout and return codes
- Sends a final `agent_message_chunk` when mini-swe-agent prints `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`

## Requirements

- Python environment with `mini-swe-agent` installed (`pip install mini-swe-agent`)
- ACP-capable client (e.g. Zed) or the bundled Textual client
- Optional: `.env` file at the repo root for shared configuration when using the duet launcher

If `mini-swe-agent` is missing, the bridge falls back to the reference copy at `reference/mini-swe-agent/src`.

## Configure models and credentials

Set environment variables before launching the bridge:

- `MINI_SWE_MODEL`: model identifier such as `openrouter/openai/gpt-4o-mini`
- `OPENROUTER_API_KEY` for OpenRouter models, or `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` for native providers
- Optional `MINI_SWE_MODEL_KWARGS`: JSON blob of extra keyword arguments (OpenRouter defaults are injected automatically when omitted)

The bridge selects the correct API key based on the chosen model and available variables.

## Run inside Zed

Add an Agent Server entry targeting `examples/mini_swe_agent/agent.py` and provide the environment variables there. Use Zed’s “Open ACP Logs” panel to observe streamed message chunks and tool call events in real time.

## Run locally with the duet launcher

To pair the bridge with the Textual TUI client, run:

```bash
python examples/mini_swe_agent/duet.py
```

Both processes inherit settings from `.env` (thanks to `python-dotenv`) and communicate over dedicated pipes.

**TUI shortcuts**
- `y`: YOLO
- `c`: Confirm
- `u`: Human (prompts for a shell command and streams it back as a tool call)
- `Enter`: Continue

## Related files

- Agent entrypoint: `examples/mini_swe_agent/agent.py`
- Duet launcher: `examples/mini_swe_agent/duet.py`
- Textual client: `examples/mini_swe_agent/client.py`
