from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import suppress
from typing import Any

from pydantic import BaseModel, ConfigDict

from ..schema import (
    AgentMessageChunk,
    AgentPlanUpdate,
    AgentThoughtChunk,
    AvailableCommand,
    AvailableCommandsUpdate,
    CurrentModeUpdate,
    PlanEntry,
    SessionNotification,
    ToolCallLocation,
    ToolCallProgress,
    ToolCallStart,
    ToolCallStatus,
    ToolKind,
    UserMessageChunk,
)


class SessionNotificationMismatchError(ValueError):
    """Raised when the accumulator receives notifications from a different session."""

    def __init__(self, expected: str, actual: str) -> None:
        message = f"SessionAccumulator received notification for {actual}, expected {expected}"
        super().__init__(message)


class SessionSnapshotUnavailableError(RuntimeError):
    """Raised when a session snapshot is requested before any notifications."""

    def __init__(self) -> None:
        super().__init__("SessionAccumulator has not processed any notifications yet")


def _copy_model_list(items: Sequence[Any] | None) -> list[Any] | None:
    if items is None:
        return None
    return [item.model_copy(deep=True) for item in items]


class _MutableToolCallState:
    def __init__(self, tool_call_id: str) -> None:
        self.tool_call_id = tool_call_id
        self.title: str | None = None
        self.kind: ToolKind | None = None
        self.status: ToolCallStatus | None = None
        self.content: list[Any] | None = None
        self.locations: list[ToolCallLocation] | None = None
        self.raw_input: Any = None
        self.raw_output: Any = None

    def apply_start(self, update: ToolCallStart) -> None:
        self.title = update.title
        self.kind = update.kind
        self.status = update.status
        self.content = _copy_model_list(update.content)
        self.locations = _copy_model_list(update.locations)
        self.raw_input = update.raw_input
        self.raw_output = update.raw_output

    def apply_progress(self, update: ToolCallProgress) -> None:
        if update.title is not None:
            self.title = update.title
        if update.kind is not None:
            self.kind = update.kind
        if update.status is not None:
            self.status = update.status
        if update.content is not None:
            self.content = _copy_model_list(update.content)
        if update.locations is not None:
            self.locations = _copy_model_list(update.locations)
        if update.raw_input is not None:
            self.raw_input = update.raw_input
        if update.raw_output is not None:
            self.raw_output = update.raw_output

    def snapshot(self) -> ToolCallView:
        return ToolCallView(
            tool_call_id=self.tool_call_id,
            title=self.title,
            kind=self.kind,
            status=self.status,
            content=tuple(item.model_copy(deep=True) for item in self.content) if self.content else None,
            locations=tuple(loc.model_copy(deep=True) for loc in self.locations) if self.locations else None,
            raw_input=self.raw_input,
            raw_output=self.raw_output,
        )


class ToolCallView(BaseModel):
    """Immutable view of a tool call in the session."""

    model_config = ConfigDict(frozen=True)

    tool_call_id: str
    title: str | None
    kind: ToolKind | None
    status: ToolCallStatus | None
    content: tuple[Any, ...] | None
    locations: tuple[ToolCallLocation, ...] | None
    raw_input: Any
    raw_output: Any


class SessionSnapshot(BaseModel):
    """Aggregated snapshot of the most recent session state."""

    model_config = ConfigDict(frozen=True)

    session_id: str
    tool_calls: dict[str, ToolCallView]
    plan_entries: tuple[PlanEntry, ...]
    current_mode_id: str | None
    available_commands: tuple[AvailableCommand, ...]
    user_messages: tuple[UserMessageChunk, ...]
    agent_messages: tuple[AgentMessageChunk, ...]
    agent_thoughts: tuple[AgentThoughtChunk, ...]


class SessionAccumulator:
    """Merge :class:`acp.schema.SessionNotification` objects into a session snapshot.

    The accumulator focuses on the common requirements observed in the Toad UI:

    * Always expose the latest merged tool call state (even if updates arrive
      without a matching ``tool_call`` start).
    * Track the agent plan, available commands, and current mode id.
    * Record the raw stream of user/agent message chunks for UI rendering.

    This helper is **experimental**: APIs may change while we gather feedback.
    """

    def __init__(self, *, auto_reset_on_session_change: bool = True) -> None:
        self._auto_reset = auto_reset_on_session_change
        self.session_id: str | None = None
        self._tool_calls: dict[str, _MutableToolCallState] = {}
        self._plan_entries: list[PlanEntry] = []
        self._current_mode_id: str | None = None
        self._available_commands: list[AvailableCommand] = []
        self._user_messages: list[UserMessageChunk] = []
        self._agent_messages: list[AgentMessageChunk] = []
        self._agent_thoughts: list[AgentThoughtChunk] = []
        self._subscribers: list[Callable[[SessionSnapshot, SessionNotification], None]] = []

    def reset(self) -> None:
        """Clear all accumulated state."""
        self.session_id = None
        self._tool_calls.clear()
        self._plan_entries.clear()
        self._current_mode_id = None
        self._available_commands.clear()
        self._user_messages.clear()
        self._agent_messages.clear()
        self._agent_thoughts.clear()

    def subscribe(self, callback: Callable[[SessionSnapshot, SessionNotification], None]) -> Callable[[], None]:
        """Register a callback that receives every new snapshot.

        The callback is invoked immediately after :meth:`apply` finishes. The
        function returns an ``unsubscribe`` callable.
        """

        self._subscribers.append(callback)

        def unsubscribe() -> None:
            with suppress(ValueError):
                self._subscribers.remove(callback)

        return unsubscribe

    def apply(self, notification: SessionNotification) -> SessionSnapshot:
        """Merge a new session notification into the current snapshot."""
        self._ensure_session(notification)
        self._apply_update(notification.update)
        snapshot = self.snapshot()
        self._notify_subscribers(snapshot, notification)
        return snapshot

    def _ensure_session(self, notification: SessionNotification) -> None:
        if self.session_id is None:
            self.session_id = notification.session_id
            return

        if notification.session_id != self.session_id:
            self._handle_session_change(notification.session_id)

    def _handle_session_change(self, session_id: str) -> None:
        expected = self.session_id
        if expected is None:
            self.session_id = session_id
            return

        if not self._auto_reset:
            raise SessionNotificationMismatchError(expected, session_id)

        self.reset()
        self.session_id = session_id

    def _apply_update(self, update: Any) -> None:
        if isinstance(update, ToolCallStart):
            state = self._tool_calls.setdefault(
                update.tool_call_id, _MutableToolCallState(tool_call_id=update.tool_call_id)
            )
            state.apply_start(update)
            return

        if isinstance(update, ToolCallProgress):
            state = self._tool_calls.setdefault(
                update.tool_call_id, _MutableToolCallState(tool_call_id=update.tool_call_id)
            )
            state.apply_progress(update)
            return

        if isinstance(update, AgentPlanUpdate):
            self._plan_entries = _copy_model_list(update.entries) or []
            return

        if isinstance(update, CurrentModeUpdate):
            self._current_mode_id = update.current_mode_id
            return

        if isinstance(update, AvailableCommandsUpdate):
            self._available_commands = _copy_model_list(update.available_commands) or []
            return

        if isinstance(update, UserMessageChunk):
            self._user_messages.append(update.model_copy(deep=True))
            return

        if isinstance(update, AgentMessageChunk):
            self._agent_messages.append(update.model_copy(deep=True))
            return

        if isinstance(update, AgentThoughtChunk):
            self._agent_thoughts.append(update.model_copy(deep=True))

    def _notify_subscribers(
        self,
        snapshot: SessionSnapshot,
        notification: SessionNotification,
    ) -> None:
        for callback in list(self._subscribers):
            callback(snapshot, notification)

    def snapshot(self) -> SessionSnapshot:
        """Return an immutable snapshot of the current state."""
        if self.session_id is None:
            raise SessionSnapshotUnavailableError()

        tool_calls = {tool_call_id: state.snapshot() for tool_call_id, state in self._tool_calls.items()}
        plan_entries = tuple(entry.model_copy(deep=True) for entry in self._plan_entries)
        available_commands = tuple(command.model_copy(deep=True) for command in self._available_commands)
        user_messages = tuple(message.model_copy(deep=True) for message in self._user_messages)
        agent_messages = tuple(message.model_copy(deep=True) for message in self._agent_messages)
        agent_thoughts = tuple(message.model_copy(deep=True) for message in self._agent_thoughts)

        return SessionSnapshot(
            session_id=self.session_id,
            tool_calls=tool_calls,
            plan_entries=plan_entries,
            current_mode_id=self._current_mode_id,
            available_commands=available_commands,
            user_messages=user_messages,
            agent_messages=agent_messages,
            agent_thoughts=agent_thoughts,
        )
