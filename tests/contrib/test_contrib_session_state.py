from __future__ import annotations

import pytest

from acp.contrib.session_state import SessionAccumulator
from acp.schema import (
    AgentMessageChunk,
    AgentPlanUpdate,
    AvailableCommandsUpdate,
    ContentToolCallContent,
    CurrentModeUpdate,
    PlanEntry,
    SessionNotification,
    TextContentBlock,
    ToolCallProgress,
    ToolCallStart,
    UserMessageChunk,
)


def notification(session_id: str, update):
    return SessionNotification(session_id=session_id, update=update)


def test_session_accumulator_merges_tool_calls():
    acc = SessionAccumulator()
    start = ToolCallStart(
        session_update="tool_call",
        tool_call_id="call-1",
        title="Read file",
        status="in_progress",
    )
    acc.apply(notification("s", start))
    progress = ToolCallProgress(
        session_update="tool_call_update",
        tool_call_id="call-1",
        status="completed",
        content=[
            ContentToolCallContent(
                type="content",
                content=TextContentBlock(type="text", text="Done"),
            )
        ],
    )
    snapshot = acc.apply(notification("s", progress))
    tool = snapshot.tool_calls["call-1"]
    assert tool.status == "completed"
    assert tool.title == "Read file"
    assert tool.content and tool.content[0].content.text == "Done"


def test_session_accumulator_records_plan_and_mode():
    acc = SessionAccumulator()
    acc.apply(
        notification(
            "s",
            AgentPlanUpdate(
                session_update="plan",
                entries=[
                    PlanEntry(content="Step 1", priority="medium", status="pending"),
                ],
            ),
        )
    )
    snapshot = acc.apply(
        notification("s", CurrentModeUpdate(session_update="current_mode_update", current_mode_id="coding"))
    )
    assert snapshot.plan_entries[0].content == "Step 1"
    assert snapshot.current_mode_id == "coding"


def test_session_accumulator_tracks_messages_and_commands():
    acc = SessionAccumulator()
    acc.apply(
        notification(
            "s",
            AvailableCommandsUpdate(
                session_update="available_commands_update",
                available_commands=[],
            ),
        )
    )
    acc.apply(
        notification(
            "s",
            UserMessageChunk(
                session_update="user_message_chunk",
                content=TextContentBlock(type="text", text="Hello"),
            ),
        )
    )
    acc.apply(
        notification(
            "s",
            AgentMessageChunk(
                session_update="agent_message_chunk",
                content=TextContentBlock(type="text", text="Hi!"),
            ),
        )
    )
    snapshot = acc.snapshot()
    user_content = snapshot.user_messages[0].content
    agent_content = snapshot.agent_messages[0].content
    assert isinstance(user_content, TextContentBlock)
    assert isinstance(agent_content, TextContentBlock)
    assert user_content.text == "Hello"
    assert agent_content.text == "Hi!"


def test_session_accumulator_auto_resets_on_new_session():
    acc = SessionAccumulator()
    acc.apply(
        notification(
            "s1",
            ToolCallStart(
                session_update="tool_call",
                tool_call_id="call-1",
                title="First",
            ),
        )
    )
    acc.apply(
        notification(
            "s2",
            ToolCallStart(
                session_update="tool_call",
                tool_call_id="call-2",
                title="Second",
            ),
        )
    )

    snapshot = acc.snapshot()
    assert snapshot.session_id == "s2"
    assert "call-1" not in snapshot.tool_calls
    assert "call-2" in snapshot.tool_calls


def test_session_accumulator_rejects_cross_session_when_auto_reset_disabled():
    acc = SessionAccumulator(auto_reset_on_session_change=False)
    acc.apply(
        notification(
            "s1",
            ToolCallStart(
                session_update="tool_call",
                tool_call_id="call-1",
                title="First",
            ),
        )
    )
    with pytest.raises(ValueError):
        acc.apply(
            notification(
                "s2",
                ToolCallStart(
                    session_update="tool_call",
                    tool_call_id="call-2",
                    title="Second",
                ),
            )
        )
