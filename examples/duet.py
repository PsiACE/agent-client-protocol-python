import asyncio
import os
import sys
from pathlib import Path


async def main() -> int:
    root = Path(__file__).resolve().parent
    agent_path = str(root / "agent.py")
    client_path = str(root / "client.py")

    # Ensure PYTHONPATH includes project src for `from acp import ...`
    env = os.environ.copy()
    src_dir = str((root.parent / "src").resolve())
    env["PYTHONPATH"] = src_dir + os.pathsep + env.get("PYTHONPATH", "")

    # Run the client and let it spawn the agent, wiring stdio automatically.
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        client_path,
        agent_path,
        env=env,
    )
    return await proc.wait()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
