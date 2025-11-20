import sys
import textwrap

import pytest

from acp.transports import spawn_stdio_transport

LARGE_LINE_SIZE = 70 * 1024


def _large_line_script(size: int = LARGE_LINE_SIZE) -> str:
    return textwrap.dedent(
        f"""
        import sys
        sys.stdout.write("X" * {size})
        sys.stdout.write("\\n")
        sys.stdout.flush()
        """
    ).strip()


@pytest.mark.asyncio
async def test_spawn_stdio_transport_hits_default_limit() -> None:
    script = _large_line_script()
    async with spawn_stdio_transport(sys.executable, "-c", script) as (reader, _writer, _process):
        # readline() re-raises LimitOverrunError as ValueError on CPython 3.12+.
        with pytest.raises(ValueError):
            await reader.readline()


@pytest.mark.asyncio
async def test_spawn_stdio_transport_custom_limit_handles_large_line() -> None:
    script = _large_line_script()
    async with spawn_stdio_transport(
        sys.executable,
        "-c",
        script,
        limit=LARGE_LINE_SIZE * 2,
    ) as (reader, _writer, _process):
        line = await reader.readline()
        assert len(line) == LARGE_LINE_SIZE + 1
