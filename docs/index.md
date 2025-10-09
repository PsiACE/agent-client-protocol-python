# Agent Client Protocol SDK (Python)

Welcome to the Python SDK for the Agent Client Protocol (ACP). The package ships ready-to-use transports, typed protocol models, and examples that stream messages to ACP-aware clients such as Zed.

## What you get

- Fully typed dataclasses generated from the upstream ACP schema (`acp.schema`)
- Async agent base class and stdio helpers to spin up an agent in a few lines
- Examples that demonstrate streaming updates and tool execution over ACP

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

Prefer a guided tour? Head to the [Quickstart](quickstart.md) for step-by-step instructions, including how to run the agent from an editor or terminal.

## Documentation map

- [Quickstart](quickstart.md): install, run, and extend the echo agent
- [Mini SWE Agent guide](mini-swe-agent.md): bridge mini-swe-agent over ACP, including duet launcher and Textual client

Source code lives under `src/acp/`, while tests and additional examples are available in `tests/` and `examples/`. If you plan to contribute, see the repository README for the development workflow.
