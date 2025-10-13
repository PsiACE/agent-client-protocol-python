<a href="https://agentclientprotocol.com/" >
  <img alt="Agent Client Protocol" src="https://zed.dev/img/acp/banner-dark.webp">
</a>

# Agent Client Protocol SDK (Python)

Welcome to the Python SDK for the Agent Client Protocol (ACP). The package ships ready-to-use transports, typed protocol models, and examples that stream messages to ACP-aware clients such as Zed.

## What you get

- Pydantic models generated from the upstream ACP schema (`acp.schema`)
- Async agent/client wrappers with JSON-RPC task supervision built in
- Process helpers (`spawn_agent_process`, `spawn_client_process`) for embedding ACP nodes inside Python applications
- Helper APIs in `acp.helpers` that mirror the Go/TS SDK builders for content blocks, tool calls, and session updates. They instantiate the generated Pydantic types for you, so call sites stay concise without sacrificing validation.
- Examples that showcase streaming updates, file operations, permission flows, and even a Gemini CLI bridge (`examples/gemini.py`)

## Getting started

1. Install the package:
   ```bash
   pip install agent-client-protocol
   ```
2. Launch the provided echo agent to verify your setup:
   ```bash
   python examples/echo_agent.py
   ```
3. Point your ACP-capable client at the running process (for Zed, configure an Agent Server entry). The SDK takes care of JSON-RPC framing and lifecycle transitions.

Prefer a guided tour? Head to the [Quickstart](quickstart.md) for terminal, editor, and programmatic launch walkthroughs.

## Gemini CLI bridge

If you have access to the Gemini CLI (`gemini --experimental-acp`), run:

```bash
python examples/gemini.py --yolo
```

Flags mirror the Go SDK example:

- `--gemini /path/to/cli` or `ACP_GEMINI_BIN` to override discovery
- `--model`, `--sandbox`, `--debug` forwarded verbatim
- `--yolo` auto-approves permission prompts with sensible defaults

An opt-in smoke test lives at `tests/test_gemini_example.py`. Enable it with `ACP_ENABLE_GEMINI_TESTS=1` (and optionally `ACP_GEMINI_TEST_ARGS`) when the CLI is authenticated; otherwise the test stays skipped.

## Documentation map

- [Quickstart](quickstart.md): install, run, and embed the echo agent, plus next steps for extending it
- [Releasing](releasing.md): schema upgrade workflow, version bumps, and publishing checklist

Source code lives under `src/acp/`, while tests and additional examples are available in `tests/` and `examples/`. If you plan to contribute, see the repository README for the development workflow.
