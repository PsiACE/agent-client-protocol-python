# Repository Guidelines

## Project Structure & Module Organization
The package code lives under `src/acp`, exposing the high-level Agent, transport helpers, and generated protocol schema. Generated artifacts such as `schema/` and `src/acp/schema.py` are refreshed via `scripts/gen_all.py` against the upstream ACP schema. Integration examples are in `examples/`, including `echo_agent.py` and the mini SWE bridge. Tests reside in `tests/` with async fixtures and doctests; documentation sources live in `docs/` and publish via MkDocs. Built distributions drop into `dist/` after builds.

## Build, Test, and Development Commands
Run `make install` to create a `uv` managed virtualenv and install pre-commit hooks. `make check` executes lock verification, Ruff linting, `ty` static checks, and deptry analysis. `make test` calls `uv run python -m pytest --doctest-modules`. For release prep use `make build` or `make build-and-publish`. `make gen-all` regenerates protocol models; export `ACP_SCHEMA_VERSION=<ref>` beforehand to fetch a specific upstream schema (defaults to the cached copy). `make docs` serves MkDocs locally; `make docs-test` ensures clean builds.

## Coding Style & Naming Conventions
Target Python 3.10+ with type hints and 120-character lines enforced by Ruff (`pyproject.toml`). Prefer dataclasses/pydantic models from the schema modules rather than bare dicts. Tests may ignore security lint (see per-file ignores) but still follow snake_case names. Keep public API modules under `acp/*` lean; place utilities in internal `_`-prefixed modules when needed.

## Testing Guidelines
Pytest is the main framework with `pytest-asyncio` for coroutine tests and doctests activated on modules. Name test files `test_*.py` and co-locate fixtures under `tests/conftest.py`. Aim to cover new protocol surfaces with integration-style tests using the async agent stubs. Generate coverage reports via `tox -e py310` when assessing CI parity.

## Commit & Pull Request Guidelines
Commit history follows Conventional Commits (`feat:`, `fix:`, `docs:`). Scope commits narrowly and include context on affected protocol version or tooling. PRs should describe agent behaviors exercised, link related issues, and mention schema regeneration if applicable. Attach test output (`make check` or targeted pytest) and screenshots only when UI-adjacent docs change. Update docs/examples when altering the public agent API.

## Agent Integration Tips
Leverage `examples/mini_swe_agent/` as a template when bridging other command executors. Use `AgentSideConnection` with `stdio_streams()` for ACP-compliant clients; document any extra environment variables in README updates.
