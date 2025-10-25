from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from .schema import (
    AgentMessageChunk,
    AgentPlanUpdate,
    AgentThoughtChunk,
    AudioContentBlock,
    AvailableCommand,
    AvailableCommandsUpdate,
    BlobResourceContents,
    ContentToolCallContent,
    CurrentModeUpdate,
    EmbeddedResourceContentBlock,
    FileEditToolCallContent,
    ImageContentBlock,
    PlanEntry,
    PlanEntryPriority,
    PlanEntryStatus,
    ResourceContentBlock,
    SessionNotification,
    TerminalToolCallContent,
    TextContentBlock,
    TextResourceContents,
    ToolCallLocation,
    ToolCallProgress,
    ToolCallStart,
    ToolCallStatus,
    ToolKind,
    UserMessageChunk,
)

ContentBlock = (
    TextContentBlock | ImageContentBlock | AudioContentBlock | ResourceContentBlock | EmbeddedResourceContentBlock
)

SessionUpdate = (
    AgentMessageChunk
    | AgentPlanUpdate
    | AgentThoughtChunk
    | AvailableCommandsUpdate
    | CurrentModeUpdate
    | UserMessageChunk
    | ToolCallStart
    | ToolCallProgress
)

ToolCallContentVariant = ContentToolCallContent | FileEditToolCallContent | TerminalToolCallContent

__all__ = [
    "audio_block",
    "embedded_blob_resource",
    "embedded_text_resource",
    "image_block",
    "plan_entry",
    "resource_block",
    "resource_link_block",
    "session_notification",
    "start_edit_tool_call",
    "start_read_tool_call",
    "start_tool_call",
    "text_block",
    "tool_content",
    "tool_diff_content",
    "tool_terminal_ref",
    "update_agent_message",
    "update_agent_message_text",
    "update_agent_thought",
    "update_agent_thought_text",
    "update_available_commands",
    "update_current_mode",
    "update_plan",
    "update_tool_call",
    "update_user_message",
    "update_user_message_text",
]


def text_block(text: str) -> TextContentBlock:
    return TextContentBlock(type="text", text=text)


def image_block(data: str, mime_type: str, *, uri: str | None = None) -> ImageContentBlock:
    return ImageContentBlock(type="image", data=data, mimeType=mime_type, uri=uri)


def audio_block(data: str, mime_type: str) -> AudioContentBlock:
    return AudioContentBlock(type="audio", data=data, mimeType=mime_type)


def resource_link_block(
    name: str,
    uri: str,
    *,
    mime_type: str | None = None,
    size: int | None = None,
    description: str | None = None,
    title: str | None = None,
) -> ResourceContentBlock:
    return ResourceContentBlock(
        type="resource_link",
        name=name,
        uri=uri,
        mimeType=mime_type,
        size=size,
        description=description,
        title=title,
    )


def embedded_text_resource(uri: str, text: str, *, mime_type: str | None = None) -> TextResourceContents:
    return TextResourceContents(uri=uri, text=text, mimeType=mime_type)


def embedded_blob_resource(uri: str, blob: str, *, mime_type: str | None = None) -> BlobResourceContents:
    return BlobResourceContents(uri=uri, blob=blob, mimeType=mime_type)


def resource_block(
    resource: TextResourceContents | BlobResourceContents,
) -> EmbeddedResourceContentBlock:
    return EmbeddedResourceContentBlock(type="resource", resource=resource)


def tool_content(block: ContentBlock) -> ContentToolCallContent:
    return ContentToolCallContent(type="content", content=block)


def tool_diff_content(path: str, new_text: str, old_text: str | None = None) -> FileEditToolCallContent:
    return FileEditToolCallContent(type="diff", path=path, newText=new_text, oldText=old_text)


def tool_terminal_ref(terminal_id: str) -> TerminalToolCallContent:
    return TerminalToolCallContent(type="terminal", terminalId=terminal_id)


def plan_entry(
    content: str,
    *,
    priority: PlanEntryPriority = "medium",
    status: PlanEntryStatus = "pending",
) -> PlanEntry:
    return PlanEntry(content=content, priority=priority, status=status)


def update_plan(entries: Iterable[PlanEntry]) -> AgentPlanUpdate:
    return AgentPlanUpdate(sessionUpdate="plan", entries=list(entries))


def update_user_message(content: ContentBlock) -> UserMessageChunk:
    return UserMessageChunk(sessionUpdate="user_message_chunk", content=content)


def update_user_message_text(text: str) -> UserMessageChunk:
    return update_user_message(text_block(text))


def update_agent_message(content: ContentBlock) -> AgentMessageChunk:
    return AgentMessageChunk(sessionUpdate="agent_message_chunk", content=content)


def update_agent_message_text(text: str) -> AgentMessageChunk:
    return update_agent_message(text_block(text))


def update_agent_thought(content: ContentBlock) -> AgentThoughtChunk:
    return AgentThoughtChunk(sessionUpdate="agent_thought_chunk", content=content)


def update_agent_thought_text(text: str) -> AgentThoughtChunk:
    return update_agent_thought(text_block(text))


def update_available_commands(commands: Iterable[AvailableCommand]) -> AvailableCommandsUpdate:
    return AvailableCommandsUpdate(
        sessionUpdate="available_commands_update",
        availableCommands=list(commands),
    )


def update_current_mode(current_mode_id: str) -> CurrentModeUpdate:
    return CurrentModeUpdate(sessionUpdate="current_mode_update", currentModeId=current_mode_id)


def session_notification(session_id: str, update: SessionUpdate) -> SessionNotification:
    return SessionNotification(sessionId=session_id, update=update)


def start_tool_call(
    tool_call_id: str,
    title: str,
    *,
    kind: ToolKind | None = None,
    status: ToolCallStatus | None = None,
    content: Sequence[ToolCallContentVariant] | None = None,
    locations: Sequence[ToolCallLocation] | None = None,
    raw_input: Any | None = None,
    raw_output: Any | None = None,
) -> ToolCallStart:
    return ToolCallStart(
        sessionUpdate="tool_call",
        toolCallId=tool_call_id,
        title=title,
        kind=kind,
        status=status,
        content=list(content) if content is not None else None,
        locations=list(locations) if locations is not None else None,
        rawInput=raw_input,
        rawOutput=raw_output,
    )


def start_read_tool_call(
    tool_call_id: str,
    title: str,
    path: str,
    *,
    extra_options: Sequence[ToolCallContentVariant] | None = None,
) -> ToolCallStart:
    content = list(extra_options) if extra_options is not None else None
    locations = [ToolCallLocation(path=path)]
    raw_input = {"path": path}
    return start_tool_call(
        tool_call_id,
        title,
        kind="read",
        status="pending",
        content=content,
        locations=locations,
        raw_input=raw_input,
    )


def start_edit_tool_call(
    tool_call_id: str,
    title: str,
    path: str,
    content: Any,
    *,
    extra_options: Sequence[ToolCallContentVariant] | None = None,
) -> ToolCallStart:
    locations = [ToolCallLocation(path=path)]
    raw_input = {"path": path, "content": content}
    return start_tool_call(
        tool_call_id,
        title,
        kind="edit",
        status="pending",
        content=list(extra_options) if extra_options is not None else None,
        locations=locations,
        raw_input=raw_input,
    )


def update_tool_call(
    tool_call_id: str,
    *,
    title: str | None = None,
    kind: ToolKind | None = None,
    status: ToolCallStatus | None = None,
    content: Sequence[ToolCallContentVariant] | None = None,
    locations: Sequence[ToolCallLocation] | None = None,
    raw_input: Any | None = None,
    raw_output: Any | None = None,
) -> ToolCallProgress:
    return ToolCallProgress(
        sessionUpdate="tool_call_update",
        toolCallId=tool_call_id,
        title=title,
        kind=kind,
        status=status,
        content=list(content) if content is not None else None,
        locations=list(locations) if locations is not None else None,
        rawInput=raw_input,
        rawOutput=raw_output,
    )
