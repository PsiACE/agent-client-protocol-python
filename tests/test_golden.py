from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import BaseModel

from acp import (
    audio_block,
    embedded_blob_resource,
    embedded_text_resource,
    image_block,
    plan_entry,
    resource_block,
    resource_link_block,
    start_edit_tool_call,
    start_read_tool_call,
    start_tool_call,
    text_block,
    tool_content,
    tool_diff_content,
    tool_terminal_ref,
    update_agent_message_text,
    update_agent_thought_text,
    update_plan,
    update_tool_call,
    update_user_message_text,
)
from acp.schema import (
    AgentMessageChunk,
    AgentPlanUpdate,
    AgentThoughtChunk,
    AllowedOutcome,
    AudioContentBlock,
    CancelNotification,
    ContentToolCallContent,
    DeniedOutcome,
    EmbeddedResourceContentBlock,
    FileEditToolCallContent,
    ImageContentBlock,
    InitializeRequest,
    InitializeResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    ReadTextFileRequest,
    ReadTextFileResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    ResourceContentBlock,
    TerminalToolCallContent,
    TextContentBlock,
    ToolCallLocation,
    ToolCallProgress,
    ToolCallStart,
    UserMessageChunk,
    WriteTextFileRequest,
)

GOLDEN_DIR = Path(__file__).parent / "golden"

# Map each golden fixture to the concrete schema model it should conform to.
GOLDEN_CASES: dict[str, type[BaseModel]] = {
    "cancel_notification": CancelNotification,
    "content_audio": AudioContentBlock,
    "content_image": ImageContentBlock,
    "content_resource_blob": EmbeddedResourceContentBlock,
    "content_resource_link": ResourceContentBlock,
    "content_resource_text": EmbeddedResourceContentBlock,
    "content_text": TextContentBlock,
    "fs_read_text_file_request": ReadTextFileRequest,
    "fs_read_text_file_response": ReadTextFileResponse,
    "fs_write_text_file_request": WriteTextFileRequest,
    "initialize_request": InitializeRequest,
    "initialize_response": InitializeResponse,
    "new_session_request": NewSessionRequest,
    "new_session_response": NewSessionResponse,
    "permission_outcome_cancelled": DeniedOutcome,
    "permission_outcome_selected": AllowedOutcome,
    "prompt_request": PromptRequest,
    "request_permission_request": RequestPermissionRequest,
    "request_permission_response_selected": RequestPermissionResponse,
    "session_update_agent_message_chunk": AgentMessageChunk,
    "session_update_agent_thought_chunk": AgentThoughtChunk,
    "session_update_plan": AgentPlanUpdate,
    "session_update_tool_call": ToolCallStart,
    "session_update_tool_call_edit": ToolCallStart,
    "session_update_tool_call_locations_rawinput": ToolCallStart,
    "session_update_tool_call_read": ToolCallStart,
    "session_update_tool_call_update_content": ToolCallProgress,
    "session_update_tool_call_update_more_fields": ToolCallProgress,
    "session_update_user_message_chunk": UserMessageChunk,
    "tool_content_content_text": ContentToolCallContent,
    "tool_content_diff": FileEditToolCallContent,
    "tool_content_diff_no_old": FileEditToolCallContent,
    "tool_content_terminal": TerminalToolCallContent,
}

_PARAMS = tuple(sorted(GOLDEN_CASES.items()))
_PARAM_IDS = [name for name, _ in _PARAMS]

GOLDEN_BUILDERS: dict[str, Callable[[], BaseModel]] = {
    "content_text": lambda: text_block("What's the weather like today?"),
    "content_image": lambda: image_block("iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB...", "image/png"),
    "content_audio": lambda: audio_block("UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAAB...", "audio/wav"),
    "content_resource_text": lambda: resource_block(
        embedded_text_resource(
            "file:///home/user/script.py",
            "def hello():\n    print('Hello, world!')",
            mime_type="text/x-python",
        )
    ),
    "content_resource_blob": lambda: resource_block(
        embedded_blob_resource(
            "file:///home/user/document.pdf",
            "<b64>",
            mime_type="application/pdf",
        )
    ),
    "content_resource_link": lambda: resource_link_block(
        "document.pdf",
        "file:///home/user/document.pdf",
        mime_type="application/pdf",
        size=1_024_000,
    ),
    "tool_content_content_text": lambda: tool_content(text_block("Analysis complete. Found 3 issues.")),
    "tool_content_diff": lambda: tool_diff_content(
        "/home/user/project/src/config.json",
        '{\n  "debug": true\n}',
        '{\n  "debug": false\n}',
    ),
    "tool_content_diff_no_old": lambda: tool_diff_content(
        "/home/user/project/src/config.json",
        '{\n  "debug": true\n}',
    ),
    "tool_content_terminal": lambda: tool_terminal_ref("term_001"),
    "session_update_user_message_chunk": lambda: update_user_message_text("What's the capital of France?"),
    "session_update_agent_message_chunk": lambda: update_agent_message_text("The capital of France is Paris."),
    "session_update_agent_thought_chunk": lambda: update_agent_thought_text("Thinking about best approach..."),
    "session_update_plan": lambda: update_plan([
        plan_entry(
            "Check for syntax errors",
            priority="high",
            status="pending",
        ),
        plan_entry(
            "Identify potential type issues",
            priority="medium",
            status="pending",
        ),
    ]),
    "session_update_tool_call": lambda: start_tool_call(
        "call_001",
        "Reading configuration file",
        kind="read",
        status="pending",
    ),
    "session_update_tool_call_read": lambda: start_read_tool_call(
        "call_001",
        "Reading configuration file",
        "/home/user/project/src/config.json",
    ),
    "session_update_tool_call_edit": lambda: start_edit_tool_call(
        "call_003",
        "Apply edit",
        "/home/user/project/src/config.json",
        "print('hello')",
    ),
    "session_update_tool_call_locations_rawinput": lambda: start_tool_call(
        "call_lr",
        "Tracking file",
        locations=[ToolCallLocation(path="/home/user/project/src/config.json")],
        raw_input={"path": "/home/user/project/src/config.json"},
    ),
    "session_update_tool_call_update_content": lambda: update_tool_call(
        "call_001",
        status="in_progress",
        content=[tool_content(text_block("Found 3 configuration files..."))],
    ),
    "session_update_tool_call_update_more_fields": lambda: update_tool_call(
        "call_010",
        title="Processing changes",
        kind="edit",
        status="completed",
        locations=[ToolCallLocation(path="/home/user/project/src/config.json")],
        raw_input={"path": "/home/user/project/src/config.json"},
        raw_output={"result": "ok"},
        content=[tool_content(text_block("Edit completed."))],
    ),
}

_HELPER_PARAMS = tuple(sorted(GOLDEN_BUILDERS.items()))
_HELPER_IDS = [name for name, _ in _HELPER_PARAMS]


def _load_golden(name: str) -> dict:
    path = GOLDEN_DIR / f"{name}.json"
    return json.loads(path.read_text())


def _dump_model(model: BaseModel) -> dict:
    return model.model_dump(mode="json", by_alias=True, exclude_none=True, exclude_unset=True)


def test_golden_cases_covered() -> None:
    available = {path.stem for path in GOLDEN_DIR.glob("*.json")}
    assert available == set(GOLDEN_CASES), "Add the new golden file to GOLDEN_CASES."


@pytest.mark.parametrize(
    ("name", "model_cls"),
    _PARAMS,
    ids=_PARAM_IDS,
)
def test_json_golden_roundtrip(name: str, model_cls: type[BaseModel]) -> None:
    raw = _load_golden(name)
    model = model_cls.model_validate(raw)
    assert _dump_model(model) == raw


@pytest.mark.parametrize(
    ("name", "builder"),
    _HELPER_PARAMS,
    ids=_HELPER_IDS,
)
def test_helpers_match_golden(name: str, builder: Callable[[], BaseModel]) -> None:
    raw = _load_golden(name)
    model = builder()
    assert isinstance(model, BaseModel)
    assert _dump_model(model) == raw
