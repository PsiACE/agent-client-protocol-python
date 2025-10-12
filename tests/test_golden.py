from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

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
