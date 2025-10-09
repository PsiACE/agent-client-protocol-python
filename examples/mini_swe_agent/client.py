import asyncio
import os
import queue
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Optional


from rich.spinner import Spinner
from rich.text import Text
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static, TextArea

from acp import (
    Client,
    PROTOCOL_VERSION,
    ClientSideConnection,
    InitializeRequest,
    NewSessionRequest,
    PromptRequest,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SessionNotification,
    SetSessionModeRequest,
)
from acp.schema import (
    AgentMessageChunk,
    AgentThoughtChunk,
    AllowedOutcome,
    ContentToolCallContent,
    PermissionOption,
    TextContentBlock,
    ToolCallStart,
    ToolCallProgress,
    UserMessageChunk,
)
from acp.stdio import _WritePipeProtocol


MODE = Literal["confirm", "yolo", "human"]


@dataclass
class UIMessage:
    role: str  # "assistant" or "user"
    content: str


def _messages_to_steps(messages: list[UIMessage]) -> list[list[UIMessage]]:
    steps: list[list[UIMessage]] = []
    current: list[UIMessage] = []
    for m in messages:
        current.append(m)
        if m.role == "user":
            steps.append(current)
            current = []
    if current:
        steps.append(current)
    return steps


class SmartInputContainer(Container):
    def __init__(self, app: "TextualMiniSweClient"):
        super().__init__(classes="smart-input-container")
        self._app = app
        self._multiline_mode = False
        self.can_focus = True
        self.display = False

        self.pending_prompt: Optional[str] = None
        self._input_event = threading.Event()
        self._input_result: Optional[str] = None

        self._header_display = Static(id="input-header-display", classes="message-header input-request-header")
        self._hint_text = Static(classes="hint-text")
        self._single_input = Input(placeholder="Type your input...")
        self._multi_input = TextArea(show_line_numbers=False, classes="multi-input")
        self._input_elements_container = Vertical(
            self._header_display,
            self._hint_text,
            self._single_input,
            self._multi_input,
            classes="message-container",
        )

    def compose(self) -> ComposeResult:
        yield self._input_elements_container

    def on_mount(self) -> None:
        self._multi_input.display = False
        self._update_mode_display()

    def on_focus(self) -> None:
        if self._multiline_mode:
            self._multi_input.focus()
        else:
            self._single_input.focus()

    def request_input(self, prompt: str) -> str:
        self._input_event.clear()
        self._input_result = None
        self.pending_prompt = prompt
        self._header_display.update(prompt)
        self._update_mode_display()
        # If we're already on the Textual thread, call directly; otherwise marshal.
        if getattr(self._app, "_thread_id", None) == threading.get_ident():
            self._app.update_content()
        else:
            self._app.call_from_thread(self._app.update_content)
        self._input_event.wait()
        return self._input_result or ""

    def _complete_input(self, input_text: str):
        self._input_result = input_text
        self.pending_prompt = None
        self.display = False
        self._single_input.value = ""
        self._multi_input.text = ""
        self._multiline_mode = False
        self._update_mode_display()
        self._app.update_content()
        # Reset scroll position to bottom
        self._app._vscroll.scroll_y = 0
        self._input_event.set()

    def action_toggle_mode(self) -> None:
        if self.pending_prompt is None or self._multiline_mode:
            return
        self._multiline_mode = True
        self._update_mode_display()
        self.on_focus()

    def _update_mode_display(self) -> None:
        if self._multiline_mode:
            self._multi_input.text = self._single_input.value
            self._single_input.display = False
            self._multi_input.display = True
            self._hint_text.update(
                "[reverse][bold][$accent] Ctrl+D [/][/][/] to submit, [reverse][bold][$accent] Tab [/][/][/] to switch focus with other controls"
            )
        else:
            self._hint_text.update(
                "[reverse][bold][$accent] Enter [/][/][/] to submit, [reverse][bold][$accent] Ctrl+T [/][/][/] to switch to multi-line input, [reverse][bold][$accent] Tab [/][/][/] to switch focus with other controls",
            )
            self._multi_input.display = False
            self._single_input.display = True

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not self._multiline_mode:
            text = event.input.value.strip()
            self._complete_input(text)

    def on_key(self, event: Key) -> None:
        if event.key == "ctrl+t" and not self._multiline_mode:
            event.prevent_default()
            self.action_toggle_mode()
            return
        if self._multiline_mode and event.key == "ctrl+d":
            event.prevent_default()
            self._complete_input(self._multi_input.text.strip())
            return
        if event.key == "escape":
            event.prevent_default()
            self.can_focus = False
            self._app.set_focus(None)
            return


class MiniSweClientImpl(Client):
    def __init__(self, app: "TextualMiniSweClient") -> None:
        self._app = app

    async def sessionUpdate(self, params: SessionNotification) -> None:
        upd = params.update

        def _post(msg: UIMessage) -> None:
            if getattr(self._app, "_thread_id", None) == threading.get_ident():
                self._app.enqueue_message(msg)
                self._app.on_message_added()
            else:
                self._app.call_from_thread(lambda: (self._app.enqueue_message(msg), self._app.on_message_added()))

        if isinstance(upd, AgentMessageChunk):
            # agent message
            txt = _content_to_text(upd.content)
            _post(UIMessage("assistant", txt))
        elif isinstance(upd, UserMessageChunk):
            txt = _content_to_text(upd.content)
            _post(UIMessage("user", txt))
        elif isinstance(upd, AgentThoughtChunk):
            # agent thought chunk (informational)
            txt = _content_to_text(upd.content)
            _post(UIMessage("assistant", f"[thought]\n{txt}"))
        elif isinstance(upd, ToolCallStart):
            # tool call start → record structured state
            self._app._update_tool_call(
                upd.toolCallId, title=upd.title or "", status=upd.status or "pending", content=upd.content
            )
            self._app.call_from_thread(self._app.update_content)
        elif isinstance(upd, ToolCallProgress):
            # tool call update → update structured state
            self._app._update_tool_call(upd.toolCallId, status=upd.status, content=upd.content)
            self._app.call_from_thread(self._app.update_content)

    async def requestPermission(self, params: RequestPermissionRequest) -> RequestPermissionResponse:
        # Respect client-side mode shortcuts
        mode = self._app.mode
        if mode == "yolo":
            return RequestPermissionResponse(outcome=AllowedOutcome(outcome="selected", optionId="allow-once"))
        # Prompt user for decision
        prompt = "Approve tool call? Press Enter to allow once, type 'n' to reject"
        ans = self._app.input_container.request_input(prompt).strip().lower()
        if ans in ("", "y", "yes"):
            return RequestPermissionResponse(outcome=AllowedOutcome(outcome="selected", optionId="allow-once"))
        return RequestPermissionResponse(outcome=AllowedOutcome(outcome="selected", optionId="reject-once"))

    # Optional features not used in this example
    async def writeTextFile(self, params):
        return None

    async def readTextFile(self, params):
        return None


def _content_to_text(content) -> str:
    if hasattr(content, "text"):
        return str(content.text)
    return str(content)


class TextualMiniSweClient(App):
    BINDINGS = [
        Binding("right,l", "next_step", "Step++", tooltip="Show next step of the agent"),
        Binding("left,h", "previous_step", "Step--", tooltip="Show previous step of the agent"),
        Binding("0", "first_step", "Step=0", tooltip="Show first step of the agent", show=False),
        Binding("$", "last_step", "Step=-1", tooltip="Show last step of the agent", show=False),
        Binding("j,down", "scroll_down", "Scroll down", show=False),
        Binding("k,up", "scroll_up", "Scroll up", show=False),
        Binding("q,ctrl+q", "quit", "Quit", tooltip="Quit the agent"),
        Binding("y,ctrl+y", "yolo", "YOLO mode", tooltip="Switch to YOLO Mode (LM actions will execute immediately)"),
        Binding(
            "c",
            "confirm",
            "CONFIRM mode",
            tooltip="Switch to Confirm Mode (LM proposes commands and you confirm/reject them)",
        ),
        Binding("u,ctrl+u", "human", "HUMAN mode", tooltip="Switch to Human Mode (you can now type commands directly)"),
        Binding("enter", "continue_step", "Next"),
        Binding("f1,question_mark", "toggle_help_panel", "Help", tooltip="Show help"),
    ]

    def __init__(self) -> None:
        # Load CSS
        css_path = os.environ.get(
            "MSWEA_MINI_STYLE_PATH",
            str(
                Path(__file__).resolve().parents[2]
                / "reference"
                / "mini-swe-agent"
                / "src"
                / "minisweagent"
                / "config"
                / "mini.tcss"
            ),
        )
        try:
            self.__class__.CSS = Path(css_path).read_text()
        except Exception:
            self.__class__.CSS = ""
        super().__init__()
        self.mode: MODE = "confirm"
        self._vscroll = VerticalScroll()
        self.input_container = SmartInputContainer(self)
        self.messages: list[UIMessage] = []
        self._spinner = Spinner("dots")
        self.agent_state: Literal["UNINITIALIZED", "RUNNING", "AWAITING_INPUT", "STOPPED"] = "UNINITIALIZED"
        self._bg_loop: Optional[asyncio.AbstractEventLoop] = None
        self._bg_thread: Optional[threading.Thread] = None
        self._conn: Optional[ClientSideConnection] = None
        self._session_id: Optional[str] = None
        self._pending_human_command: Optional[str] = None
        self._outbox: "queue.Queue[list[TextContentBlock]]" = queue.Queue()
        # Pagination and metrics
        self._i_step: int = 0
        self.n_steps: int = 1
        # Structured state for tool calls and plan
        self._tool_calls: dict[str, dict] = {}
        self._plan: list[dict] = []
        self._ask_new_task_pending = False

    # --- Textual lifecycle ---

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main"):
            with self._vscroll:
                with Vertical(id="content"):
                    pass
            yield self.input_container
        yield Footer()

    def on_mount(self) -> None:
        self.agent_state = "RUNNING"
        self.update_content()
        self.set_interval(1 / 8, self._update_headers)
        # Ask for initial task without blocking UI
        threading.Thread(target=self._ask_initial_task, daemon=True).start()

    def _ask_initial_task(self) -> None:
        task = self.input_container.request_input("Enter your task for mini-swe-agent:")
        blocks = [TextContentBlock(type="text", text=task)]
        self._outbox.put(blocks)
        self._start_connection_thread()

    def on_unmount(self) -> None:
        if self._bg_loop:
            try:
                self._bg_loop.call_soon_threadsafe(self._bg_loop.stop)
            except Exception:
                pass

    # --- Backend comms ---

    def _start_connection_thread(self) -> None:
        """Start a background thread running the ACP connection event loop."""

        def _runner() -> None:
            loop = asyncio.new_event_loop()
            self._bg_loop = loop
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_connection())

        t = threading.Thread(target=_runner, daemon=True)
        t.start()
        self._bg_thread = t

    async def _open_acp_streams_from_env(self) -> tuple[Optional[asyncio.StreamReader], Optional[asyncio.StreamWriter]]:
        """If launched via duet, open ACP streams from inherited FDs; else return (None, None)."""
        read_fd_s = os.environ.get("MSWEA_READ_FD")
        write_fd_s = os.environ.get("MSWEA_WRITE_FD")
        if not read_fd_s or not write_fd_s:
            return None, None
        read_fd = int(read_fd_s)
        write_fd = int(write_fd_s)
        loop = asyncio.get_running_loop()
        # Reader
        reader = asyncio.StreamReader()
        reader_proto = asyncio.StreamReaderProtocol(reader)
        r_file = os.fdopen(read_fd, "rb", buffering=0)
        await loop.connect_read_pipe(lambda: reader_proto, r_file)
        # Writer
        write_proto = _WritePipeProtocol()
        w_file = os.fdopen(write_fd, "wb", buffering=0)
        transport, _ = await loop.connect_write_pipe(lambda: write_proto, w_file)
        writer = asyncio.StreamWriter(transport, write_proto, None, loop)
        return reader, writer

    async def _run_connection(self) -> None:
        """Run the ACP client connection using FDs provided by duet; do not fallback."""
        reader, writer = await self._open_acp_streams_from_env()
        if reader is None or writer is None:  # type: ignore[truthy-bool]
            # Do not fallback; inform user and stop
            self.call_from_thread(
                lambda: (
                    self.enqueue_message(
                        UIMessage(
                            "assistant",
                            "Communication endpoints not provided. Please launch via examples/mini_swe_agent/duet.py",
                        )
                    ),
                    self.on_message_added(),
                )
            )
            self.agent_state = "STOPPED"
            return

        self._conn = ClientSideConnection(lambda _agent: MiniSweClientImpl(self), writer, reader)
        try:
            resp = await self._conn.initialize(InitializeRequest(protocolVersion=PROTOCOL_VERSION))
            self.call_from_thread(
                lambda: (
                    self.enqueue_message(UIMessage("assistant", f"Initialized v{resp.protocolVersion}")),
                    self.on_message_added(),
                )
            )
            new_sess = await self._conn.newSession(NewSessionRequest(mcpServers=[], cwd=os.getcwd()))
            self._session_id = new_sess.sessionId
            self.call_from_thread(
                lambda: (
                    self.enqueue_message(UIMessage("assistant", f"Session {self._session_id} created")),
                    self.on_message_added(),
                )
            )
        except Exception as e:
            self.call_from_thread(
                lambda: (
                    self.enqueue_message(UIMessage("assistant", f"ACP connect error: {e}")),
                    self.on_message_added(),
                )
            )
            self.agent_state = "STOPPED"
            return

        # Autostep loop: take queued prompts and send; if none and mode != human, keep stepping
        while self.agent_state != "STOPPED":
            blocks: list[TextContentBlock]
            try:
                blocks = self._outbox.get_nowait()
            except queue.Empty:
                # Auto-advance a step when not in human mode and we're not awaiting input
                if self.mode != "human" and self.input_container.pending_prompt is None:
                    blocks = []
                else:
                    await asyncio.sleep(0.05)
                    continue
            # Send prompt turn
            try:
                result = await self._conn.prompt(PromptRequest(sessionId=self._session_id, prompt=blocks))
                # Minimal finish/new task UX: after each stopReason, if not human and idle, offer new task
                if (
                    self.mode != "human"
                    and not self._ask_new_task_pending
                    and self.input_container.pending_prompt is None
                ):
                    self._ask_new_task_pending = True

                    def _ask_new():
                        task = self.input_container.request_input(
                            "Turn complete. Type a new task or press Enter to continue:"
                        )
                        if task.strip():
                            self._outbox.put([TextContentBlock(type="text", text=task)])
                        else:
                            self._outbox.put([])
                        self._ask_new_task_pending = False

                    threading.Thread(target=_ask_new, daemon=True).start()
            except Exception as e:
                # Break on connection shutdowns to stop background thread cleanly
                msg = str(e)
                if isinstance(e, (BrokenPipeError, ConnectionResetError)) or "Broken pipe" in msg or "closed" in msg:
                    self.agent_state = "STOPPED"
                    break
                self.call_from_thread(lambda: self.enqueue_message(UIMessage("assistant", f"prompt error: {e}")))
            # Tiny delay to avoid busy-looping
            await asyncio.sleep(0.05)

    def send_human_command(self, cmd: str) -> None:
        if not cmd.strip():
            return
        code = f"```bash\n{cmd.strip()}\n```"
        self._outbox.put([TextContentBlock(type="text", text=code)])

    # --- UI updates ---

    def enqueue_message(self, msg: UIMessage) -> None:
        self.messages.append(msg)

    def on_message_added(self) -> None:
        auto_follow = self._vscroll.scroll_y <= 1 and self._i_step == self.n_steps - 1
        # recompute step pages
        items = _messages_to_steps(self.messages)
        self.n_steps = max(1, len(items))
        self.update_content()
        if auto_follow:
            self.action_last_step()

    # --- Structured state helpers ---

    def _update_tool_call(
        self, tool_id: str, *, title: Optional[str] = None, status: Optional[str] = None, content=None
    ) -> None:
        tc = self._tool_calls.get(tool_id, {"toolCallId": tool_id, "title": "", "status": "pending", "content": []})
        if title is not None:
            tc["title"] = title
        if status is not None:
            tc["status"] = status
        if content:
            # Append any text content blocks
            texts = []
            for c in content:
                if isinstance(c, ContentToolCallContent) and getattr(c.content, "type", None) == "text":
                    texts.append(getattr(c.content, "text", ""))
            if texts:
                tc.setdefault("content", []).append("\n".join(texts))
        self._tool_calls[tool_id] = tc

    def update_content(self) -> None:
        container = self.query_one("#content", Vertical)
        container.remove_children()
        if not self.messages:
            container.mount(Static("Waiting for agent…"))
            return
        items = _messages_to_steps(self.messages)
        page = items[self._i_step] if items else []
        for m in page[-400:]:
            message_container = Vertical(classes="message-container")
            container.mount(message_container)
            role = m.role.replace("assistant", "mini-swe-agent").upper()
            message_container.mount(Static(role, classes="message-header"))
            message_container.mount(Static(Text(m.content, no_wrap=False), classes="message-content"))
        # Render structured tool calls at the end of the page
        if self._tool_calls:
            tc_container = Vertical(classes="message-container")
            container.mount(tc_container)
            tc_container.mount(Static("TOOL CALLS", classes="message-header"))
            for tcid, tc in self._tool_calls.items():
                block = Vertical(classes="message-content")
                tc_container.mount(block)
                status = tc.get("status", "")
                title = tc.get("title", "")
                block.mount(Static(Text(f"[TOOL] {title} — {status}", no_wrap=False)))
                for chunk in tc.get("content", []) or []:
                    block.mount(Static(Text(chunk, no_wrap=False)))
        if self.input_container.pending_prompt is not None:
            self.agent_state = "AWAITING_INPUT"
        self.input_container.display = (
            self.input_container.pending_prompt is not None and self._i_step == len(items) - 1
        )
        if self.input_container.display:
            self.input_container.on_focus()
        self._update_headers()
        self.refresh()

    def _update_headers(self) -> None:
        status_text = self.agent_state
        if self.agent_state == "RUNNING":
            spinner_frame = str(self._spinner.render(time.time())).strip()
            status_text = f"{self.agent_state} {spinner_frame}"
        self.title = f"Step {self._i_step + 1}/{self.n_steps} - {status_text}"
        try:
            self.query_one("Header").set_class(self.agent_state == "RUNNING", "running")
        except NoMatches:
            pass

    # --- Actions ---

    # --- Pagination helpers ---

    @property
    def i_step(self) -> int:
        return self._i_step

    @i_step.setter
    def i_step(self, value: int) -> None:
        if value != self._i_step:
            self._i_step = max(0, min(value, self.n_steps - 1))
            self._vscroll.scroll_to(y=0, animate=False)
            self.update_content()

    # --- Actions ---

    def action_next_step(self) -> None:
        self.i_step += 1

    def action_previous_step(self) -> None:
        self.i_step -= 1

    def action_first_step(self) -> None:
        self.i_step = 0

    def action_last_step(self) -> None:
        self.i_step = self.n_steps - 1

    def action_scroll_down(self) -> None:
        self._vscroll.scroll_to(y=self._vscroll.scroll_target_y + 15)

    def action_scroll_up(self) -> None:
        self._vscroll.scroll_to(y=self._vscroll.scroll_target_y - 15)

    def _set_agent_mode_async(self, mode_id: str) -> None:
        if not self._conn or not self._session_id or not self._bg_loop:
            return

        def _schedule() -> None:
            try:
                self._bg_loop.create_task(
                    self._conn.setSessionMode(SetSessionModeRequest(sessionId=self._session_id, modeId=mode_id))
                )
            except Exception:
                pass

        try:
            self._bg_loop.call_soon_threadsafe(_schedule)
        except Exception:
            pass

    def action_yolo(self):
        self.mode = "yolo"
        self._set_agent_mode_async("yolo")
        if self.input_container.pending_prompt is not None:
            self.input_container._complete_input("")
        self.notify("YOLO mode enabled")

    def action_confirm(self):
        self.mode = "confirm"
        self._set_agent_mode_async("confirm")
        if self.input_container.pending_prompt is not None:
            self.input_container._complete_input("")
        self.notify("Confirm mode enabled")

    def action_human(self):
        self.mode = "human"
        self._set_agent_mode_async("human")

        # Ask for a command asynchronously to avoid blocking UI
        def _ask():
            cmd = self.input_container.request_input("Type a bash command to run:")
            if cmd.strip():
                self.send_human_command(cmd)

        threading.Thread(target=_ask, daemon=True).start()
        self.notify("Human mode: commands will be executed as you submit them")

    def action_continue_step(self):
        # For non-human modes, enqueue an empty turn to advance one step.
        if self.mode != "human":
            self._outbox.put([])
            return

        # For human, prompt for next command.
        def _ask():
            cmd = self.input_container.request_input("Type a bash command to run:")
            if cmd.strip():
                self.send_human_command(cmd)

        threading.Thread(target=_ask, daemon=True).start()

    def action_toggle_help_panel(self) -> None:
        if self.query("HelpPanel"):
            self.action_hide_help_panel()
        else:
            self.action_show_help_panel()


def main() -> None:
    app = TextualMiniSweClient()
    app.run()


if __name__ == "__main__":
    main()
