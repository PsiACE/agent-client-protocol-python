"""Compatibility re-exports for historical imports.

The project now keeps implementation in dedicated modules mirroring the
agent-client-protocol Rust structure, but external callers may still import
from ``acp.core``. Keep the surface API stable by forwarding to the new homes.
"""

from __future__ import annotations

from typing import Any

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
    "connect_to_agent",
    "run_agent",
]


async def run_agent(
    agent: Agent,
    input_stream: Any = None,
    output_stream: Any = None,
    *,
    use_unstable_protocol: bool = False,
    **connection_kwargs: Any,
) -> None:
    """Run an ACP agent over the given input/output streams.

    This is a convenience function that creates an :class:`AgentSideConnection`
    and starts listening for incoming messages.

    Args:
        agent: The agent implementation to run.
        input_stream: The (client) input stream to write to (defaults: ``sys.stdin``).
        output_stream: The (client) output stream to read from (defaults: ``sys.stdout``).
        use_unstable_protocol: Whether to enable unstable protocol features.
        **connection_kwargs: Additional keyword arguments to pass to the
            :class:`AgentSideConnection` constructor.
    """
    from .stdio import stdio_streams

    if input_stream is None and output_stream is None:
        output_stream, input_stream = await stdio_streams()
    conn = AgentSideConnection(
        agent,
        input_stream,
        output_stream,
        listening=False,
        use_unstable_protocol=use_unstable_protocol,
        **connection_kwargs,
    )
    await conn.listen()


def connect_to_agent(
    client: Client,
    input_stream: Any,
    output_stream: Any,
    *,
    use_unstable_protocol: bool = False,
    **connection_kwargs: Any,
) -> ClientSideConnection:
    """Create a ClientSideConnection to an ACP agent over the given input/output streams.

    Args:
        client: The client implementation to use.
        input_stream: The (agent) input stream to write to (default: ``sys.stdin``).
        output_stream: The (agent) output stream to read from (default: ``sys.stdout``).
        use_unstable_protocol: Whether to enable unstable protocol features.
        **connection_kwargs: Additional keyword arguments to pass to the
            :class:`ClientSideConnection` constructor.

    Returns:
        A :class:`ClientSideConnection` instance connected to the agent.
    """
    return ClientSideConnection(
        client, input_stream, output_stream, use_unstable_protocol=use_unstable_protocol, **connection_kwargs
    )
