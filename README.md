<a href="https://agentclientprotocol.com/">
  <img alt="Agent Client Protocol" src="https://zed.dev/img/acp/banner-dark.webp">
</a>

# Agent Client Protocol (Python)

Build ACP-compliant agents and clients in Python with generated schema models, asyncio transports, helper builders, and runnable demos.

> Releases track the upstream ACP schema; contributions that tighten coverage or tooling are always welcome.

## Install

```bash
pip install agent-client-protocol
# or
uv add agent-client-protocol
```

## At a glance

- **Spec parity:** Generated Pydantic models in `acp.schema` track every ACP release so payloads stay valid.
- **Runtime ergonomics:** Async base classes, stdio JSON-RPC plumbing, and lifecycle helpers keep custom agents tiny.
- **Examples ready:** Streaming, permissions, Gemini bridge, and duet demos live under `examples/`.
- **Helper builders:** `acp.helpers` mirrors the Go/TS SDK APIs for content blocks, tool calls, and session updates.
- **Contrib utilities:** Session accumulators, tool call trackers, and permission brokers share patterns from real deployments.

## Who benefits

- Agent authors who need typed models, helper builders, and event-stream ergonomics for ACP-compatible assistants.
- Client integrators embedding ACP parties inside Python applications or wrapping existing CLIs via stdio.
- Tooling teams experimenting with permission flows, streaming UX, or Gemini bridges without re-implementing transports.
See real adopters like kimi-cli in the [Use Cases list](https://agentclientprotocol.github.io/python-sdk/use-cases/).

## How to get started

- Follow the [Quickstart guide](https://agentclientprotocol.github.io/python-sdk/quickstart/) for installation, echo-agent validation, editor wiring (e.g. Zed), and programmatic launch recipes.
- Browse the [example gallery](https://github.com/agentclientprotocol/python-sdk/tree/main/examples) to see progressively richer integrations you can copy or extend.
- Skim the [docs hub](https://agentclientprotocol.github.io/python-sdk/) for focused references on contrib helpers, releasing, and transport details.

## Quick links

| Need               | Link                                                                   |
|--------------------|------------------------------------------------------------------------|
| Docs hub           | <https://agentclientprotocol.github.io/python-sdk/>                    |
| Quickstart         | <https://agentclientprotocol.github.io/python-sdk/quickstart/>         |
| Use cases          | <https://agentclientprotocol.github.io/python-sdk/use-cases/>          |
| Contrib helpers    | <https://agentclientprotocol.github.io/python-sdk/contrib/>            |
| Releasing workflow | <https://agentclientprotocol.github.io/python-sdk/releasing/>          |
| Examples           | <https://github.com/agentclientprotocol/python-sdk/tree/main/examples> |
| Tests              | <https://github.com/agentclientprotocol/python-sdk/tree/main/tests>    |
| PyPI               | <https://pypi.org/project/agent-client-protocol/>                      |

## Project layout

- `src/acp/`: runtime package (agents, clients, transports, helpers, schema bindings, contrib utilities)
- `schema/`: upstream JSON schema sources (regenerate via `make gen-all`)
- `docs/`: MkDocs content backing the published documentation
- `examples/`: runnable scripts covering stdio orchestration patterns
- `tests/`: pytest suite with golden fixtures and optional Gemini coverage

## Developer commands

- `make install` provisions the `uv` virtualenv and installs pre-commit hooks.
- `make check` runs Ruff formatting/linting, type analysis, dependency hygiene, and lock verification.
- `make test` executes `pytest` (with doctests) inside the managed environment.
- `ACP_SCHEMA_VERSION=<ref> make gen-all` refreshes protocol artifacts when the schema advances.

Keep docs and examples current whenever you ship public API or transport changes, and prefer Conventional Commits (`feat:`, `fix:`, etc.) when submitting patches.

## Community & support

- File issues or feature requests at <https://github.com/agentclientprotocol/python-sdk>.
- Discuss ideas or get help via GitHub Discussions: <https://github.com/agentclientprotocol/python-sdk/discussions>.
- Join the broader ACP conversations at <https://agentclientprotocol.com/>, the Zed community channels, or the community Zulip: <https://agentclientprotocol.zulipchat.com/>.
- Shared learnings, integrations, or third-party transports are welcome additions to the documentation—open a PR!
