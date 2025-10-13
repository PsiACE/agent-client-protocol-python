from __future__ import annotations

import argparse
import asyncio
import asyncio.subprocess
import contextlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable

from acp import (
    Client,
    ClientSideConnection,
    PROTOCOL_VERSION,
    RequestError,
    text_block,
)
from acp.schema import (
    AgentMessageChunk,
    AgentPlanUpdate,
    AgentThoughtChunk,
    AllowedOutcome,
    CancelNotification,
    ClientCapabilities,
    FileEditToolCallContent,
    FileSystemCapability,
    CreateTerminalRequest,
    CreateTerminalResponse,
    DeniedOutcome,
    EmbeddedResourceContentBlock,
    KillTerminalCommandRequest,
    KillTerminalCommandResponse,
    InitializeRequest,
    NewSessionRequest,
    PermissionOption,
    PromptRequest,
    ReadTextFileRequest,
    ReadTextFileResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    ResourceContentBlock,
    ReleaseTerminalRequest,
    ReleaseTerminalResponse,
    SessionNotification,
    TerminalToolCallContent,
    TerminalOutputRequest,
    TerminalOutputResponse,
    TextContentBlock,
    ToolCallProgress,
    ToolCallStart,
    UserMessageChunk,
    WaitForTerminalExitRequest,
    WaitForTerminalExitResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
)


class GeminiClient(Client):
    """Minimal client implementation that can drive the Gemini CLI over ACP."""

    def __init__(self, auto_approve: bool) -> None:
        self._auto_approve = auto_approve

    async def requestPermission(
        self,
        params: RequestPermissionRequest,
    ) -> RequestPermissionResponse:  # type: ignore[override]
        if self._auto_approve:
            option = _pick_preferred_option(params.options)
            if option is None:
                return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
            return RequestPermissionResponse(outcome=AllowedOutcome(optionId=option.optionId, outcome="selected"))

        title = params.toolCall.title or "<permission>"
        if not params.options:
            print(f"\n🔐 Permission requested: {title} (no options, cancelling)")
            return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
        print(f"\n🔐 Permission requested: {title}")
        for idx, opt in enumerate(params.options, start=1):
            print(f"  {idx}. {opt.name} ({opt.kind})")

        loop = asyncio.get_running_loop()
        while True:
            choice = await loop.run_in_executor(None, lambda: input("Select option: ").strip())
            if not choice:
                continue
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(params.options):
                    opt = params.options[idx]
                    return RequestPermissionResponse(outcome=AllowedOutcome(optionId=opt.optionId, outcome="selected"))
            print("Invalid selection, try again.")

    async def writeTextFile(
        self,
        params: WriteTextFileRequest,
    ) -> WriteTextFileResponse:  # type: ignore[override]
        path = Path(params.path)
        if not path.is_absolute():
            raise RequestError.invalid_params({"path": params.path, "reason": "path must be absolute"})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(params.content)
        print(f"[Client] Wrote {path} ({len(params.content)} bytes)")
        return WriteTextFileResponse()

    async def readTextFile(
        self,
        params: ReadTextFileRequest,
    ) -> ReadTextFileResponse:  # type: ignore[override]
        path = Path(params.path)
        if not path.is_absolute():
            raise RequestError.invalid_params({"path": params.path, "reason": "path must be absolute"})
        text = path.read_text()
        print(f"[Client] Read {path} ({len(text)} bytes)")
        if params.line is not None or params.limit is not None:
            text = _slice_text(text, params.line, params.limit)
        return ReadTextFileResponse(content=text)

    async def sessionUpdate(
        self,
        params: SessionNotification,
    ) -> None:  # type: ignore[override]
        update = params.update
        if isinstance(update, AgentMessageChunk):
            _print_text_content(update.content)
        elif isinstance(update, AgentThoughtChunk):
            print("\n[agent_thought]")
            _print_text_content(update.content)
        elif isinstance(update, UserMessageChunk):
            print("\n[user_message]")
            _print_text_content(update.content)
        elif isinstance(update, AgentPlanUpdate):
            print("\n[plan]")
            for entry in update.entries:
                print(f" - {entry.status.upper():<10} {entry.content}")
        elif isinstance(update, ToolCallStart):
            print(f"\n🔧 {update.title} ({update.status or 'pending'})")
        elif isinstance(update, ToolCallProgress):
            status = update.status or "in_progress"
            print(f"\n🔧 Tool call `{update.toolCallId}` → {status}")
            if update.content:
                for item in update.content:
                    if isinstance(item, FileEditToolCallContent):
                        print(f"  diff: {item.path}")
                    elif isinstance(item, TerminalToolCallContent):
                        print(f"  terminal: {item.terminalId}")
                    elif isinstance(item, dict):
                        print(f"  content: {json.dumps(item, indent=2)}")
        else:
            print(f"\n[session update] {update}")

    # Optional / terminal-related methods ---------------------------------
    async def createTerminal(
        self,
        params: CreateTerminalRequest,
    ) -> CreateTerminalResponse:  # type: ignore[override]
        print(f"[Client] createTerminal: {params}")
        return CreateTerminalResponse(terminalId="term-1")

    async def terminalOutput(
        self,
        params: TerminalOutputRequest,
    ) -> TerminalOutputResponse:  # type: ignore[override]
        print(f"[Client] terminalOutput: {params}")
        return TerminalOutputResponse(output="", truncated=False)

    async def releaseTerminal(
        self,
        params: ReleaseTerminalRequest,
    ) -> ReleaseTerminalResponse:  # type: ignore[override]
        print(f"[Client] releaseTerminal: {params}")
        return ReleaseTerminalResponse()

    async def waitForTerminalExit(
        self,
        params: WaitForTerminalExitRequest,
    ) -> WaitForTerminalExitResponse:  # type: ignore[override]
        print(f"[Client] waitForTerminalExit: {params}")
        return WaitForTerminalExitResponse()

    async def killTerminal(
        self,
        params: KillTerminalCommandRequest,
    ) -> KillTerminalCommandResponse:  # type: ignore[override]
        print(f"[Client] killTerminal: {params}")
        return KillTerminalCommandResponse()


def _pick_preferred_option(options: Iterable[PermissionOption]) -> PermissionOption | None:
    best: PermissionOption | None = None
    for option in options:
        if option.kind in {"allow_once", "allow_always"}:
            return option
        best = best or option
    return best


def _slice_text(content: str, line: int | None, limit: int | None) -> str:
    lines = content.splitlines()
    start = 0
    if line:
        start = max(line - 1, 0)
    end = len(lines)
    if limit:
        end = min(start + limit, end)
    return "\n".join(lines[start:end])


def _print_text_content(content: object) -> None:
    if isinstance(content, TextContentBlock):
        print(content.text)
    elif isinstance(content, ResourceContentBlock):
        print(f"{content.name or content.uri}")
    elif isinstance(content, EmbeddedResourceContentBlock):
        resource = content.resource
        text = getattr(resource, "text", None)
        if text:
            print(text)
        else:
            blob = getattr(resource, "blob", None)
            print(blob if blob else "<embedded resource>")
    elif isinstance(content, dict):
        text = content.get("text")  # type: ignore[union-attr]
        if text:
            print(text)


async def interactive_loop(conn: ClientSideConnection, session_id: str) -> None:
    print("Type a message and press Enter to send.")
    print("Commands: :cancel, :exit")

    loop = asyncio.get_running_loop()
    while True:
        try:
            line = await loop.run_in_executor(None, lambda: input("\n> ").strip())
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not line:
            continue
        if line in {":exit", ":quit"}:
            break
        if line == ":cancel":
            await conn.cancel(CancelNotification(sessionId=session_id))
            continue

        try:
            await conn.prompt(
                PromptRequest(
                    sessionId=session_id,
                    prompt=[text_block(line)],
                )
            )
        except RequestError as err:
            _print_request_error("prompt", err)
        except Exception as exc:  # noqa: BLE001
            print(f"Prompt failed: {exc}", file=sys.stderr)


def _resolve_gemini_cli(binary: str | None) -> str:
    if binary:
        return binary
    env_value = os.environ.get("ACP_GEMINI_BIN")
    if env_value:
        return env_value
    resolved = shutil.which("gemini")
    if resolved:
        return resolved
    raise FileNotFoundError("Unable to locate `gemini` CLI, provide --gemini path")


async def run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Interact with the Gemini CLI over ACP.")
    parser.add_argument("--gemini", help="Path to the Gemini CLI binary")
    parser.add_argument("--model", help="Model identifier to pass to Gemini")
    parser.add_argument("--sandbox", action="store_true", help="Enable Gemini sandbox mode")
    parser.add_argument("--debug", action="store_true", help="Pass --debug to Gemini")
    parser.add_argument("--yolo", action="store_true", help="Auto-approve permission prompts")
    args = parser.parse_args(argv[1:])

    try:
        gemini_path = _resolve_gemini_cli(args.gemini)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    cmd = [gemini_path, "--experimental-acp"]
    if args.model:
        cmd += ["--model", args.model]
    if args.sandbox:
        cmd.append("--sandbox")
    if args.debug:
        cmd.append("--debug")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=None,
        )
    except FileNotFoundError as exc:
        print(f"Failed to start Gemini CLI: {exc}", file=sys.stderr)
        return 1

    if proc.stdin is None or proc.stdout is None:
        print("Gemini process did not expose stdio pipes.", file=sys.stderr)
        proc.terminate()
        with contextlib.suppress(ProcessLookupError):
            await proc.wait()
        return 1

    client_impl = GeminiClient(auto_approve=args.yolo)
    conn = ClientSideConnection(lambda _agent: client_impl, proc.stdin, proc.stdout)

    try:
        init_resp = await conn.initialize(
            InitializeRequest(
                protocolVersion=PROTOCOL_VERSION,
                clientCapabilities=ClientCapabilities(
                    fs=FileSystemCapability(readTextFile=True, writeTextFile=True),
                    terminal=True,
                ),
            )
        )
    except RequestError as err:
        _print_request_error("initialize", err)
        await _shutdown(proc, conn)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"initialize error: {exc}", file=sys.stderr)
        await _shutdown(proc, conn)
        return 1

    print(f"✅ Connected to Gemini (protocol v{init_resp.protocolVersion})")

    try:
        session = await conn.newSession(
            NewSessionRequest(
                cwd=os.getcwd(),
                mcpServers=[],
            )
        )
    except RequestError as err:
        _print_request_error("new_session", err)
        await _shutdown(proc, conn)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"new_session error: {exc}", file=sys.stderr)
        await _shutdown(proc, conn)
        return 1

    print(f"📝 Created session: {session.sessionId}")

    try:
        await interactive_loop(conn, session.sessionId)
    finally:
        await _shutdown(proc, conn)

    return 0


def _print_request_error(stage: str, err: RequestError) -> None:
    payload = err.to_error_obj()
    message = payload.get("message", "")
    code = payload.get("code")
    print(f"{stage} error ({code}): {message}", file=sys.stderr)
    data = payload.get("data")
    if data is not None:
        try:
            formatted = json.dumps(data, indent=2)
        except TypeError:
            formatted = str(data)
        print(formatted, file=sys.stderr)


async def _shutdown(proc: asyncio.subprocess.Process, conn: ClientSideConnection) -> None:
    with contextlib.suppress(Exception):
        await conn.close()
    if proc.returncode is None:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()


def main(argv: list[str] | None = None) -> int:
    args = sys.argv if argv is None else argv
    return asyncio.run(run(list(args)))


if __name__ == "__main__":
    raise SystemExit(main())
