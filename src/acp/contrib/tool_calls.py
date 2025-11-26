from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from typing import Any, cast

from pydantic import BaseModel, ConfigDict

from ..helpers import text_block, tool_content
from ..schema import (
    ToolCallLocation,
    ToolCallProgress,
    ToolCallStart,
    ToolCallStatus,
    ToolCallUpdate,
    ToolKind,
)


class _MissingToolCallTitleError(ValueError):
    """Raised when emitting a tool call start without a configured title."""

    def __init__(self) -> None:
        super().__init__("title must be set before sending a ToolCallStart")


class _UnknownToolCallError(KeyError):
    """Raised when retrieving a tool call that is not tracked."""

    def __init__(self, external_id: str) -> None:
        self.external_id = external_id
        super().__init__(external_id)

    def __str__(self) -> str:
        return f"Unknown tool call id: {self.external_id}"


def _copy_model_list(items: Sequence[Any] | None) -> list[Any] | None:
    if items is None:
        return None
    return [item.model_copy(deep=True) for item in items]


class _Unset:
    """Sentinel for optional parameters."""


UNSET = _Unset()


class TrackedToolCallView(BaseModel):
    """Immutable representation of a tracked tool call."""

    model_config = ConfigDict(frozen=True)

    tool_call_id: str
    title: str | None
    kind: ToolKind | None
    status: ToolCallStatus | None
    content: tuple[Any, ...] | None
    locations: tuple[ToolCallLocation, ...] | None
    raw_input: Any
    raw_output: Any


class _TrackedToolCall:
    def __init__(
        self,
        *,
        tool_call_id: str,
        title: str | None = None,
        kind: ToolKind | None = None,
        status: ToolCallStatus | None = None,
        content: Sequence[Any] | None = None,
        locations: Sequence[ToolCallLocation] | None = None,
        raw_input: Any = None,
        raw_output: Any = None,
    ) -> None:
        self.tool_call_id = tool_call_id
        self.title = title
        self.kind = kind
        self.status = status
        self.content = _copy_model_list(content)
        self.locations = _copy_model_list(locations)
        self.raw_input = raw_input
        self.raw_output = raw_output
        self._stream_buffer: str | None = None

    def to_view(self) -> TrackedToolCallView:
        return TrackedToolCallView(
            tool_call_id=self.tool_call_id,
            title=self.title,
            kind=self.kind,
            status=self.status,
            content=tuple(item.model_copy(deep=True) for item in self.content) if self.content else None,
            locations=tuple(loc.model_copy(deep=True) for loc in self.locations) if self.locations else None,
            raw_input=self.raw_input,
            raw_output=self.raw_output,
        )

    def to_tool_call_model(self) -> ToolCallUpdate:
        return ToolCallUpdate(
            tool_call_id=self.tool_call_id,
            title=self.title,
            kind=self.kind,
            status=self.status,
            content=_copy_model_list(self.content),
            locations=_copy_model_list(self.locations),
            raw_input=self.raw_input,
            raw_output=self.raw_output,
        )

    def to_start_model(self) -> ToolCallStart:
        if self.title is None:
            raise _MissingToolCallTitleError()
        return ToolCallStart(
            session_update="tool_call",
            tool_call_id=self.tool_call_id,
            title=self.title,
            kind=self.kind,
            status=self.status,
            content=_copy_model_list(self.content),
            locations=_copy_model_list(self.locations),
            raw_input=self.raw_input,
            raw_output=self.raw_output,
        )

    def update(
        self,
        *,
        title: Any = UNSET,
        kind: Any = UNSET,
        status: Any = UNSET,
        content: Any = UNSET,
        locations: Any = UNSET,
        raw_input: Any = UNSET,
        raw_output: Any = UNSET,
    ) -> ToolCallProgress:
        kwargs: dict[str, Any] = {}
        if title is not UNSET:
            self.title = cast(str | None, title)
            kwargs["title"] = self.title
        if kind is not UNSET:
            self.kind = cast(ToolKind | None, kind)
            kwargs["kind"] = self.kind
        if status is not UNSET:
            self.status = cast(ToolCallStatus | None, status)
            kwargs["status"] = self.status
        if content is not UNSET:
            seq_content = cast(Sequence[Any] | None, content)
            self.content = _copy_model_list(seq_content)
            kwargs["content"] = _copy_model_list(seq_content)
        if locations is not UNSET:
            seq_locations = cast(Sequence[ToolCallLocation] | None, locations)
            self.locations = cast(
                list[ToolCallLocation] | None,
                _copy_model_list(seq_locations),
            )
            kwargs["locations"] = _copy_model_list(seq_locations)
        if raw_input is not UNSET:
            self.raw_input = raw_input
            kwargs["rawInput"] = raw_input
        if raw_output is not UNSET:
            self.raw_output = raw_output
            kwargs["raw_output"] = raw_output
        return ToolCallProgress(session_update="tool_call_update", tool_call_id=self.tool_call_id, **kwargs)

    def append_stream_text(
        self,
        text: str,
        *,
        title: Any = UNSET,
        status: Any = UNSET,
    ) -> ToolCallProgress:
        self._stream_buffer = (self._stream_buffer or "") + text
        content = [tool_content(text_block(self._stream_buffer))]
        return self.update(title=title, status=status, content=content)


class ToolCallTracker:
    """Utility for generating ACP tool call updates on the server side."""

    def __init__(self, *, id_factory: Callable[[], str] | None = None) -> None:
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._calls: dict[str, _TrackedToolCall] = {}

    def start(
        self,
        external_id: str,
        *,
        title: str,
        kind: ToolKind | None = None,
        status: ToolCallStatus | None = "in_progress",
        content: Sequence[Any] | None = None,
        locations: Sequence[ToolCallLocation] | None = None,
        raw_input: Any = None,
        raw_output: Any = None,
    ) -> ToolCallStart:
        """Register a new tool call and return the ``tool_call`` notification."""
        call_id = self._id_factory()
        state = _TrackedToolCall(
            tool_call_id=call_id,
            title=title,
            kind=kind,
            status=status,
            content=content,
            locations=locations,
            raw_input=raw_input,
            raw_output=raw_output,
        )
        self._calls[external_id] = state
        return state.to_start_model()

    def progress(
        self,
        external_id: str,
        *,
        title: Any = UNSET,
        kind: Any = UNSET,
        status: Any = UNSET,
        content: Any = UNSET,
        locations: Any = UNSET,
        raw_input: Any = UNSET,
        raw_output: Any = UNSET,
    ) -> ToolCallProgress:
        """Produce a ``tool_call_update`` message and merge it into the tracker."""
        state = self._require_call(external_id)
        return state.update(
            title=title,
            kind=kind,
            status=status,
            content=content,
            locations=locations,
            raw_input=raw_input,
            raw_output=raw_output,
        )

    def append_stream_text(
        self,
        external_id: str,
        text: str,
        *,
        title: Any = UNSET,
        status: Any = UNSET,
    ) -> ToolCallProgress:
        """Append text to the tool call arguments/content and emit an update."""
        state = self._require_call(external_id)
        return state.append_stream_text(text, title=title, status=status)

    def forget(self, external_id: str) -> None:
        """Remove a tracked tool call (e.g. after completion)."""
        self._calls.pop(external_id, None)

    def view(self, external_id: str) -> TrackedToolCallView:
        """Return an immutable view of the current tool call state."""
        state = self._require_call(external_id)
        return state.to_view()

    def tool_call_model(self, external_id: str) -> ToolCallUpdate:
        """Return a deep copy of the tool call suitable for permission requests."""
        state = self._require_call(external_id)
        return state.to_tool_call_model()

    def _require_call(self, external_id: str) -> _TrackedToolCall:
        try:
            return self._calls[external_id]
        except KeyError as exc:
            raise _UnknownToolCallError(external_id) from exc


__all__ = [
    "UNSET",
    "ToolCallTracker",
    "TrackedToolCallView",
]
