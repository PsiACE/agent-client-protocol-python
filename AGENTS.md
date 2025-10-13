# Repository Guidelines

## Project Structure & Module Organization
- `src/acp/`: runtime package exposing agent/client abstractions, transports, and the generated `schema.py`.
- `schema/`: upstream JSON schema sources; regenerate Python bindings with `make gen-all`.
- `examples/`: runnable scripts (`echo_agent.py`, `client.py`, `gemini.py`, etc.) demonstrating stdio orchestration patterns.
- `tests/`: pytest suite, including opt-in Gemini smoke checks under `tests/test_gemini_example.py`.
- `docs/`: MkDocs content powering the hosted documentation.

## Build, Test, and Development Commands
- `make install` — provision the `uv` virtualenv and install pre-commit hooks.
- `make check` — run Ruff linting/formatting, type analysis, dependency hygiene, and lock verification.
- `make test` — execute `pytest` (with doctests) inside the managed environment.
- `make gen-all` — refresh protocol artifacts when the ACP schema version advances (`ACP_SCHEMA_VERSION=<ref>` to pin an upstream tag).

## Coding Style & Naming Conventions
- Target Python 3.10+ with four-space indentation and type hints on public APIs.
- Ruff enforces formatting and lint rules (`uv run ruff check`, `uv run ruff format`); keep both clean before publishing.
- Prefer dataclasses or generated Pydantic models from `acp.schema` over ad-hoc dicts. Place shared utilities in `_`-prefixed internal modules.
- Prefer the builders in `acp.helpers` (for example `text_block`, `start_tool_call`) when constructing ACP payloads. The helpers instantiate the generated Pydantic models for you, keep literal discriminator fields out of call sites, and stay in lockstep with the schema thanks to the golden tests (`tests/test_golden.py`).

## Testing Guidelines
- Tests live in `tests/` and must be named `test_*.py`. Use `pytest.mark.asyncio` for coroutine coverage.
- Run `make test` (or `uv run python -m pytest`) prior to commits; include reproducing steps for any added fixtures.
- Gemini CLI coverage is disabled by default. Set `ACP_ENABLE_GEMINI_TESTS=1` (and `ACP_GEMINI_BIN=/path/to/gemini`) to exercise `tests/test_gemini_example.py`.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`, etc.) with succinct scopes, noting schema regenerations when applicable.
- PRs should describe exercised agent behaviours, link relevant issues, and include output from `make check` or focused pytest runs.
- Update documentation and examples whenever public APIs or transport behaviours change, and call out environment prerequisites for new integrations.

## Agent Integration Tips
- Bootstrap agents from `examples/echo_agent.py` or `examples/agent.py`; pair with `examples/client.py` for round-trip validation.
- Use `spawn_agent_process` / `spawn_client_process` to embed ACP parties directly in Python applications.
- Validate new transports against `tests/test_rpc.py` and, when applicable, the Gemini example to ensure streaming updates and permission flows stay compliant.
