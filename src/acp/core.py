"""Compatibility re-exports for historical imports.

The project now keeps implementation in dedicated modules mirroring the
agent-client-protocol Rust structure, but external callers may still import
from ``acp.core``. Keep the surface API stable by forwarding to the new homes.
"""

from __future__ import annotations

from .agent.connection import AgentSideConnection
from .client.connection import ClientSideConnection
from .connection import Connection, JsonValue, MethodHandler
from .exceptions import RequestError
from .interfaces import Agent, Client
from .terminal import TerminalHandle

__all__ = [
    "Agent",
    "AgentSideConnection",
    "Client",
    "ClientSideConnection",
    "Connection",
    "JsonValue",
    "MethodHandler",
    "RequestError",
    "TerminalHandle",
]
