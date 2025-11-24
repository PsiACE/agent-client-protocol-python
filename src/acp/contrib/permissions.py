from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from ..helpers import text_block, tool_content
from ..schema import PermissionOption, RequestPermissionRequest, RequestPermissionResponse, ToolCallUpdate
from .tool_calls import ToolCallTracker, _copy_model_list


class PermissionBrokerError(ValueError):
    """Base error for permission broker misconfiguration."""


class MissingToolCallError(PermissionBrokerError):
    """Raised when a permission request is missing the referenced tool call."""

    def __init__(self) -> None:
        super().__init__("tool_call must be provided when no ToolCallTracker is configured")


class MissingPermissionOptionsError(PermissionBrokerError):
    """Raised when no permission options are available for a request."""

    def __init__(self) -> None:
        super().__init__("PermissionBroker requires at least one permission option")


def default_permission_options() -> tuple[PermissionOption, PermissionOption, PermissionOption]:
    """Return a standard approval/reject option set."""
    return (
        PermissionOption(option_id="approve", name="Approve", kind="allow_once"),
        PermissionOption(option_id="approve_for_session", name="Approve for session", kind="allow_always"),
        PermissionOption(option_id="reject", name="Reject", kind="reject_once"),
    )


class PermissionBroker:
    """Helper for issuing permission requests tied to tracked tool calls."""

    def __init__(
        self,
        session_id: str,
        requester: Callable[[RequestPermissionRequest], Awaitable[RequestPermissionResponse]],
        *,
        tracker: ToolCallTracker | None = None,
        default_options: Sequence[PermissionOption] | None = None,
    ) -> None:
        self._session_id = session_id
        self._requester = requester
        self._tracker = tracker
        self._default_options = tuple(
            option.model_copy(deep=True) for option in (default_options or default_permission_options())
        )

    async def request_for(
        self,
        external_id: str,
        *,
        description: str | None = None,
        options: Sequence[PermissionOption] | None = None,
        content: Sequence[Any] | None = None,
        tool_call: ToolCallUpdate | None = None,
    ) -> RequestPermissionResponse:
        """Request user approval for a tool call."""
        if tool_call is None:
            if self._tracker is None:
                raise MissingToolCallError()
            tool_call = self._tracker.tool_call_model(external_id)
        else:
            tool_call = tool_call.model_copy(deep=True)

        if content is not None:
            tool_call.content = _copy_model_list(content)

        if description:
            existing = tool_call.content or []
            existing.append(tool_content(text_block(description)))
            tool_call.content = existing

        option_set = tuple(option.model_copy(deep=True) for option in (options or self._default_options))
        if not option_set:
            raise MissingPermissionOptionsError()

        request = RequestPermissionRequest(
            session_id=self._session_id,
            tool_call=tool_call,
            options=list(option_set),
        )
        return await self._requester(request)


__all__ = [
    "PermissionBroker",
    "default_permission_options",
]
