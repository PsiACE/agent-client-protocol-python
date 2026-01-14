import os
import subprocess
import sys
import tempfile
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


@pytest.mark.asyncio
async def test_run_agent_stdio_buffer_limit() -> None:
    """Test that run_agent with different buffer limits can handle appropriately sized messages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: Small buffer (1KB) fails with large message (70KB)
        small_agent = os.path.join(tmpdir, "small_agent.py")
        with open(small_agent, "w") as f:
            f.write("""
import asyncio
from acp.core import run_agent
from acp.interfaces import Agent

class TestAgent(Agent):
    async def list_capabilities(self):
        return {"capabilities": {}}

asyncio.run(run_agent(TestAgent(), stdio_buffer_limit_bytes=1024))
""")

        # Send a 70KB message - should fail with 1KB buffer
        large_msg = '{"jsonrpc":"2.0","method":"test","params":{"data":"' + "X" * LARGE_LINE_SIZE + '"}}\n'
        result = subprocess.run(  # noqa: S603
            [sys.executable, small_agent], input=large_msg, capture_output=True, text=True, timeout=2
        )

        # Should have errors in stderr about the buffer limit
        assert "Error" in result.stderr or result.returncode != 0, (
            f"Expected error with small buffer, got: {result.stderr}"
        )

        # Test 2: Large buffer (200KB) succeeds with large message (70KB)
        large_agent = os.path.join(tmpdir, "large_agent.py")
        with open(large_agent, "w") as f:
            f.write(f"""
import asyncio
from acp.core import run_agent
from acp.interfaces import Agent

class TestAgent(Agent):
    async def list_capabilities(self):
        return {{"capabilities": {{}}}}

asyncio.run(run_agent(TestAgent(), stdio_buffer_limit_bytes={LARGE_LINE_SIZE * 3}))
""")

        # Same message, but with a buffer 3x the size - should handle it
        result = subprocess.run(  # noqa: S603
            [sys.executable, large_agent], input=large_msg, capture_output=True, text=True, timeout=2
        )

        # With a large enough buffer, the agent should at least start successfully
        # (it may have other errors from invalid JSON-RPC, but not buffer overrun)
        if "LimitOverrunError" in result.stderr or "buffer" in result.stderr.lower():
            pytest.fail(f"Large buffer still hit limit error: {result.stderr}")
