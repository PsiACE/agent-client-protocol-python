# Agent Client Protocol SDK (Python)

Welcome to the Python SDK for the Agent Client Protocol (ACP). The package ships ready-to-use transports, typed protocol models, and examples that stream messages to ACP-aware clients such as Zed.

## What you get

- Pydantic models generated from the upstream ACP schema (`acp.schema`)
- Async agent/client wrappers with JSON-RPC task supervision built in
- Process helpers (`spawn_agent_process`, `spawn_client_process`) for embedding ACP nodes inside Python applications
- Examples that showcase streaming updates, file operations, and permission flows

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

## Documentation map

- [Quickstart](quickstart.md): install, run, and embed the echo agent, plus next steps for extending it

Source code lives under `src/acp/`, while tests and additional examples are available in `tests/` and `examples/`. If you plan to contribute, see the repository README for the development workflow.
