# Experimental Contrib Modules

> The helpers under `acp.contrib` capture patterns we observed in reference integrations such as Toad and kimi-cli. Every API here is experimental and may change without notice.

## SessionAccumulator

Module: `acp.contrib.session_state`

UI surfaces like Toad need a live, merged view of the latest tool calls, plan entries, and message stream. The core SDK only emits raw `SessionNotification` payloads, so applications usually end up writing their own state layer. `SessionAccumulator` offers that cache out of the box.

Capabilities:

- `SessionAccumulator.apply(notification)` merges `tool_call` and `tool_call_update` events, backfilling a missing start message when necessary.
- Each call to `snapshot()` returns an immutable `SessionSnapshot` (Pydantic model) containing the active plan, current mode ID, available commands, and historical user/agent/thought chunks.
- `subscribe(callback)` wires a lightweight observer that receives every new snapshot, making it easy to refresh UI widgets.
- Automatic reset when a different session ID arrives (configurable via `auto_reset_on_session_change`).

> Integration tip: create one accumulator per UI controller. Feed every `SessionNotification` through it, then render from `snapshot.tool_calls` or `snapshot.user_messages` instead of mutating state manually.

## ToolCallTracker & PermissionBroker

Modules: `acp.contrib.tool_calls` and `acp.contrib.permissions`

Agent-side runtimes (for example kimi-cli) are responsible for synthesising tool call IDs, streaming argument fragments, and formatting permission prompts. Managing bare Pydantic models quickly devolves into boilerplate; these helpers centralise the bookkeeping.

- `ToolCallTracker.start()/progress()/append_stream_text()` manages tool call state and emits canonical `ToolCallStart` / `ToolCallProgress` messages. The tracker also exposes `view()` (immutable `TrackedToolCallView`) and `tool_call_model()` for logging or permission prompts.
- `PermissionBroker.request_for()` wraps `requestPermission` RPCs. It reuses the tracker’s state (or an explicit `ToolCall`), applies optional extra content, and defaults to a standard Approve / Approve for session / Reject option set.
- `default_permission_options()` exposes that canonical option triple so applications can customise or extend it.

> Integration tip: keep a single tracker alongside your agent loop. Emit tool call notifications through it, and hand the tracker to `PermissionBroker` so permission prompts stay in sync with the latest call state.

## Design Guardrails

To stay aligned with the ACP schema, the contrib layer follows a few rules:

- Protocol types continue to live in `acp.schema`. Contrib code always copies them via `.model_copy(deep=True)` to avoid mutating shared instances.
- Helpers are opt-in; the core package never imports them implicitly and imposes no UI or agent framework assumptions.
- Implementations focus on the common pain points (tool call aggregation, permission requests) while leaving business-specific policy to the application.

Try the contrib modules in your agent or client, and open an issue/PR with feedback so we can decide which pieces should graduate into the stable surface.
