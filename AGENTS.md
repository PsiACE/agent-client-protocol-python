# Repository Guidelines

## Project Structure & Module Organization
The runtime package lives in `src/acp`, exposing the top-level agent entrypoints, transport adapters, and the generated `schema.py`. Regenerate protocol artifacts via `scripts/gen_all.py`, which refreshes both `schema/` and `src/acp/schema.py`. Examples demonstrating stdio bridges and quick-start flows are under `examples/`, while async-focused tests and fixtures sit in `tests/`. Documentation sources for MkDocs reside in `docs/`, and built artifacts land in `dist/` after release builds.

## Build, Test, and Development Commands
- `make install`: Provisions a `uv`-managed virtualenv and installs pre-commit hooks.
- `make check`: Runs lock verification, Ruff linting, `ty` type analysis, and deptry dependency checks.
- `make test`: Executes `uv run python -m pytest --doctest-modules` across the suite.
- `make gen-all`: Regenerates protocol schemas (set `ACP_SCHEMA_VERSION=<ref>` to target a specific upstream tag).
- `make build` / `make build-and-publish`: Produce or ship distribution artifacts.
- `make docs` and `make docs-test`: Serve or validate MkDocs documentation locally.

## Coding Style & Naming Conventions
Target Python 3.10+ with 4-space indentation and type hints on public APIs. Ruff (configured via `pyproject.toml`) enforces formatting, 120-character lines, and linting; keep `ruff --fix` output clean before opening a PR. Prefer dataclasses and Pydantic models generated in `acp.schema` over ad-hoc dicts. Place shared utilities in `_`-prefixed internal modules and keep public surfaces lean.

## Testing Guidelines
Pytest with `pytest-asyncio` powers the suite, and doctests are enabled for modules. Name test files `test_*.py`, keep fixtures in `tests/conftest.py`, and run `make test` before pushing. For deeper coverage investigation, run `tox -e py310` and review the HTML report in `.tox/py310/tmp/coverage`.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat:`, `fix:`, `docs:`) with narrow scopes and mention schema regeneration when applicable. PRs should describe exercised agent behaviors, link related issues, and attach `make check` (or targeted pytest) output. Update docs and examples whenever public agent APIs change, and include environment notes for new agent integrations.

## Agent Integration Tips
Use `examples/echo_agent.py` as the minimal agent template, or look at `examples/client.py` and `examples/duet.py` for spawning patterns that rely on `spawn_agent_process`/`spawn_client_process`. Document any environment requirements in `README.md`, and verify round-trip messaging with the echo agent before extending transports.
