# Contributing

Thanks for helping improve the Agent Client Protocol Python SDK! This guide mirrors the concise tone of the README/index so you can skim it quickly and get back to building.

## Ways to help

- **Report bugs** — file an issue with repro steps, OS + Python versions, and any environment toggles.
- **Improve docs/examples** — clarify workflows, add integration notes, or document a new transport.
- **Fix issues** — search for `bug` / `help wanted` labels or tackle anything that affects your integration.
- **Propose features** — describe the use case, API shape, and constraints so we can scope the work together.

## Filing great issues

When reporting a bug or requesting a feature, include:

- The ACP schema / SDK version you’re using.
- How to reproduce the behaviour (commands, inputs, expected vs. actual).
- Logs or payload snippets when available (scrub secrets).

## Local workflow

1. **Fork & clone** your GitHub fork: `git clone git@github.com:<you>/python-sdk.git`.
2. **Bootstrap tooling** inside the repo root: `make install`. This provisions `uv`, syncs deps, and installs pre-commit hooks.
3. **Create a topic branch:** `git checkout -b feat-my-improvement`.
4. **Develop + document:**
   - Keep code typed (Python 3.10+), prefer generated models/helpers over dicts.
   - Update docs/examples when user-facing behaviour shifts.
5. **Run the test gauntlet:**
   ```bash
   make check   # formatting, lint, type analysis, deps
   make test    # pytest + doctests
   ```
   Optional: `ACP_ENABLE_GEMINI_TESTS=1 make test` when you have the Gemini CLI available.
6. **(Optional) Cross-Python smoke:** `tox` if you want the same matrix CI runs.
7. **Commit + push:** `git commit -m "feat: add better tool call helper"` followed by `git push origin <branch>`.

## Pull request checklist

- [ ] PR title follows Conventional Commits.
- [ ] Tests cover the new behaviour (or the reason they’re not needed is documented).
- [ ] `make check` / `make test` output is attached or referenced.
- [ ] Docs and examples reflect user-visible changes.
- [ ] Any schema regeneration (`make gen-all`) is called out explicitly.

## Need help?

Open a discussion or ping us in the ACP Zulip if you’re stuck on design decisions, transport quirks, or schema questions. We’d rather collaborate early than rework later.
