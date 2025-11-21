import asyncio
import importlib.util
import os
import sys
from pathlib import Path

from acp import PROTOCOL_VERSION, spawn_agent_process


def _load_client_module(path: Path):
    spec = importlib.util.spec_from_file_location("examples_client", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load client module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("examples_client", module)
    spec.loader.exec_module(module)
    return module


async def main() -> int:
    root = Path(__file__).resolve().parent
    agent_path = root / "agent.py"

    env = os.environ.copy()
    src_dir = str((root.parent / "src").resolve())
    env["PYTHONPATH"] = src_dir + os.pathsep + env.get("PYTHONPATH", "")

    client_module = _load_client_module(root / "client.py")
    client = client_module.ExampleClient()

    async with spawn_agent_process(client, sys.executable, str(agent_path), env=env) as (
        conn,
        process,
    ):
        await conn.initialize(protocol_version=PROTOCOL_VERSION, client_capabilities=None)
        session = await conn.new_session(mcp_servers=[], cwd=str(root))
        await client_module.interactive_loop(conn, session.session_id)

    return process.returncode or 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
