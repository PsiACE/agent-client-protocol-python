from __future__ import annotations

from acp.contrib.tool_calls import ToolCallTracker
from acp.schema import ContentToolCallContent, TextContentBlock, ToolCallProgress


def test_tool_call_tracker_generates_ids_and_updates():
    tracker = ToolCallTracker(id_factory=lambda: "generated-id")
    start = tracker.start("external", title="Run command")
    assert start.tool_call_id == "generated-id"
    progress = tracker.progress("external", status="completed")
    assert isinstance(progress, ToolCallProgress)
    assert progress.tool_call_id == "generated-id"
    view = tracker.view("external")
    assert view.status == "completed"


def test_tool_call_tracker_streaming_text_updates_content():
    tracker = ToolCallTracker(id_factory=lambda: "stream-id")
    tracker.start("external", title="Stream", status="in_progress")
    update1 = tracker.append_stream_text("external", "hello")
    assert update1.content is not None
    first_content = update1.content[0]
    assert isinstance(first_content, ContentToolCallContent)
    assert isinstance(first_content.content, TextContentBlock)
    assert first_content.content.text == "hello"
    update2 = tracker.append_stream_text("external", ", world", status="in_progress")
    assert update2.content is not None
    second_content = update2.content[0]
    assert isinstance(second_content, ContentToolCallContent)
    assert isinstance(second_content.content, TextContentBlock)
    assert second_content.content.text == "hello, world"
