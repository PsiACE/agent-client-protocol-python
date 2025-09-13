import asyncio
import contextlib
import os
import signal
import sys
from pathlib import Path


async def _relay(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, tag: str):
    try:
        while True:
            line = await reader.readline()
            if not line:
                break
            writer.write(line)
            try:
                await writer.drain()
            except ConnectionError:
                break
            # Mirror minimal logs for visibility
            sys.stderr.write(f"[{tag}] {line.decode('utf-8', errors='replace')}")
            sys.stderr.flush()
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def main() -> None:
    # Launch the Textual client only; it will spawn the agent as a child and connect to it via pipes.
    root = Path(__file__).resolve().parent
    client_path = str(root / "client.py")

    env = os.environ.copy()
    src_dir = str((root.parents[1] / "src").resolve())
    env["PYTHONPATH"] = src_dir + os.pathsep + env.get("PYTHONPATH", "")

    client = await asyncio.create_subprocess_exec(
        sys.executable,
        client_path,
        stderr=sys.stderr,
        env=env,
    )

    await client.wait()


if __name__ == "__main__":
    asyncio.run(main())
