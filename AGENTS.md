# Repository Handbook

Use this page as the quick orientation for the Python SDK repo. It mirrors the tone of the main README/index and surfaces what you need without hunting through multiple docs.

## Repo Map

| Path | Why it exists |
| --- | --- |
| `src/acp/` | Runtime package: agent/client bases, transports, helpers, schema bindings, contrib utilities |
| `schema/` | Upstream JSON schema sources (regenerate with `make gen-all`) |
| `examples/` | Runnable scripts such as `echo_agent.py`, `client.py`, `gemini.py`, `duet.py` |
| `tests/` | Pytest suite, including optional Gemini smoke tests in `tests/test_gemini_example.py` |
| `docs/` | MkDocs content published at `agentclientprotocol.github.io/python-sdk/` |

## Daily Commands

| Need | Command |
| --- | --- |
| Bootstrap env + pre-commit | `make install` |
| Format, lint, types, deps | `make check` |
| Test suite (pytest + doctest) | `make test` |
| Regenerate schema + bindings | `ACP_SCHEMA_VERSION=<tag> make gen-all` |

## Style Guardrails

- Target Python 3.10+ and keep public APIs typed.
- Ruff handles formatting + linting (`uv run ruff format` / `check`)—keep both clean before pushing.
- Reach for the generated Pydantic models and helpers (e.g. `text_block`, `start_tool_call`) instead of hand-crafting dicts; helpers stay aligned with the schema via `tests/test_golden.py`.
- Place reusable internals in `_`-prefixed modules.

## Testing Expectations

- Tests live under `tests/` and follow the `test_*.py` naming. Mark async tests with `pytest.mark.asyncio`.
- Run `make test` (or `uv run python -m pytest`) before committing and include reproduction steps for new fixtures.
- Gemini CLI checks are opt-in: set `ACP_ENABLE_GEMINI_TESTS=1` and optionally `ACP_GEMINI_BIN=/path/to/gemini` to exercise `tests/test_gemini_example.py`.

## PR Checklist

- Use Conventional Commit prefixes (`feat:`, `fix:`, `docs:`, etc.) and call out schema regenerations explicitly.
- Summarise exercised behaviours, link related issues, and attach `make check` / targeted pytest output in PR descriptions.
- Update docs/examples when user-visible APIs or transports change, and document any new environment requirements.

## Agent Integration Tips

- Start new agents from `examples/echo_agent.py` or `examples/agent.py`; pair them with `examples/client.py` for loopback validation.
- `spawn_agent_process` / `spawn_client_process` embed ACP parties inside Python apps without hand-wiring stdio.
- Validate new transports against `tests/test_rpc.py` and (when relevant) the Gemini example to ensure streaming + permission flows stay compliant.
