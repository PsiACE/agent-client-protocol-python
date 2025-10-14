# Releasing

This project tracks the ACP schema tags published by
[`agentclientprotocol/agent-client-protocol`](https://github.com/agentclientprotocol/agent-client-protocol).
Every release should line up with one of those tags so that the generated `acp.schema` module, examples, and package
version remain consistent.

## Preparation

Pick the target schema tag (for example `v0.4.5`) and regenerate the protocol bindings:

```bash
ACP_SCHEMA_VERSION=v0.4.5 make gen-all
```

This downloads the upstream schema package and rewrites `schema/` plus the generated `src/acp/schema.py`.

Bump the project version in `pyproject.toml`, updating `uv.lock` if dependencies changed.

Run the standard checks:

```bash
make check
make test
```

- `make check` covers Ruff formatting/linting, static analysis, and dependency hygiene.
- `make test` executes pytest (including doctests).

Refresh documentation and examples (for instance the Gemini walkthrough) so they match the new schema behaviour.

## Commit & Merge

1. Make sure the diff only includes the expected artifacts: regenerated schema sources, `src/acp/schema.py`, version bumps, and doc updates.
2. Commit with a Conventional Commit message (for example `release: v0.4.5`) and note in the PR:
   - The ACP schema tag you targeted
   - Results from `make check` / `make test`
   - Any behavioural or API changes worth highlighting
3. Merge once the review is approved.

## Publish via GitHub Release

Publishing is automated through `on-release-main.yml`. After the release PR merges to `main`:

1. Draft a GitHub Release for the new tag (e.g. `v0.4.5`). If the tag is missing, the release UI will create it.
2. Once published, the workflow will:
   - Write the tag back into `pyproject.toml` to keep the package version aligned
   - Build and publish to PyPI via `uv publish` (using the `PYPI_TOKEN` secret)
   - Deploy updated documentation with `mkdocs gh-deploy`

No local `uv build`/`uv publish` runs are required—focus on providing a complete release summary (highlights, compatibility notes, etc.).

## Additional Notes

- Breaking schema updates often require refreshing golden fixtures (`tests/test_golden.py`), end-to-end cases such as `tests/test_rpc.py`, and any affected examples.
- Use `make clean` to remove generated artifacts if you need a fresh baseline before re-running `make gen-all`.
- Run optional checks like the Gemini smoke test (`ACP_ENABLE_GEMINI_TESTS=1`) whenever the environment is available to catch regressions before publishing.
