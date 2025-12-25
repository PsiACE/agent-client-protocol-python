#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schema"
SCHEMA_JSON = SCHEMA_DIR / "schema.json"
VERSION_FILE = SCHEMA_DIR / "VERSION"
SCHEMA_OUT = ROOT / "src" / "acp" / "schema.py"

BACKCOMPAT_MARKER = "# Backwards compatibility aliases"

# Pattern caches used when post-processing generated schema.
FIELD_DECLARATION_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\s*:")
DESCRIPTION_PATTERN = re.compile(
    r"description\s*=\s*(?P<prefix>[rRbBuU]*)?(?P<quote>'''|\"\"\"|'|\")(?P<value>.*?)(?P=quote)",
    re.DOTALL,
)

STDIO_TYPE_LITERAL = 'Literal["2#-datamodel-code-generator-#-object-#-special-#"]'
MODELS_TO_REMOVE = [
    "AgentClientProtocol",
    "AgentClientProtocol1",
    "AgentClientProtocol2",
    "AgentClientProtocol3",
    "AgentClientProtocol4",
    "AgentClientProtocol5",
    "AgentClientProtocol6",
]

# Map of numbered classes produced by datamodel-code-generator to descriptive names.
# Keep this in sync with the Rust/TypeScript SDK nomenclature.
RENAME_MAP: dict[str, str] = {
    "AgentResponse1": "AgentResponseMessage",
    "AgentResponse2": "AgentErrorMessage",
    "ClientResponse1": "ClientResponseMessage",
    "ClientResponse2": "ClientErrorMessage",
    "ContentBlock1": "TextContentBlock",
    "ContentBlock2": "ImageContentBlock",
    "ContentBlock3": "AudioContentBlock",
    "ContentBlock4": "ResourceContentBlock",
    "ContentBlock5": "EmbeddedResourceContentBlock",
    "McpServer1": "HttpMcpServer",
    "McpServer2": "SseMcpServer",
    "RequestPermissionOutcome1": "DeniedOutcome",
    "RequestPermissionOutcome2": "AllowedOutcome",
    "SessionConfigOption1": "SessionConfigOptionSelect",
    "SessionUpdate1": "UserMessageChunk",
    "SessionUpdate2": "AgentMessageChunk",
    "SessionUpdate3": "AgentThoughtChunk",
    "SessionUpdate4": "ToolCallStart",
    "SessionUpdate5": "ToolCallProgress",
    "SessionUpdate6": "AgentPlanUpdate",
    "SessionUpdate7": "AvailableCommandsUpdate",
    "SessionUpdate8": "CurrentModeUpdate",
    "SessionUpdate9": "ConfigOptionUpdate",
    "SessionUpdate10": "SessionInfoUpdate",
    "ToolCallContent1": "ContentToolCallContent",
    "ToolCallContent2": "FileEditToolCallContent",
    "ToolCallContent3": "TerminalToolCallContent",
}

ALIASES_MAP = {
    "StdioMcpServer": "McpServerStdio",
}

ENUM_LITERAL_MAP: dict[str, tuple[str, ...]] = {
    "PermissionOptionKind": (
        "allow_once",
        "allow_always",
        "reject_once",
        "reject_always",
    ),
    "PlanEntryPriority": ("high", "medium", "low"),
    "PlanEntryStatus": ("pending", "in_progress", "completed"),
    "StopReason": ("end_turn", "max_tokens", "max_turn_requests", "refusal", "cancelled"),
    "ToolCallStatus": ("pending", "in_progress", "completed", "failed"),
    "ToolKind": ("read", "edit", "delete", "move", "search", "execute", "think", "fetch", "switch_mode", "other"),
}

FIELD_TYPE_OVERRIDES: tuple[tuple[str, str, str, bool], ...] = (
    ("PermissionOption", "kind", "PermissionOptionKind", False),
    ("PlanEntry", "priority", "PlanEntryPriority", False),
    ("PlanEntry", "status", "PlanEntryStatus", False),
    ("PromptResponse", "stop_reason", "StopReason", False),
    ("ToolCall", "kind", "ToolKind", True),
    ("ToolCall", "status", "ToolCallStatus", True),
    ("ToolCallUpdate", "kind", "ToolKind", True),
    ("ToolCallUpdate", "status", "ToolCallStatus", True),
)

DEFAULT_VALUE_OVERRIDES: tuple[tuple[str, str, str], ...] = (
    ("AgentCapabilities", "mcp_capabilities", "McpCapabilities()"),
    ("AgentCapabilities", "session_capabilities", "SessionCapabilities()"),
    (
        "AgentCapabilities",
        "prompt_capabilities",
        "PromptCapabilities()",
    ),
    ("ClientCapabilities", "fs", "FileSystemCapability()"),
    ("ClientCapabilities", "terminal", "False"),
    (
        "InitializeRequest",
        "client_capabilities",
        "ClientCapabilities()",
    ),
    (
        "InitializeResponse",
        "agent_capabilities",
        "AgentCapabilities()",
    ),
)


@dataclass(frozen=True)
class _ProcessingStep:
    """A named transformation applied to the generated schema content."""

    name: str
    apply: Callable[[str], str]


def main() -> None:
    generate_schema()


def generate_schema() -> None:
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
        "--snake-case-field",
    ]

    subprocess.check_call(cmd)  # noqa: S603
    warnings = postprocess_generated_schema(SCHEMA_OUT)
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)


def postprocess_generated_schema(output_path: Path) -> list[str]:
    if not output_path.exists():
        raise RuntimeError(f"Generated schema not found at {output_path}")

    raw_content = output_path.read_text(encoding="utf-8")
    header_block = _build_header_block()

    content = _strip_existing_header(raw_content)
    content = _remove_backcompat_block(content)
    content = _remove_unused_models(content)
    content, leftover_classes = _rename_numbered_models(content)

    processing_steps: tuple[_ProcessingStep, ...] = (
        _ProcessingStep("apply field overrides", _apply_field_overrides),
        _ProcessingStep("apply default overrides", _apply_default_overrides),
        _ProcessingStep("attach description comments", _add_description_comments),
        _ProcessingStep("ensure custom BaseModel", _ensure_custom_base_model),
    )

    for step in processing_steps:
        content = step.apply(content)

    missing_targets = _find_missing_targets(content)

    content = _inject_enum_aliases(content)
    alias_block = _build_alias_block()
    final_content = header_block + content.rstrip() + "\n\n" + alias_block
    if not final_content.endswith("\n"):
        final_content += "\n"
    output_path.write_text(final_content, encoding="utf-8")

    warnings: list[str] = []
    if leftover_classes:
        warnings.append(
            "Unrenamed schema models detected: "
            + ", ".join(leftover_classes)
            + ". Update RENAME_MAP in scripts/gen_schema.py."
        )
    if missing_targets:
        warnings.append(
            "Renamed schema targets not found after generation: "
            + ", ".join(sorted(missing_targets))
            + ". Check RENAME_MAP or upstream schema changes."
        )
    warnings.extend(_validate_schema_alignment())

    return warnings


def _build_header_block() -> str:
    header_lines = ["# Generated from schema/schema.json. Do not edit by hand."]
    if VERSION_FILE.exists():
        ref = VERSION_FILE.read_text(encoding="utf-8").strip()
        if ref:
            header_lines.append(f"# Schema ref: {ref}")
    return "\n".join(header_lines) + "\n\n"


def _build_alias_block() -> str:
    alias_lines = [f"{old} = {new}" for old, new in sorted(RENAME_MAP.items())]
    alias_lines += [f"{old} = {new}" for old, new in sorted(ALIASES_MAP.items())]
    return BACKCOMPAT_MARKER + "\n" + "\n".join(alias_lines) + "\n"


def _strip_existing_header(content: str) -> str:
    existing_header = re.match(r"(#.*\n)+", content)
    if existing_header:
        return content[existing_header.end() :].lstrip("\n")
    return content.lstrip("\n")


def _remove_backcompat_block(content: str) -> str:
    marker_index = content.find(BACKCOMPAT_MARKER)
    if marker_index != -1:
        return content[:marker_index].rstrip()
    return content


def _rename_numbered_models(content: str) -> tuple[str, list[str]]:
    renamed = content
    for old, new in sorted(RENAME_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(new)}\b", renamed) is not None:
            renamed = re.sub(rf"\b{re.escape(new)}\b", f"_{new}", renamed)
        pattern = re.compile(rf"\b{re.escape(old)}\b")
        renamed = pattern.sub(new, renamed)

    leftover_class_pattern = re.compile(r"^class (\w+\d+)\(", re.MULTILINE)
    leftover_classes = sorted(set(leftover_class_pattern.findall(renamed)))
    return renamed, leftover_classes


def _find_missing_targets(content: str) -> list[str]:
    missing: list[str] = []
    for new_name in RENAME_MAP.values():
        pattern = re.compile(rf"^class {re.escape(new_name)}\(", re.MULTILINE)
        if not pattern.search(content):
            missing.append(new_name)
    return missing


def _validate_schema_alignment() -> list[str]:
    warnings: list[str] = []
    if not SCHEMA_JSON.exists():
        warnings.append("schema/schema.json missing; unable to validate enum aliases.")
        return warnings

    try:
        schema_enums = _load_schema_enum_literals()
    except json.JSONDecodeError as exc:
        warnings.append(f"Failed to parse schema/schema.json: {exc}")
        return warnings

    for enum_name, expected_values in ENUM_LITERAL_MAP.items():
        schema_values = schema_enums.get(enum_name)
        if schema_values is None:
            warnings.append(
                f"Enum '{enum_name}' not found in schema.json; update ENUM_LITERAL_MAP or investigate schema changes."
            )
            continue
        if tuple(schema_values) != expected_values:
            warnings.append(
                f"Enum mismatch for '{enum_name}': schema.json -> {schema_values}, generated aliases -> {expected_values}"
            )
    return warnings


def _load_schema_enum_literals() -> dict[str, tuple[str, ...]]:
    schema_data = json.loads(SCHEMA_JSON.read_text(encoding="utf-8"))
    defs = schema_data.get("$defs", {})
    enum_literals: dict[str, tuple[str, ...]] = {}

    for name, definition in defs.items():
        values: list[str] = []
        if "enum" in definition:
            values = [str(item) for item in definition["enum"]]
        elif "oneOf" in definition:
            values = [
                str(option["const"])
                for option in definition.get("oneOf", [])
                if isinstance(option, dict) and "const" in option
            ]
        if values:
            enum_literals[name] = tuple(values)

    return enum_literals


def _ensure_custom_base_model(content: str) -> str:
    if "class BaseModel(_BaseModel):" in content:
        return content
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        if not line.startswith("from pydantic import "):
            continue
        imports = [part.strip() for part in line[len("from pydantic import ") :].split(",")]
        has_alias = any(part == "BaseModel as _BaseModel" for part in imports)
        has_config = any(part == "ConfigDict" for part in imports)
        new_imports = []
        for part in imports:
            if part == "BaseModel":
                new_imports.append("BaseModel as _BaseModel")
                has_alias = True
            else:
                new_imports.append(part)
        if not has_alias:
            new_imports.append("BaseModel as _BaseModel")
        if not has_config:
            new_imports.append("ConfigDict")
        lines[idx] = "from pydantic import " + ", ".join(new_imports)
        to_insert = textwrap.dedent("""\
            class BaseModel(_BaseModel):
                model_config = ConfigDict(populate_by_name=True)

                def __getattr__(self, item: str) -> Any:
                    if item.lower() != item:
                        snake_cased = "".join("_" + c.lower() if c.isupper() and i > 0 else c.lower() for i, c in enumerate(item))
                        return getattr(self, snake_cased)
                    raise AttributeError(f"'{type(self).__name__}' object has no attribute '{item}'")
        """)
        insert_idx = idx + 1
        lines.insert(insert_idx, "")
        for offset, line in enumerate(to_insert.splitlines(), 1):
            lines.insert(insert_idx + offset, line)
        break
    return "\n".join(lines) + "\n"


def _apply_field_overrides(content: str) -> str:
    for class_name, field_name, new_type, optional in FIELD_TYPE_OVERRIDES:
        if optional:
            pattern = re.compile(
                rf"(class {class_name}\(BaseModel\):.*?\n\s+{field_name}:\s+Annotated\[\s*)Optional\[str],",
                re.DOTALL,
            )
            content, count = pattern.subn(rf"\1Optional[{new_type}],", content)
        else:
            pattern = re.compile(
                rf"(class {class_name}\(BaseModel\):.*?\n\s+{field_name}:\s+Annotated\[\s*)str,",
                re.DOTALL,
            )
            content, count = pattern.subn(rf"\1{new_type},", content)
        if count == 0:
            print(
                f"Warning: failed to apply type override for {class_name}.{field_name} -> {new_type}",
                file=sys.stderr,
            )
    return content


def _apply_default_overrides(content: str) -> str:
    for class_name, field_name, replacement in DEFAULT_VALUE_OVERRIDES:
        class_pattern = re.compile(
            rf"(class {class_name}\(BaseModel\):)(.*?)(?=\nclass |\Z)",
            re.DOTALL,
        )

        def replace_block(
            match: re.Match[str],
            _field_name: str = field_name,
            _replacement: str = replacement,
            _class_name: str = class_name,
        ) -> str:
            header, block = match.group(1), match.group(2)
            field_patterns: tuple[tuple[re.Pattern[str], Callable[[re.Match[str]], str]], ...] = (
                (
                    re.compile(
                        rf"(\n\s+{_field_name}:.*?\]\s*=\s*)([\s\S]*?)(?=\n\s{{4}}[A-Za-z_]|$)",
                        re.DOTALL,
                    ),
                    lambda m, _rep=_replacement: m.group(1) + _rep,
                ),
                (
                    re.compile(
                        rf"(\n\s+{_field_name}:[^\n]*=)\s*([^\n]+)",
                        re.MULTILINE,
                    ),
                    lambda m, _rep=_replacement: m.group(1) + " " + _rep,
                ),
            )
            for pattern, replacer in field_patterns:
                new_block, count = pattern.subn(replacer, block, count=1)
                if count:
                    return header + new_block
            print(
                f"Warning: failed to override default for {_class_name}.{_field_name}",
                file=sys.stderr,
            )
            return match.group(0)

        content, count = class_pattern.subn(replace_block, content, count=1)
        if count == 0:
            print(
                f"Warning: class {class_name} not found for default override on {field_name}",
                file=sys.stderr,
            )
    return content


def _add_description_comments(content: str) -> str:
    lines = content.splitlines()
    new_lines: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if indent == 4 and FIELD_DECLARATION_PATTERN.match(stripped or ""):
            block_lines, next_index = _collect_field_block(lines, index, indent)
            block_text = "\n".join(block_lines)
            description = _extract_description(block_text)

            if description:
                indent_str = " " * indent
                comment_lines = [
                    f"{indent_str}# {comment_line}" if comment_line else f"{indent_str}#"
                    for comment_line in description.splitlines()
                ]
                if comment_lines:
                    new_lines.extend(comment_lines)

            new_lines.extend(block_lines)
            index = next_index
            continue

        new_lines.append(line)
        index += 1

    return "\n".join(new_lines)


def _collect_field_block(lines: list[str], start: int, indent: int) -> tuple[list[str], int]:
    block: list[str] = []
    index = start

    while index < len(lines):
        current_line = lines[index]
        current_indent = len(current_line) - len(current_line.lstrip())
        if index != start and current_line.strip() and current_indent <= indent:
            break

        block.append(current_line)
        index += 1

    return block, index


def _extract_description(block_text: str) -> str | None:
    match = DESCRIPTION_PATTERN.search(block_text)
    if not match:
        return None

    prefix = match.group("prefix") or ""
    quote = match.group("quote")
    value = match.group("value")
    literal = f"{prefix}{quote}{value}{quote}"

    # datamodel-code-generator emits standard string literals, but fall back to raw text on parse errors.
    try:
        parsed = ast.literal_eval(literal)
    except (SyntaxError, ValueError):
        return value.replace("\\n", "\n")

    if isinstance(parsed, str):
        return parsed
    return str(parsed)


def _inject_enum_aliases(content: str) -> str:
    enum_lines = [
        f"{name} = Literal[{', '.join(repr(value) for value in values)}]" for name, values in ENUM_LITERAL_MAP.items()
    ]
    if not enum_lines:
        return content
    block = "\n".join(enum_lines) + "\n\n"
    class_index = content.find("\nclass ")
    if class_index == -1:
        return content
    insertion_point = class_index + 1  # include leading newline
    return content[:insertion_point] + block + content[insertion_point:]


def _remove_unused_models(content: str) -> str:
    for model_name in MODELS_TO_REMOVE:
        pattern = re.compile(
            rf"^(class {model_name}\([\s\S]*?\):)([\s\S]*?)(?=^\S|\Z)",
            re.MULTILINE,
        )
        content, count = pattern.subn("", content)
        if count > 0:
            print(f"Removed unused model: {model_name}", file=sys.stderr)
    return content


if __name__ == "__main__":
    main()
