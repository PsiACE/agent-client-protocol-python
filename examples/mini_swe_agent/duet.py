import asyncio
import contextlib
import os
import sys
from pathlib import Path


async def main() -> None:
    # Launch agent and client, wiring a dedicated pipe pair for ACP protocol.
    # Client keeps its own stdin/stdout for the Textual UI.
    root = Path(__file__).resolve().parent
    agent_path = str(root / "agent.py")
    client_path = str(root / "client.py")

    # Load .env into process env so children inherit it (prefer python-dotenv if available)
    try:
        from dotenv import load_dotenv  # type: ignore

        # Load .env from repo root: examples/mini_swe_agent -> examples -> REPO
        load_dotenv(dotenv_path=str(root.parents[1] / ".env"), override=True)
    except Exception:
        pass

    base_env = os.environ.copy()
    src_dir = str((root.parents[1] / "src").resolve())
    base_env["PYTHONPATH"] = src_dir + os.pathsep + base_env.get("PYTHONPATH", "")

    # Create two pipes: agent->client and client->agent
    a2c_r, a2c_w = os.pipe()
    c2a_r, c2a_w = os.pipe()
    # Ensure the FDs we pass to children are inheritable
    for fd in (a2c_r, a2c_w, c2a_r, c2a_w):
        os.set_inheritable(fd, True)

    # Start agent: stdin <- client (c2a_r), stdout -> client (a2c_w)
    agent = await asyncio.create_subprocess_exec(
        sys.executable,
        agent_path,
        stdin=c2a_r,
        stdout=a2c_w,
        stderr=sys.stderr,
        env=base_env,
        close_fds=True,
    )

    # Start client with ACP FDs exported via environment; keep terminal IO for UI
    client_env = base_env.copy()
    client_env["MSWEA_READ_FD"] = str(a2c_r)  # where client reads ACP messages
    client_env["MSWEA_WRITE_FD"] = str(c2a_w)  # where client writes ACP messages

    client = await asyncio.create_subprocess_exec(
        sys.executable,
        client_path,
        env=client_env,
        pass_fds=(a2c_r, c2a_w),  # ensure client inherits these FDs
        close_fds=True,
    )

    # Close parent's copies of the pipe ends to avoid leaks
    for fd in (a2c_r, a2c_w, c2a_r, c2a_w):
        with contextlib.suppress(OSError):
            os.close(fd)

    # If either process exits, terminate the other gracefully
    agent_task = asyncio.create_task(agent.wait())
    client_task = asyncio.create_task(client.wait())
    done, pending = await asyncio.wait({agent_task, client_task}, return_when=asyncio.FIRST_COMPLETED)

    # Terminate the peer process
    if agent_task in done and client.returncode is None:
        with contextlib.suppress(ProcessLookupError):
            client.terminate()
    if client_task in done and agent.returncode is None:
        with contextlib.suppress(ProcessLookupError):
            agent.terminate()

    # Wait a bit, then kill if still running
    try:
        await asyncio.wait_for(asyncio.gather(agent.wait(), client.wait()), timeout=3)
    except asyncio.TimeoutError:
        with contextlib.suppress(ProcessLookupError):
            if agent.returncode is None:
                agent.kill()
        with contextlib.suppress(ProcessLookupError):
            if client.returncode is None:
                client.kill()
        await asyncio.gather(agent.wait(), client.wait())


if __name__ == "__main__":
    asyncio.run(main())
