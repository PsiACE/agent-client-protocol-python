from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PatchWarning:
    message: str


def apply_schema_patches(schema: dict[str, Any]) -> tuple[dict[str, Any], list[PatchWarning]]:
    patched = schema
    warnings: list[PatchWarning] = []

    patched, warning = _make_defs_field_optional(patched, "NewSessionRequest", "mcpServers")
    if warning is not None:
        warnings.append(warning)

    patched, warning = _make_defs_field_optional(patched, "LoadSessionRequest", "mcpServers")
    if warning is not None:
        warnings.append(warning)

    return patched, warnings


def _make_defs_field_optional(
    schema: dict[str, Any],
    model_name: str,
    field_name: str,
) -> tuple[dict[str, Any], PatchWarning | None]:
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return schema, PatchWarning("schema.$defs missing or invalid; cannot apply patches")

    model = defs.get(model_name)
    if not isinstance(model, dict):
        return schema, PatchWarning(f"schema.$defs.{model_name} missing or invalid; cannot patch {field_name}")

    required = model.get("required")
    if required is None:
        return schema, None
    if not isinstance(required, list):
        return schema, PatchWarning(f"schema.$defs.{model_name}.required invalid; cannot patch {field_name}")

    new_required = [item for item in required if item != field_name]
    if new_required == required:
        return schema, None

    model["required"] = new_required
    return schema, None
