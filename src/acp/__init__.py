from typing import Any

from .core import (
    Agent,
    Client,
    RequestError,
    TerminalHandle,
    connect_to_agent,
    run_agent,
)
from .helpers import (
    audio_block,
    embedded_blob_resource,
    embedded_text_resource,
    image_block,
    plan_entry,
    resource_block,
    resource_link_block,
    session_notification,
    start_edit_tool_call,
    start_read_tool_call,
    start_tool_call,
    text_block,
    tool_content,
    tool_diff_content,
    tool_terminal_ref,
    update_agent_message,
    update_agent_message_text,
    update_agent_thought,
    update_agent_thought_text,
    update_plan,
    update_tool_call,
    update_user_message,
    update_user_message_text,
)
from .meta import (
    AGENT_METHODS,
    CLIENT_METHODS,
    PROTOCOL_VERSION,
)
from .schema import (
    AuthenticateRequest,
    AuthenticateResponse,
    CancelNotification,
    CreateTerminalRequest,
    CreateTerminalResponse,
    InitializeRequest,
    InitializeResponse,
    KillTerminalCommandRequest,
    KillTerminalCommandResponse,
    LoadSessionRequest,
    LoadSessionResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    ReleaseTerminalRequest,
    ReleaseTerminalResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SessionNotification,
    SetSessionModelRequest,
    SetSessionModelResponse,
    SetSessionModeRequest,
    SetSessionModeResponse,
    TerminalOutputRequest,
    TerminalOutputResponse,
    WaitForTerminalExitRequest,
    WaitForTerminalExitResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
)
from .stdio import spawn_agent_process, spawn_client_process, spawn_stdio_connection, stdio_streams
from .transports import default_environment, spawn_stdio_transport

_DEPRECATED_NAMES = [
    (
        "AgentSideConnection",
        "acp.core:AgentSideConnection",
        "Using `AgentSideConnection` directly is deprecated, please use `acp.run_agent` instead.",
    ),
    (
        "ClientSideConnection",
        "acp.core:ClientSideConnection",
        "Using `ClientSideConnection` directly is deprecated, please use `acp.connect_to_agent` instead.",
    ),
]

__all__ = [  # noqa: RUF022
    # constants
    "PROTOCOL_VERSION",
    "AGENT_METHODS",
    "CLIENT_METHODS",
    # types
    "InitializeRequest",
    "InitializeResponse",
    "NewSessionRequest",
    "NewSessionResponse",
    "LoadSessionRequest",
    "LoadSessionResponse",
    "AuthenticateRequest",
    "AuthenticateResponse",
    "PromptRequest",
    "PromptResponse",
    "WriteTextFileRequest",
    "WriteTextFileResponse",
    "ReadTextFileRequest",
    "ReadTextFileResponse",
    "RequestPermissionRequest",
    "RequestPermissionResponse",
    "CancelNotification",
    "SessionNotification",
    "SetSessionModeRequest",
    "SetSessionModeResponse",
    "SetSessionModelRequest",
    "SetSessionModelResponse",
    # terminal types
    "CreateTerminalRequest",
    "CreateTerminalResponse",
    "TerminalOutputRequest",
    "TerminalOutputResponse",
    "WaitForTerminalExitRequest",
    "WaitForTerminalExitResponse",
    "KillTerminalCommandRequest",
    "KillTerminalCommandResponse",
    "ReleaseTerminalRequest",
    "ReleaseTerminalResponse",
    # core
    "run_agent",
    "connect_to_agent",
    "RequestError",
    "Agent",
    "Client",
    "TerminalHandle",
    # stdio helper
    "stdio_streams",
    "spawn_stdio_connection",
    "spawn_agent_process",
    "spawn_client_process",
    "default_environment",
    "spawn_stdio_transport",
    # helpers
    "text_block",
    "image_block",
    "audio_block",
    "resource_link_block",
    "embedded_text_resource",
    "embedded_blob_resource",
    "resource_block",
    "tool_content",
    "tool_diff_content",
    "tool_terminal_ref",
    "plan_entry",
    "update_plan",
    "update_user_message",
    "update_user_message_text",
    "update_agent_message",
    "update_agent_message_text",
    "update_agent_thought",
    "update_agent_thought_text",
    "session_notification",
    "start_tool_call",
    "start_read_tool_call",
    "start_edit_tool_call",
    "update_tool_call",
]


def __getattr__(name: str) -> Any:
    import warnings
    from importlib import import_module

    for deprecated_name, new_path, warning in _DEPRECATED_NAMES:
        if name == deprecated_name:
            warnings.warn(warning, DeprecationWarning, stacklevel=2)
            module_name, attr_name = new_path.split(":")
            module = import_module(module_name)
            return getattr(module, attr_name)
    raise AttributeError(f"module {__name__} has no attribute {name}")
