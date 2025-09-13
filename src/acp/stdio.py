from __future__ import annotations

import asyncio
import contextlib
import logging
import platform
import sys
from asyncio import transports as aio_transports
from typing import cast


class _WritePipeProtocol(asyncio.BaseProtocol):
    def __init__(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._paused = False
        self._drain_waiter: asyncio.Future[None] | None = None

    def pause_writing(self) -> None:  # type: ignore[override]
        self._paused = True
        if self._drain_waiter is None:
            self._drain_waiter = self._loop.create_future()

    def resume_writing(self) -> None:  # type: ignore[override]
        self._paused = False
        if self._drain_waiter is not None and not self._drain_waiter.done():
            self._drain_waiter.set_result(None)
        self._drain_waiter = None

    async def _drain_helper(self) -> None:
        if self._paused and self._drain_waiter is not None:
            await self._drain_waiter


def _start_stdin_feeder(loop: asyncio.AbstractEventLoop, reader: asyncio.StreamReader) -> None:
    # Feed stdin from a background thread line-by-line
    def blocking_read() -> None:
        try:
            while True:
                data = sys.stdin.buffer.readline()
                if not data:
                    break
                loop.call_soon_threadsafe(reader.feed_data, data)
        finally:
            loop.call_soon_threadsafe(reader.feed_eof)

    import threading

    threading.Thread(target=blocking_read, daemon=True).start()


class _StdoutTransport(asyncio.BaseTransport):
    def __init__(self) -> None:
        self._is_closing = False

    def write(self, data: bytes) -> None:  # type: ignore[override]
        if self._is_closing:
            return
        try:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        except Exception:
            logging.exception("Error writing to stdout")

    def can_write_eof(self) -> bool:  # type: ignore[override]
        return False

    def is_closing(self) -> bool:  # type: ignore[override]
        return self._is_closing

    def close(self) -> None:  # type: ignore[override]
        self._is_closing = True
        with contextlib.suppress(Exception):
            sys.stdout.flush()

    def abort(self) -> None:  # type: ignore[override]
        self.close()

    def get_extra_info(self, name: str, default=None):  # type: ignore[override]
        return default


async def _windows_stdio_streams(loop: asyncio.AbstractEventLoop) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    reader = asyncio.StreamReader()
    _ = asyncio.StreamReaderProtocol(reader)

    _start_stdin_feeder(loop, reader)

    write_protocol = _WritePipeProtocol()
    transport = _StdoutTransport()
    writer = asyncio.StreamWriter(cast(aio_transports.WriteTransport, transport), write_protocol, None, loop)
    return reader, writer


async def _posix_stdio_streams(loop: asyncio.AbstractEventLoop) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    # Reader from stdin
    reader = asyncio.StreamReader()
    reader_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)

    # Writer to stdout with protocol providing _drain_helper
    write_protocol = _WritePipeProtocol()
    transport, _ = await loop.connect_write_pipe(lambda: write_protocol, sys.stdout)
    writer = asyncio.StreamWriter(transport, write_protocol, None, loop)
    return reader, writer


async def stdio_streams() -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Create stdio asyncio streams; on Windows use a thread feeder + custom stdout transport."""
    loop = asyncio.get_running_loop()
    if platform.system() == "Windows":
        return await _windows_stdio_streams(loop)
    return await _posix_stdio_streams(loop)
