from __future__ import annotations

import asyncio
import asyncio.subprocess as aio_subprocess
import contextlib
import os
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path

__all__ = ["DEFAULT_INHERITED_ENV_VARS", "default_environment", "spawn_stdio_transport"]

DEFAULT_INHERITED_ENV_VARS = (
    [
        "APPDATA",
        "HOMEDRIVE",
        "HOMEPATH",
        "LOCALAPPDATA",
        "PATH",
        "PATHEXT",
        "PROCESSOR_ARCHITECTURE",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "USERNAME",
        "USERPROFILE",
    ]
    if os.name == "nt"
    else ["HOME", "LOGNAME", "PATH", "SHELL", "TERM", "USER"]
)


def default_environment() -> dict[str, str]:
    """Return a trimmed environment based on MCP best practices."""
    env: dict[str, str] = {}
    for key in DEFAULT_INHERITED_ENV_VARS:
        value = os.environ.get(key)
        if value is None:
            continue
        # Skip function-style env vars on some shells (see MCP reference)
        if value.startswith("()"):
            continue
        env[key] = value
    return env


@asynccontextmanager
async def spawn_stdio_transport(
    command: str,
    *args: str,
    env: Mapping[str, str] | None = None,
    cwd: str | Path | None = None,
    stderr: int | None = aio_subprocess.PIPE,
    limit: int | None = None,
    shutdown_timeout: float = 2.0,
) -> AsyncIterator[tuple[asyncio.StreamReader, asyncio.StreamWriter, aio_subprocess.Process]]:
    """Launch a subprocess and expose its stdio streams as asyncio transports.

    This mirrors the defensive shutdown behaviour used by the MCP Python SDK:
    close stdin first, wait for graceful exit, then escalate to terminate/kill.
    """
    merged_env = dict(default_environment())
    if env:
        merged_env.update(env)

    if limit is None:
        process = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=aio_subprocess.PIPE,
            stdout=aio_subprocess.PIPE,
            stderr=stderr,
            env=merged_env,
            cwd=str(cwd) if cwd is not None else None,
        )
    else:
        process = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=aio_subprocess.PIPE,
            stdout=aio_subprocess.PIPE,
            stderr=stderr,
            env=merged_env,
            cwd=str(cwd) if cwd is not None else None,
            limit=limit,
        )

    if process.stdout is None or process.stdin is None:
        process.kill()
        await process.wait()
        msg = "spawn_stdio_transport requires stdout/stderr pipes"
        raise RuntimeError(msg)

    try:
        yield process.stdout, process.stdin, process
    finally:
        # Attempt graceful stdin shutdown first
        if process.stdin is not None:
            try:
                process.stdin.write_eof()
            except (AttributeError, OSError, RuntimeError):
                process.stdin.close()
            with contextlib.suppress(Exception):
                await process.stdin.drain()
            with contextlib.suppress(Exception):
                process.stdin.close()
            with contextlib.suppress(Exception):
                await process.stdin.wait_closed()

        try:
            await asyncio.wait_for(process.wait(), timeout=shutdown_timeout)
        except asyncio.TimeoutError:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=shutdown_timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
