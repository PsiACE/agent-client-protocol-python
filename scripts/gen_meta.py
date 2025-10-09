#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schema"
VERSION_FILE = SCHEMA_DIR / "VERSION"


def main() -> None:
    generate_meta()


def generate_meta() -> None:
    meta_json = SCHEMA_DIR / "meta.json"
    out_py = ROOT / "src" / "acp" / "meta.py"
    if not meta_json.exists():
        raise SystemExit("schema/meta.json not found. Run gen_schema.py first.")  # noqa: TRY003

    data = json.loads(meta_json.read_text("utf-8"))
    agent_methods = data.get("agentMethods", {})
    client_methods = data.get("clientMethods", {})
    version = data.get("version", 1)
    header_lines = ["# Generated from schema/meta.json. Do not edit by hand."]
    if VERSION_FILE.exists():
        ref = VERSION_FILE.read_text("utf-8").strip()
        if ref:
            header_lines.append(f"# Schema ref: {ref}")

    out_py.write_text(
        "\n".join(header_lines)
        + "\n"
        + f"AGENT_METHODS = {agent_methods!r}\n"
        + f"CLIENT_METHODS = {client_methods!r}\n"
        + f"PROTOCOL_VERSION = {int(version)}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
