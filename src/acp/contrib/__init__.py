"""
Experimental helpers for Agent Client Protocol integrations.

Everything exposed from :mod:`acp.contrib` is considered unstable and may change
without notice. These modules are published to share techniques observed in the
reference implementations (for example Toad or kimi-cli) while we continue
refining the core SDK surface.

The helpers live in ``acp.contrib`` so consuming applications must opt-in
explicitly, making it clear that the APIs are incubating.
"""

from __future__ import annotations

from .permissions import PermissionBroker, default_permission_options
from .session_state import SessionAccumulator, SessionSnapshot, ToolCallView
from .tool_calls import ToolCallTracker, TrackedToolCallView

__all__ = [
    "PermissionBroker",
    "SessionAccumulator",
    "SessionSnapshot",
    "ToolCallTracker",
    "ToolCallView",
    "TrackedToolCallView",
    "default_permission_options",
]
