from __future__ import annotations

import os
from collections.abc import Mapping
from contextlib import AbstractContextManager, ExitStack, nullcontext
from typing import Any, cast

try:
    from logfire import span as logfire_span  # type: ignore[unresolved-import]
except ModuleNotFoundError:  # pragma: no cover - logfire is optional
    logfire_span = None  # type: ignore[assignment]
else:  # pragma: no cover - optional
    os.environ.setdefault("LOGFIRE_IGNORE_NO_CONFIG", "1")

try:  # pragma: no cover - opentelemetry is optional
    from opentelemetry.trace import get_tracer as otel_get_tracer  # type: ignore[unresolved-import]
except ModuleNotFoundError:  # pragma: no cover - opentelemetry is optional
    otel_get_tracer = None  # type: ignore[assignment]

DEFAULT_TAGS = ["acp"]
TRACER = otel_get_tracer(__name__) if otel_get_tracer else None


def _start_tracer_span(name: str, *, attributes: Mapping[str, Any] | None = None) -> AbstractContextManager[Any]:
    if TRACER is None:
        return nullcontext()
    attrs = dict(attributes or {})
    return TRACER.start_as_current_span(name, attributes=attrs)


def span_context(name: str, *, attributes: Mapping[str, Any] | None = None) -> AbstractContextManager[None]:
    if logfire_span is None and TRACER is None:
        return nullcontext()
    stack = ExitStack()
    attrs: dict[str, Any] = {"logfire.tags": DEFAULT_TAGS}
    if attributes:
        attrs.update(attributes)
    if logfire_span is not None:
        stack.enter_context(logfire_span(name, attributes=attrs))
    stack.enter_context(_start_tracer_span(name, attributes=attributes))
    return cast(AbstractContextManager[None], stack)
