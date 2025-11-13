# Experimental Contrib Modules

The helpers under `acp.contrib` package recurring patterns we saw in integrations such as Toad, kimi-cli, and Gemini. Keep in mind they are experimental—APIs can still shift as we learn. Use this page as a menu:

- **`session_state.SessionAccumulator`** — build a canonical, immutable snapshot of every session update so UIs can render tool calls and plans without re-implementing state machines.
- **`tool_calls.ToolCallTracker` + `permissions.PermissionBroker`** — coordinate streamed tool call updates and permission prompts from one place.

## SessionAccumulator (`acp.contrib.session_state`)

**Use it when:** you need a live, merged view of `SessionNotification` events (e.g. tool calls, plan entries, user/agent messages) to drive UI widgets.

**Key capabilities**

- `SessionAccumulator.apply(notification)` reconciles `tool_call` and `tool_call_update` payloads, even if the start event arrives late.
- `snapshot()` returns an immutable `SessionSnapshot` Pydantic model containing the plan, current mode, commands, and ordered message history.
- `subscribe(callback)` lets you push snapshots into stores or UI components whenever state changes.
- Automatic reset on session-change (toggle with `auto_reset_on_session_change`).

> Tip: Create one accumulator per UI controller. Feed every raw `SessionNotification` into it and render from `snapshot.tool_calls` / `snapshot.user_messages` instead of mutating state manually.

## ToolCallTracker & PermissionBroker (`acp.contrib.tool_calls`, `acp.contrib.permissions`)

**Use them when:** your agent runtime synthesises tool call IDs, streams arguments, and prompts the user for approval. The helpers centralise the bookkeeping so you don’t juggle raw Pydantic models.

- `ToolCallTracker.start()/progress()/append_stream_text()` emits canonical `ToolCallStart` / `ToolCallProgress` updates and keeps an in-memory view via `view()` or `tool_call_model()`.
- `PermissionBroker.request_for()` wraps `requestPermission` RPCs. It reuses tracker state (or a provided `ToolCall`), lets you append extra content, and defaults to Approve / Approve for session / Reject options.
- `default_permission_options()` exposes that canonical option triple if you need to customise it.

> Tip: Keep one tracker near the agent event loop. Emit notifications through it and share the tracker with `PermissionBroker` so permission prompts always match the latest tool call state.

## Design Guardrails

To stay aligned with the ACP schema, the contrib layer follows a few rules:

- Schema data classes continue to live in `acp.schema`. Contrib helpers clone them with `.model_copy(deep=True)` before mutation.
- The core runtime never imports contrib modules implicitly—you opt in when they help.
- Helpers focus on painful bookkeeping (tool call aggregation, permission UX) and leave product-specific policy to your application.

Try the contrib modules, then open an issue or PR with feedback so we know which APIs should graduate into the stable surface.
