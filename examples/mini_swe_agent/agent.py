import asyncio
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal

from acp import (
    Agent,
    AgentSideConnection,
    AuthenticateRequest,
    CancelNotification,
    Client,
    InitializeRequest,
    InitializeResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    SessionNotification,
    SetSessionModeRequest,
    SetSessionModeResponse,
    stdio_streams,
    PROTOCOL_VERSION,
)
from acp.schema import (
    AgentMessageChunk,
    AgentThoughtChunk,
    AllowedOutcome,
    ContentToolCallContent,
    PermissionOption,
    RequestPermissionRequest,
    RequestPermissionResponse,
    TextContentBlock,
    ToolCallStart,
    ToolCallProgress,
    ToolCallUpdate,
    UserMessageChunk,
)


# Lazily import mini-swe-agent to avoid hard dependency for users who don't need this example


@dataclass
class ACPAgentConfig:  # Extra controls layered on top of mini-swe-agent defaults
    mode: Literal["confirm", "yolo", "human"] = "confirm"
    whitelist_actions: list[str] = field(default_factory=list)
    confirm_exit: bool = True


def _create_streaming_mini_agent(
    *,
    client: Client,
    session_id: str,
    cwd: str,
    model_name: str,
    model_kwargs: dict[str, Any],
    loop: asyncio.AbstractEventLoop,
    ext_config: ACPAgentConfig,
):
    """Create a DefaultAgent that emits ACP session/update events during execution.

    Returns (agent, error_message_if_any).
    """
    try:
        try:
            from minisweagent.agents.default import (
                DefaultAgent,
                NonTerminatingException,
                Submitted,
                LimitsExceeded,
                AgentConfig as _BaseCfg,
            )  # type: ignore
            from minisweagent.environments.local import LocalEnvironment  # type: ignore
            from minisweagent.models.litellm_model import LitellmModel  # type: ignore
        except Exception:
            # Fallback to vendored reference copy if available
            REF_SRC = Path(__file__).resolve().parents[2] / "reference" / "mini-swe-agent" / "src"
            if REF_SRC.is_dir():
                if str(REF_SRC) not in sys.path:
                    sys.path.insert(0, str(REF_SRC))
                from minisweagent.agents.default import (
                    DefaultAgent,
                    NonTerminatingException,
                    Submitted,
                    LimitsExceeded,
                    AgentConfig as _BaseCfg,
                )  # type: ignore
                from minisweagent.environments.local import LocalEnvironment  # type: ignore
                from minisweagent.models.litellm_model import LitellmModel  # type: ignore
            else:
                raise

        class _StreamingMiniAgent(DefaultAgent):  # type: ignore[misc]
            def __init__(self) -> None:
                self._acp_client = client
                self._session_id = session_id
                self._tool_seq = 0
                self._loop = loop
                # expose mini-swe-agent exception types for outer loop
                self._Submitted = Submitted
                self._NonTerminatingException = NonTerminatingException
                self._LimitsExceeded = LimitsExceeded
                model = LitellmModel(model_name=model_name, model_kwargs=model_kwargs)
                env = LocalEnvironment(cwd=cwd)
                super().__init__(model=model, env=env, config_class=_BaseCfg)
                # extra config
                self.acp_config = ext_config
                # During initial seeding (system/user templates), suppress updates
                self._emit_updates = False

            # --- ACP streaming helpers ---

            def _schedule(self, coro):
                import asyncio as _asyncio

                return _asyncio.run_coroutine_threadsafe(coro, self._loop)

            async def _send(self, update_model) -> None:
                await self._acp_client.sessionUpdate(
                    SessionNotification(sessionId=self._session_id, update=update_model)
                )

            def _send_cost_hint(self) -> None:
                try:
                    cost = float(getattr(self.model, "cost", 0.0))
                except Exception:
                    cost = 0.0
                hint = AgentThoughtChunk(
                    sessionUpdate="agent_thought_chunk",
                    content=TextContentBlock(type="text", text=f"__COST__:{cost:.2f}"),
                )
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._send(hint))
                except RuntimeError:
                    self._schedule(self._send(hint))

            async def on_tool_start(self, title: str, command: str, tool_call_id: str) -> None:
                """Send a tool_call start notification for a bash command."""
                update = ToolCallStart(
                    sessionUpdate="tool_call",
                    toolCallId=tool_call_id,
                    title=title,
                    kind="execute",
                    status="pending",
                    content=[
                        ContentToolCallContent(
                            type="content", content=TextContentBlock(type="text", text=f"```bash\n{command}\n```")
                        )
                    ],
                    rawInput={"command": command},
                )
                await self._send(update)

            async def on_tool_complete(
                self,
                tool_call_id: str,
                output: str,
                returncode: int,
                *,
                status: str = "completed",
            ) -> None:
                """Send a tool_call_update with the final output and return code."""
                update = ToolCallProgress(
                    sessionUpdate="tool_call_update",
                    toolCallId=tool_call_id,
                    status=status,
                    content=[
                        ContentToolCallContent(
                            type="content", content=TextContentBlock(type="text", text=f"```ansi\n{output}\n```")
                        )
                    ],
                    rawOutput={"output": output, "returncode": returncode},
                )
                await self._send(update)

            def add_message(self, role: str, content: str, **kwargs):
                super().add_message(role, content, **kwargs)
                # Only stream LM output as agent_message_chunk; tool output is handled via tool_call_update.
                if not getattr(self, "_emit_updates", True) or role != "assistant":
                    return
                text = str(content)
                block = TextContentBlock(type="text", text=text)
                update = AgentMessageChunk(sessionUpdate="agent_message_chunk", content=block)
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._send(update))
                except RuntimeError:
                    self._schedule(self._send(update))
                # Fire-and-forget

            def _confirm_action_sync(self, tool_call_id: str, command: str) -> bool:
                # Build request and block until client responds
                req = RequestPermissionRequest(
                    sessionId=self._session_id,
                    options=[
                        PermissionOption(optionId="allow-once", name="Allow once", kind="allow_once"),
                        PermissionOption(optionId="reject-once", name="Reject", kind="reject_once"),
                    ],
                    toolCall=ToolCallUpdate(
                        toolCallId=tool_call_id,
                        title="bash",
                        kind="execute",
                        status="pending",
                        content=[
                            ContentToolCallContent(
                                type="content",
                                content=TextContentBlock(type="text", text=f"```bash\n{command}\n```"),
                            )
                        ],
                        rawInput={"command": command},
                    ),
                )
                fut = self._schedule(self._acp_client.requestPermission(req))
                try:
                    resp: RequestPermissionResponse = fut.result()  # type: ignore[assignment]
                except Exception:
                    return False
                out = resp.outcome
                if isinstance(out, AllowedOutcome) and out.optionId in ("allow-once", "allow-always"):
                    return True
                return False

            def execute_action(self, action: dict) -> dict:  # type: ignore[override]
                self._tool_seq += 1
                tool_id = f"mini-bash-{self._tool_seq}-{uuid.uuid4().hex[:8]}"
                command = action.get("action", "")

                # Always create tool_call first (pending)
                self._schedule(self.on_tool_start("bash", command, tool_id))

                # Request permission unless whitelisted
                if command.strip() and not any(re.match(r, command) for r in self.acp_config.whitelist_actions):
                    allowed = self._confirm_action_sync(tool_id, command)
                    if not allowed:
                        # Mark as cancelled/failed accordingly and abort this step
                        self._schedule(
                            self.on_tool_complete(
                                tool_id,
                                "Permission denied by user",
                                0,
                                status="cancelled",
                            )
                        )
                        raise self._NonTerminatingException("Command not executed: denied by user")

                try:
                    # Mark in progress
                    self._schedule(
                        self._send(
                            ToolCallProgress(
                                sessionUpdate="tool_call_update",
                                toolCallId=tool_id,
                                status="in_progress",
                            )
                        )
                    )
                    result = super().execute_action(action)
                    output = result.get("output", "")
                    returncode = int(result.get("returncode", 0) or 0)
                    self._schedule(self.on_tool_complete(tool_id, output, returncode, status="completed"))
                    return result
                except self._Submitted as e:  # type: ignore[misc]
                    final_text = str(e)
                    self._schedule(self.on_tool_complete(tool_id, final_text, 0, status="completed"))
                    raise
                except self._NonTerminatingException as e:  # type: ignore[misc]
                    msg = str(e)
                    status = (
                        "cancelled"
                        if any(
                            key in msg
                            for key in (
                                "Command not executed",
                                "Switching to human mode",
                                "switched to manual mode",
                                "Interrupted by user",
                            )
                        )
                        else "failed"
                    )
                    self._schedule(
                        self.on_tool_complete(tool_id, msg, 124 if status != "cancelled" else 0, status=status)
                    )
                    raise
                except Exception as e:  # include other failures
                    msg = str(e) or "execution failed"
                    self._schedule(self.on_tool_complete(tool_id, msg, 124, status="failed"))
                    raise

        return _StreamingMiniAgent(), None
    except Exception as e:
        return None, f"Failed to load mini-swe-agent: {e}"


class MiniSweACPAgent(Agent):
    def __init__(self, client: Client) -> None:
        self._client = client
        self._sessions: Dict[str, Dict[str, Any]] = {}

    async def initialize(self, _params: InitializeRequest) -> InitializeResponse:
        from acp.schema import AgentCapabilities, PromptCapabilities

        return InitializeResponse(
            protocolVersion=PROTOCOL_VERSION,
            agentCapabilities=AgentCapabilities(
                loadSession=True,
                promptCapabilities=PromptCapabilities(audio=False, image=False, embeddedContext=True),
            ),
            authMethods=[],
        )

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:
        session_id = f"sess-{uuid.uuid4().hex[:12]}"
        # load config from env for whitelist & confirm_exit
        cfg = ACPAgentConfig()
        try:
            import json as _json

            wl = os.getenv("MINI_SWE_WHITELIST", "[]")
            cfg.whitelist_actions = list(_json.loads(wl)) if wl else []  # type: ignore[assignment]
        except Exception:
            pass
        ce = os.getenv("MINI_SWE_CONFIRM_EXIT")
        if ce is not None:
            cfg.confirm_exit = ce.lower() not in ("0", "false", "no")
        self._sessions[session_id] = {
            "cwd": params.cwd,
            "agent": None,
            "task": None,
            "config": cfg,
        }
        return NewSessionResponse(sessionId=session_id)

    async def loadSession(self, params) -> None:  # type: ignore[override]
        try:
            session_id = params.sessionId  # type: ignore[attr-defined]
            cwd = params.cwd  # type: ignore[attr-defined]
        except Exception:
            session_id = getattr(params, "sessionId", "sess-unknown")
            cwd = getattr(params, "cwd", os.getcwd())
        if session_id not in self._sessions:
            cfg = ACPAgentConfig()
            try:
                import json as _json

                wl = os.getenv("MINI_SWE_WHITELIST", "[]")
                cfg.whitelist_actions = list(_json.loads(wl)) if wl else []  # type: ignore[assignment]
            except Exception:
                pass
            ce = os.getenv("MINI_SWE_CONFIRM_EXIT")
            if ce is not None:
                cfg.confirm_exit = ce.lower() not in ("0", "false", "no")
            self._sessions[session_id] = {"cwd": cwd, "agent": None, "task": None, "config": cfg}
        return None

    async def authenticate(self, _params: AuthenticateRequest) -> None:
        return None

    async def setSessionMode(self, params: SetSessionModeRequest) -> SetSessionModeResponse | None:  # type: ignore[override]
        sess = self._sessions.get(params.sessionId)
        if not sess:
            return SetSessionModeResponse()
        mode = params.modeId.lower()
        if mode in ("confirm", "yolo", "human"):
            sess["config"].mode = mode  # type: ignore[attr-defined]
        return SetSessionModeResponse()

    def _extract_mode_from_blocks(self, blocks) -> Literal["confirm", "yolo", "human"] | None:
        for b in blocks:
            if getattr(b, "type", None) == "text":
                t = getattr(b, "text", "") or ""
                m = re.search(r"\[\[MODE:([a-zA-Z]+)\]\]", t)
                if m:
                    mode = m.group(1).lower()
                    if mode in ("confirm", "yolo", "human"):
                        return mode  # type: ignore[return-value]
        return None

    def _extract_code_from_blocks(self, blocks) -> str | None:
        for b in blocks:
            if getattr(b, "type", None) == "text":
                t = getattr(b, "text", "") or ""
                actions = re.findall(r"```bash\n(.*?)\n```", t, re.DOTALL)
                if actions:
                    return actions[0].strip()
        return None

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        sess = self._sessions.get(params.sessionId)
        if not sess:
            self._sessions[params.sessionId] = {
                "cwd": os.getcwd(),
                "agent": None,
                "task": None,
                "config": ACPAgentConfig(),
            }
            sess = self._sessions[params.sessionId]

        # Init or reuse agent
        agent = sess.get("agent")
        if agent is None:
            model_name = os.getenv("MINI_SWE_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
            try:
                import json

                model_kwargs = json.loads(os.getenv("MINI_SWE_MODEL_KWARGS", "{}"))
                if not isinstance(model_kwargs, dict):
                    model_kwargs = {}
            except Exception:
                model_kwargs = {}
            loop = asyncio.get_running_loop()
            agent, err = _create_streaming_mini_agent(
                client=self._client,
                session_id=params.sessionId,
                cwd=sess.get("cwd") or os.getcwd(),
                model_name=model_name,
                model_kwargs=model_kwargs,
                loop=loop,
                ext_config=sess["config"],
            )
            if err:
                await self._client.sessionUpdate(
                    SessionNotification(
                        sessionId=params.sessionId,
                        update=AgentMessageChunk(
                            sessionUpdate="agent_message_chunk",
                            content=TextContentBlock(
                                type="text",
                                text=(
                                    "mini-swe-agent load error: "
                                    + err
                                    + "\nPlease install mini-swe-agent or its dependencies in the configured venv."
                                ),
                            ),
                        ),
                    )
                )
                return PromptResponse(stopReason="end_turn")
            sess["agent"] = agent

        # Mode is controlled entirely client-side via requestPermission behavior; no control blocks are parsed.

        # Initialize conversation on first task
        if not sess.get("task"):
            # Build task
            task_parts: list[str] = []
            for block in params.prompt:
                btype = getattr(block, "type", None)
                if btype == "text":
                    text = getattr(block, "text", "")
                    if text and not text.strip().startswith("[[MODE:"):
                        task_parts.append(str(text))
            task = "\n".join(task_parts).strip() or "Help me with the current repository."
            sess["task"] = task
            agent.extra_template_vars |= {"task": task}
            agent.messages = []
            # Seed templates without emitting updates
            agent._emit_updates = False  # type: ignore[attr-defined]
            agent.add_message("system", agent.render_template(agent.config.system_template))
            agent.add_message("user", agent.render_template(agent.config.instance_template))
            agent._emit_updates = True  # type: ignore[attr-defined]

        # Decide the source of the next action
        try:
            if sess["config"].mode == "human":
                # Expect a bash command from the client
                cmd = self._extract_code_from_blocks(params.prompt)
                if not cmd:
                    # Ask user to provide a command and return
                    await self._client.sessionUpdate(
                        SessionNotification(
                            sessionId=params.sessionId,
                            update=AgentMessageChunk(
                                sessionUpdate="agent_message_chunk",
                                content=TextContentBlock(type="text", text="Human mode: please submit a bash command."),
                            ),
                        )
                    )
                    return PromptResponse(stopReason="end_turn")
                # Fabricate assistant message with the command
                msg_content = f"\n```bash\n{cmd}\n```"
                agent.add_message("assistant", msg_content)
                response = {"content": msg_content}
            else:
                # Query the model in a worker thread to keep the event loop free
                response = await asyncio.to_thread(agent.query)
                # Send cost hint after each model call
                try:
                    agent._send_cost_hint()  # type: ignore[attr-defined]
                except Exception:
                    pass

            # Execute and record observation in worker thread
            await asyncio.to_thread(agent.get_observation, response)
        except getattr(agent, "_NonTerminatingException") as e:  # type: ignore[misc]
            agent.add_message("user", str(e))
        except getattr(agent, "_Submitted") as e:  # type: ignore[misc]
            final_message = str(e)
            agent.add_message("user", final_message)
            # Ask for confirmation / new task if configured
            if sess["config"].confirm_exit:
                await self._client.sessionUpdate(
                    SessionNotification(
                        sessionId=params.sessionId,
                        update=AgentMessageChunk(
                            sessionUpdate="agent_message_chunk",
                            content=TextContentBlock(
                                type="text",
                                text=(
                                    "Agent finished. Type a new task in the next message to continue, or do nothing to end."
                                ),
                            ),
                        ),
                    )
                )
                # Reset task so that next prompt can set a new one
                sess["task"] = None
        except getattr(agent, "_LimitsExceeded") as e:  # type: ignore[misc]
            agent.add_message("user", f"Limits exceeded: {e}")
        except Exception as e:
            # Surface unexpected errors to the client to avoid silent waits
            await self._client.sessionUpdate(
                SessionNotification(
                    sessionId=params.sessionId,
                    update=AgentMessageChunk(
                        sessionUpdate="agent_message_chunk",
                        content=TextContentBlock(type="text", text=f"Error while processing: {e}"),
                    ),
                )
            )

        return PromptResponse(stopReason="end_turn")

    async def cancel(self, _params: CancelNotification) -> None:
        return None


async def main() -> None:
    reader, writer = await stdio_streams()
    AgentSideConnection(lambda client: MiniSweACPAgent(client), writer, reader)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
