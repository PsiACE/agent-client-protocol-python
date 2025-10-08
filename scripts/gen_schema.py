#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schema"
SCHEMA_JSON = SCHEMA_DIR / "schema.json"
VERSION_FILE = SCHEMA_DIR / "VERSION"
SCHEMA_OUT = ROOT / "src" / "acp" / "schema.py"

BACKCOMPAT_MARKER = "# Backwards compatibility aliases"

# Map of numbered classes produced by datamodel-code-generator to descriptive names.
# Keep this in sync with the Rust/TypeScript SDK nomenclature.
RENAME_MAP: dict[str, str] = {
    "AvailableCommandInput1": "CommandInputHint",
    "ContentBlock1": "TextContentBlock",
    "ContentBlock2": "ImageContentBlock",
    "ContentBlock3": "AudioContentBlock",
    "ContentBlock4": "ResourceContentBlock",
    "ContentBlock5": "EmbeddedResourceContentBlock",
    "McpServer1": "HttpMcpServer",
    "McpServer2": "SseMcpServer",
    "McpServer3": "StdioMcpServer",
    "RequestPermissionOutcome1": "DeniedOutcome",
    "RequestPermissionOutcome2": "AllowedOutcome",
    "SessionUpdate1": "UserMessageChunk",
    "SessionUpdate2": "AgentMessageChunk",
    "SessionUpdate3": "AgentThoughtChunk",
    "SessionUpdate4": "ToolCallStart",
    "SessionUpdate5": "ToolCallProgress",
    "SessionUpdate6": "AgentPlanUpdate",
    "SessionUpdate7": "AvailableCommandsUpdate",
    "SessionUpdate8": "CurrentModeUpdate",
    "ToolCallContent1": "ContentToolCallContent",
    "ToolCallContent2": "FileEditToolCallContent",
    "ToolCallContent3": "TerminalToolCallContent",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate src/acp/schema.py from the ACP JSON schema.")
    parser.add_argument(
        "--format",
        dest="format_output",
        action="store_true",
        help="Format generated files with 'uv run ruff format'.",
    )
    parser.add_argument(
        "--no-format",
        dest="format_output",
        action="store_false",
        help="Disable formatting with ruff.",
    )
    parser.set_defaults(format_output=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_schema(format_output=args.format_output)


def generate_schema(*, format_output: bool = True) -> None:
    if not SCHEMA_JSON.exists():
        print(
            "Schema file missing. Ensure schema/schema.json exists (run gen_all.py --version to download).",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "datamodel_code_generator",
        "--input",
        str(SCHEMA_JSON),
        "--input-file-type",
        "jsonschema",
        "--output",
        str(SCHEMA_OUT),
        "--target-python-version",
        "3.12",
        "--collapse-root-models",
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--use-annotated",
    ]

    subprocess.check_call(cmd)  # noqa: S603
    warnings = rename_types(SCHEMA_OUT)
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    if format_output:
        format_with_ruff(SCHEMA_OUT)


def rename_types(output_path: Path) -> list[str]:
    if not output_path.exists():
        raise RuntimeError(f"Generated schema not found at {output_path}")  # noqa: TRY003

    content = output_path.read_text(encoding="utf-8")

    header_lines = ["# Generated from schema/schema.json. Do not edit by hand."]
    if VERSION_FILE.exists():
        ref = VERSION_FILE.read_text(encoding="utf-8").strip()
        if ref:
            header_lines.append(f"# Schema ref: {ref}")

    existing_header = re.match(r"(#.*\n)+", content)
    if existing_header:
        content = content[existing_header.end() :]
    content = content.lstrip("\n")

    marker_index = content.find(BACKCOMPAT_MARKER)
    if marker_index != -1:
        content = content[:marker_index].rstrip()

    for old, new in sorted(RENAME_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(rf"\b{re.escape(old)}\b")
        content = pattern.sub(new, content)

    leftover_class_pattern = re.compile(r"^class (\w+\d+)\(", re.MULTILINE)
    leftover_classes = sorted(set(leftover_class_pattern.findall(content)))

    header_block = "\n".join(header_lines) + "\n\n"
    alias_lines = [f"{old} = {new}" for old, new in sorted(RENAME_MAP.items())]
    alias_block = BACKCOMPAT_MARKER + "\n" + "\n".join(alias_lines) + "\n"

    content = header_block + content.rstrip() + "\n\n" + alias_block
    if not content.endswith("\n"):
        content += "\n"
    output_path.write_text(content, encoding="utf-8")

    warnings: list[str] = []
    if leftover_classes:
        warnings.append(
            "Unrenamed schema models detected: "
            + ", ".join(leftover_classes)
            + ". Update RENAME_MAP in scripts/gen_schema.py."
        )

    return warnings


def format_with_ruff(file_path: Path) -> None:
    uv_executable = shutil.which("uv")
    if uv_executable is None:
        print("Warning: 'uv' executable not found; skipping formatting.", file=sys.stderr)
        return
    try:
        subprocess.check_call([uv_executable, "run", "ruff", "format", str(file_path)])  # noqa: S603
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:  # pragma: no cover - best effort
        print(f"Warning: failed to format {file_path}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
