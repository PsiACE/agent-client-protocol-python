# Migrating to ACP Python SDK 0.7

ACP 0.7 reshapes the public surface so that Python-facing names, runtime helpers, and schema models line up with the evolving Agent Client Protocol schema. This guide covers the major changes in 0.7.0 and calls out the mechanical steps you need to apply in downstream agents, clients, and transports.

## 1. `acp.schema` models now expose `snake_case` fields

- Every generated model in `acp.schema` (see `src/acp/schema.py`) now uses Pythonic attribute names such as `session_id`, `stop_reason`, and `field_meta`. The JSON aliases (e.g., `alias="sessionId"`) stay intact so over-the-wire payloads remain camelCase.
- Instantiating a model or accessing response values must now use the `snake_case` form:

```python
# Before (0.6 and earlier)
PromptResponse(stopReason="end_turn")
params.sessionId

# After (0.7 and later)
PromptResponse(stop_reason="end_turn")
params.session_id
```

- If you relied on `model_dump()` to emit camelCase keys automatically, switch to `model_dump(by_alias=True)` (or use helpers such as `text_block`, `start_tool_call`, etc.) so responses continue to match the protocol.
- `field_meta` stays available for extension data. Any extra keys that were nested under `_meta` should now be provided via keyword arguments when constructing the schema models (see section 3).

## 2. `acp.run_agent` and `acp.connect_to_agent` replace manual connection wiring

`AgentSideConnection` and `ClientSideConnection` still exist internally, but the top-level entry points now prefer the helper functions implemented in `src/acp/core.py`.

### Updating agents

- Old pattern:

```python
conn = AgentSideConnection(lambda conn: Agent(), writer, reader)
await asyncio.Event().wait()  # keep running
```

- New pattern:

```python
await run_agent(MyAgent(), input_stream=writer, output_stream=reader)
```

- When your agent just runs over stdio, call `await run_agent(MyAgent())` and the helper will acquire asyncio streams via `stdio_streams()` for you.

### Updating clients and tests

- Old pattern:

```python
conn = ClientSideConnection(lambda conn: MyClient(), proc.stdin, proc.stdout)
```

- New pattern:

```python
conn = connect_to_agent(MyClient(), proc.stdin, proc.stdout)
```

- `spawn_agent_process` / `spawn_client_process` now accept concrete `Agent`/`Client` instances instead of factories that received the connection. Instantiate your implementation first and pass it in.
- Importing the legacy connection classes via `acp.AgentSideConnection` / `acp.ClientSideConnection` issues a `DeprecationWarning` (see `src/acp/__init__.py:82-96`). Update your imports to `run_agent` and `connect_to_agent` to silence the warning.

## 3. `Agent` and `Client` interface methods take explicit parameters

Both interfaces in `src/acp/interfaces.py` now look like idiomatic Python protocols: methods use `snake_case` names and receive the individual schema fields rather than a single request model.

### What changed

- Method names follow `snake_case` (`request_permission`, `session_update`, `new_session`, `set_session_model`, etc.).
- Parameters represent the schema fields, so there is no need to unpack `params` manually.
- Each method is decorated with `@param_model(...)`. Combined with the `compatible_class` helper (see `src/acp/utils.py`), this keeps the camelCase wrappers alive for callers that still pass a full Pydantic request object—but those wrappers now emit `DeprecationWarning`s to encourage migration.

### How to update your implementations

1. Rename your method overrides to their `snake_case` equivalents.
2. Replace `params: Model` arguments with the concrete fields plus `**kwargs` to collect future `_meta` keys.
3. Access schema data directly via those parameters.

Example migration for an agent:

```python
# Before
class EchoAgent:
    async def prompt(self, params: PromptRequest) -> PromptResponse:
        text = params.prompt[0].text
        return PromptResponse(stopReason="end_turn")

# After
class EchoAgent:
    async def prompt(self, prompt, session_id, **kwargs) -> PromptResponse:
        text = prompt[0].text
        return PromptResponse(stop_reason="end_turn")
```

Similarly, a client method such as `requestPermission` becomes:

```python
class RecordingClient(Client):
    async def request_permission(self, options, session_id, tool_call, **kwargs):
        ...
```

### Additional notes

- The connection layers automatically assemble the right request/response models using the `param_model` metadata, so callers do not need to build Pydantic objects manually anymore.
- For extension points (`field_meta`), pass keyword arguments from the connection into your handler signature: they arrive inside `**kwargs`.

### Backward compatibility

- The change should be 100% backward compatible as long as you update your method names and signatures. The `compatible_class` wrapper ensures that existing callers passing full request models continue to work. The old style API will remain functional before the next major release(1.0).
- Because camelCase wrappers remain for now, you can migrate file-by-file while still running against ACP 0.7. Just watch for the new deprecation warnings in your logs/tests.
