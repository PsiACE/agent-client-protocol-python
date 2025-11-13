<a href="https://agentclientprotocol.com/">
  <img alt="Agent Client Protocol" src="https://zed.dev/img/acp/banner-dark.webp">
</a>

# Agent Client Protocol SDK (Python)

The Python SDK packages generated schema bindings, asyncio transports, helper builders, and runnable demos so you can build ACP-compatible agents and clients without re-implementing JSON-RPC plumbing.

## ACP in practice

- ACP is the wire protocol that lets editors, CLIs, and other "clients" orchestrate AI agents via stdio.
- Each agent session exchanges structured messages (`session/update`, permission prompts, tool calls) defined in the ACP schema.
- This SDK mirrors the official schema version so Python integrations stay interoperable with the wider ACP ecosystem (Zed, Gemini CLI, etc.).

## SDK building blocks

- `acp.schema`: generated Pydantic models that validate every payload against the canonical ACP definition.
- `acp.agent` / `acp.client`: async base classes, JSON-RPC supervision, and lifecycle orchestration.
- `acp.helpers`: builders for content blocks, tool calls, permissions, and notifications that keep discriminator fields consistent.
- `acp.contrib`: experimental utilities (session accumulators, permission brokers, tool call trackers) derived from production deployments.
- `examples/`: ready-to-run agents, clients, duo processes, and the Gemini CLI bridge to test real workflows.

## Start building

1. Follow the [Quickstart](quickstart.md) to install the package, launch the echo agent, and connect from an editor or program.
2. Use the example scripts as scaffolding for your own integrations—swap in your business logic while keeping the ACP plumbing.
3. Extend transports, helpers, or contrib modules as needed; the test suite and golden fixtures keep schema compliance intact.

## Choose a path

- Curious who already runs this SDK? The [Use Cases](use-cases.md) page lists real integrations such as kimi-cli.
- Shipping an integration with advanced UX (streaming, permissions, resources)? Combine the helper builders with the contrib utilities for faster iteration.
- Embedding ACP parties inside an existing Python service? Reach for `spawn_agent_process` / `spawn_client_process` examples.

## Reference material

- [Quickstart](quickstart.md) — installation, editor wiring, and programmatic launch walkthroughs
- [Use Cases](use-cases.md) — real adopters with links to the resources they relied on
- [Experimental Contrib](contrib.md) — deep dives on the `acp.contrib` utilities
- [Releasing](releasing.md) — schema upgrade process, versioning policy, and publishing checklist

Need API-level details? Browse the source in `src/acp/`.

## Feedback & support

- Open issues or discussions on GitHub for bugs, feature requests, or integration help.
- Join the GitHub Discussions board at [github.com/agentclientprotocol/python-sdk/discussions](https://github.com/agentclientprotocol/python-sdk/discussions) to swap ideas.
- Share examples, tutorials, or transports by adding them to the `docs/` or `examples/` directories via pull request.
- Join the community chat at [agentclientprotocol.zulipchat.com](https://agentclientprotocol.zulipchat.com/) for real-time discussion.
- ACP roadmap updates live at [agentclientprotocol.com](https://agentclientprotocol.com/); follow along to keep this SDK in lockstep.
