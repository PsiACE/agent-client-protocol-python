# Generated from schema/schema.json. Do not edit by hand.
# Schema ref: refs/tags/v0.10.3

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel as _BaseModel, Field, RootModel, ConfigDict

PermissionOptionKind = Literal["allow_once", "allow_always", "reject_once", "reject_always"]
PlanEntryPriority = Literal["high", "medium", "low"]
PlanEntryStatus = Literal["pending", "in_progress", "completed"]
StopReason = Literal["end_turn", "max_tokens", "max_turn_requests", "refusal", "cancelled"]
ToolCallStatus = Literal["pending", "in_progress", "completed", "failed"]
ToolKind = Literal["read", "edit", "delete", "move", "search", "execute", "think", "fetch", "switch_mode", "other"]


class BaseModel(_BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    def __getattr__(self, item: str) -> Any:
        if item.lower() != item:
            snake_cased = "".join("_" + c.lower() if c.isupper() and i > 0 else c.lower() for i, c in enumerate(item))
            return getattr(self, snake_cased)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{item}'")


class Jsonrpc(Enum):
    field_2_0 = "2.0"


class AuthMethod(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Optional description providing more details about this authentication method.
    description: Annotated[
        Optional[str],
        Field(description="Optional description providing more details about this authentication method."),
    ] = None
    # Unique identifier for this authentication method.
    id: Annotated[str, Field(description="Unique identifier for this authentication method.")]
    # Human-readable name of the authentication method.
    name: Annotated[str, Field(description="Human-readable name of the authentication method.")]


class AuthenticateRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The ID of the authentication method to use.
    # Must be one of the methods advertised in the initialize response.
    method_id: Annotated[
        str,
        Field(
            alias="methodId",
            description="The ID of the authentication method to use.\nMust be one of the methods advertised in the initialize response.",
        ),
    ]


class AuthenticateResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None


class BlobResourceContents(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    blob: str
    mime_type: Annotated[Optional[str], Field(alias="mimeType")] = None
    uri: str


class CreateTerminalResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The unique identifier for the created terminal.
    terminal_id: Annotated[
        str,
        Field(
            alias="terminalId",
            description="The unique identifier for the created terminal.",
        ),
    ]


class Diff(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The new content after modification.
    new_text: Annotated[str, Field(alias="newText", description="The new content after modification.")]
    # The original content (None for new files).
    old_text: Annotated[
        Optional[str],
        Field(alias="oldText", description="The original content (None for new files)."),
    ] = None
    # The file path being modified.
    path: Annotated[str, Field(description="The file path being modified.")]


class EnvVariable(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The name of the environment variable.
    name: Annotated[str, Field(description="The name of the environment variable.")]
    # The value to set for the environment variable.
    value: Annotated[str, Field(description="The value to set for the environment variable.")]


class FileSystemCapability(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Whether the Client supports `fs/read_text_file` requests.
    read_text_file: Annotated[
        Optional[bool],
        Field(
            alias="readTextFile",
            description="Whether the Client supports `fs/read_text_file` requests.",
        ),
    ] = False
    # Whether the Client supports `fs/write_text_file` requests.
    write_text_file: Annotated[
        Optional[bool],
        Field(
            alias="writeTextFile",
            description="Whether the Client supports `fs/write_text_file` requests.",
        ),
    ] = False


class HttpHeader(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The name of the HTTP header.
    name: Annotated[str, Field(description="The name of the HTTP header.")]
    # The value to set for the HTTP header.
    value: Annotated[str, Field(description="The value to set for the HTTP header.")]


class Implementation(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Intended for programmatic or logical use, but can be used as a display
    # name fallback if title isn’t present.
    name: Annotated[
        str,
        Field(
            description="Intended for programmatic or logical use, but can be used as a display\nname fallback if title isn’t present."
        ),
    ]
    # Intended for UI and end-user contexts — optimized to be human-readable
    # and easily understood.
    #
    # If not provided, the name should be used for display.
    title: Annotated[
        Optional[str],
        Field(
            description="Intended for UI and end-user contexts — optimized to be human-readable\nand easily understood.\n\nIf not provided, the name should be used for display."
        ),
    ] = None
    # Version of the implementation. Can be displayed to the user or used
    # for debugging or metrics purposes. (e.g. "1.0.0").
    version: Annotated[
        str,
        Field(
            description='Version of the implementation. Can be displayed to the user or used\nfor debugging or metrics purposes. (e.g. "1.0.0").'
        ),
    ]


class KillTerminalCommandResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None


class ListSessionsRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Opaque cursor token from a previous response's nextCursor field for cursor-based pagination
    cursor: Annotated[
        Optional[str],
        Field(
            description="Opaque cursor token from a previous response's nextCursor field for cursor-based pagination"
        ),
    ] = None
    # Filter sessions by working directory. Must be an absolute path.
    cwd: Annotated[
        Optional[str],
        Field(description="Filter sessions by working directory. Must be an absolute path."),
    ] = None


class McpCapabilities(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Agent supports [`McpServer::Http`].
    http: Annotated[Optional[bool], Field(description="Agent supports [`McpServer::Http`].")] = False
    # Agent supports [`McpServer::Sse`].
    sse: Annotated[Optional[bool], Field(description="Agent supports [`McpServer::Sse`].")] = False


class McpServerHttp(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # HTTP headers to set when making requests to the MCP server.
    headers: Annotated[
        List[HttpHeader],
        Field(description="HTTP headers to set when making requests to the MCP server."),
    ]
    # Human-readable name identifying this MCP server.
    name: Annotated[str, Field(description="Human-readable name identifying this MCP server.")]
    # URL to the MCP server.
    url: Annotated[str, Field(description="URL to the MCP server.")]


class McpServerSse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # HTTP headers to set when making requests to the MCP server.
    headers: Annotated[
        List[HttpHeader],
        Field(description="HTTP headers to set when making requests to the MCP server."),
    ]
    # Human-readable name identifying this MCP server.
    name: Annotated[str, Field(description="Human-readable name identifying this MCP server.")]
    # URL to the MCP server.
    url: Annotated[str, Field(description="URL to the MCP server.")]


class McpServerStdio(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Command-line arguments to pass to the MCP server.
    args: Annotated[
        List[str],
        Field(description="Command-line arguments to pass to the MCP server."),
    ]
    # Path to the MCP server executable.
    command: Annotated[str, Field(description="Path to the MCP server executable.")]
    # Environment variables to set when launching the MCP server.
    env: Annotated[
        List[EnvVariable],
        Field(description="Environment variables to set when launching the MCP server."),
    ]
    # Human-readable name identifying this MCP server.
    name: Annotated[str, Field(description="Human-readable name identifying this MCP server.")]


class ModelInfo(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Optional description of the model.
    description: Annotated[Optional[str], Field(description="Optional description of the model.")] = None
    # Unique identifier for the model.
    model_id: Annotated[str, Field(alias="modelId", description="Unique identifier for the model.")]
    # Human-readable name of the model.
    name: Annotated[str, Field(description="Human-readable name of the model.")]


class PromptCapabilities(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Agent supports [`ContentBlock::Audio`].
    audio: Annotated[Optional[bool], Field(description="Agent supports [`ContentBlock::Audio`].")] = False
    # Agent supports embedded context in `session/prompt` requests.
    #
    # When enabled, the Client is allowed to include [`ContentBlock::Resource`]
    # in prompt requests for pieces of context that are referenced in the message.
    embedded_context: Annotated[
        Optional[bool],
        Field(
            alias="embeddedContext",
            description="Agent supports embedded context in `session/prompt` requests.\n\nWhen enabled, the Client is allowed to include [`ContentBlock::Resource`]\nin prompt requests for pieces of context that are referenced in the message.",
        ),
    ] = False
    # Agent supports [`ContentBlock::Image`].
    image: Annotated[Optional[bool], Field(description="Agent supports [`ContentBlock::Image`].")] = False


class ReadTextFileResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    content: str


class ReleaseTerminalResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None


class DeniedOutcome(BaseModel):
    outcome: Literal["cancelled"]


class Role(Enum):
    assistant = "assistant"
    user = "user"


class SelectedPermissionOutcome(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The ID of the option the user selected.
    option_id: Annotated[
        str,
        Field(alias="optionId", description="The ID of the option the user selected."),
    ]


class SessionForkCapabilities(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None


class SessionInfo(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The working directory for this session. Must be an absolute path.
    cwd: Annotated[
        str,
        Field(description="The working directory for this session. Must be an absolute path."),
    ]
    # Unique identifier for the session
    session_id: Annotated[str, Field(alias="sessionId", description="Unique identifier for the session")]
    # Human-readable title for the session
    title: Annotated[Optional[str], Field(description="Human-readable title for the session")] = None
    # ISO 8601 timestamp of last activity
    updated_at: Annotated[
        Optional[str],
        Field(alias="updatedAt", description="ISO 8601 timestamp of last activity"),
    ] = None


class _SessionInfoUpdate(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Human-readable title for the session. Set to null to clear.
    title: Annotated[
        Optional[str],
        Field(description="Human-readable title for the session. Set to null to clear."),
    ] = None
    # ISO 8601 timestamp of last activity. Set to null to clear.
    updated_at: Annotated[
        Optional[str],
        Field(
            alias="updatedAt",
            description="ISO 8601 timestamp of last activity. Set to null to clear.",
        ),
    ] = None


class SessionListCapabilities(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None


class SessionModelState(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The set of models that the Agent can use
    available_models: Annotated[
        List[ModelInfo],
        Field(
            alias="availableModels",
            description="The set of models that the Agent can use",
        ),
    ]
    # The current model the Agent is in.
    current_model_id: Annotated[
        str,
        Field(alias="currentModelId", description="The current model the Agent is in."),
    ]


class SessionResumeCapabilities(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None


class SessionInfoUpdate(_SessionInfoUpdate):
    session_update: Annotated[Literal["session_info_update"], Field(alias="sessionUpdate")]


class SetSessionModeRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The ID of the mode to set.
    mode_id: Annotated[str, Field(alias="modeId", description="The ID of the mode to set.")]
    # The ID of the session to set the mode for.
    session_id: Annotated[
        str,
        Field(alias="sessionId", description="The ID of the session to set the mode for."),
    ]


class SetSessionModeResponse(BaseModel):
    field_meta: Annotated[Optional[Dict[str, Any]], Field(alias="_meta")] = None


class SetSessionModelRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The ID of the model to set.
    model_id: Annotated[str, Field(alias="modelId", description="The ID of the model to set.")]
    # The ID of the session to set the model for.
    session_id: Annotated[
        str,
        Field(alias="sessionId", description="The ID of the session to set the model for."),
    ]


class SetSessionModelResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None


class Terminal(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    terminal_id: Annotated[str, Field(alias="terminalId")]


class TerminalExitStatus(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The process exit code (may be null if terminated by signal).
    exit_code: Annotated[
        Optional[int],
        Field(
            alias="exitCode",
            description="The process exit code (may be null if terminated by signal).",
            ge=0,
        ),
    ] = None
    # The signal that terminated the process (may be null if exited normally).
    signal: Annotated[
        Optional[str],
        Field(description="The signal that terminated the process (may be null if exited normally)."),
    ] = None


class TerminalOutputRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The session ID for this request.
    session_id: Annotated[str, Field(alias="sessionId", description="The session ID for this request.")]
    # The ID of the terminal to get output from.
    terminal_id: Annotated[
        str,
        Field(alias="terminalId", description="The ID of the terminal to get output from."),
    ]


class TerminalOutputResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Exit status if the command has completed.
    exit_status: Annotated[
        Optional[TerminalExitStatus],
        Field(alias="exitStatus", description="Exit status if the command has completed."),
    ] = None
    # The terminal output captured so far.
    output: Annotated[str, Field(description="The terminal output captured so far.")]
    # Whether the output was truncated due to byte limits.
    truncated: Annotated[bool, Field(description="Whether the output was truncated due to byte limits.")]


class TextResourceContents(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    mime_type: Annotated[Optional[str], Field(alias="mimeType")] = None
    text: str
    uri: str


class FileEditToolCallContent(Diff):
    type: Literal["diff"]


class TerminalToolCallContent(Terminal):
    type: Literal["terminal"]


class ToolCallLocation(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Optional line number within the file.
    line: Annotated[Optional[int], Field(description="Optional line number within the file.", ge=0)] = None
    # The file path being accessed or modified.
    path: Annotated[str, Field(description="The file path being accessed or modified.")]


class UnstructuredCommandInput(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # A hint to display when the input hasn't been provided yet
    hint: Annotated[
        str,
        Field(description="A hint to display when the input hasn't been provided yet"),
    ]


class WaitForTerminalExitRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The session ID for this request.
    session_id: Annotated[str, Field(alias="sessionId", description="The session ID for this request.")]
    # The ID of the terminal to wait for.
    terminal_id: Annotated[
        str,
        Field(alias="terminalId", description="The ID of the terminal to wait for."),
    ]


class WaitForTerminalExitResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The process exit code (may be null if terminated by signal).
    exit_code: Annotated[
        Optional[int],
        Field(
            alias="exitCode",
            description="The process exit code (may be null if terminated by signal).",
            ge=0,
        ),
    ] = None
    # The signal that terminated the process (may be null if exited normally).
    signal: Annotated[
        Optional[str],
        Field(description="The signal that terminated the process (may be null if exited normally)."),
    ] = None


class WriteTextFileRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The text content to write to the file.
    content: Annotated[str, Field(description="The text content to write to the file.")]
    # Absolute path to the file to write.
    path: Annotated[str, Field(description="Absolute path to the file to write.")]
    # The session ID for this request.
    session_id: Annotated[str, Field(alias="sessionId", description="The session ID for this request.")]


class WriteTextFileResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None


class Annotations(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    audience: Optional[List[Role]] = None
    last_modified: Annotated[Optional[str], Field(alias="lastModified")] = None
    priority: Optional[float] = None


class AudioContent(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    annotations: Optional[Annotations] = None
    data: str
    mime_type: Annotated[str, Field(alias="mimeType")]


class AvailableCommandInput(RootModel[UnstructuredCommandInput]):
    # The input specification for a command.
    root: Annotated[
        UnstructuredCommandInput,
        Field(description="The input specification for a command."),
    ]


class CancelNotification(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The ID of the session to cancel operations for.
    session_id: Annotated[
        str,
        Field(
            alias="sessionId",
            description="The ID of the session to cancel operations for.",
        ),
    ]


class CancelRequestNotification(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The ID of the request to cancel.
    request_id: Annotated[
        Optional[Union[int, str]],
        Field(alias="requestId", description="The ID of the request to cancel."),
    ] = None


class ClientCapabilities(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # File system capabilities supported by the client.
    # Determines which file operations the agent can request.
    fs: Annotated[
        Optional[FileSystemCapability],
        Field(
            description="File system capabilities supported by the client.\nDetermines which file operations the agent can request."
        ),
    ] = FileSystemCapability()
    # Whether the Client support all `terminal/*` methods.
    terminal: Annotated[
        Optional[bool],
        Field(description="Whether the Client support all `terminal/*` methods."),
    ] = False


class ClientNotification(BaseModel):
    method: str
    params: Optional[Union[CancelNotification, Any]] = None


class AudioContentBlock(AudioContent):
    type: Literal["audio"]


class CreateTerminalRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Array of command arguments.
    args: Annotated[Optional[List[str]], Field(description="Array of command arguments.")] = None
    # The command to execute.
    command: Annotated[str, Field(description="The command to execute.")]
    # Working directory for the command (absolute path).
    cwd: Annotated[
        Optional[str],
        Field(description="Working directory for the command (absolute path)."),
    ] = None
    # Environment variables for the command.
    env: Annotated[
        Optional[List[EnvVariable]],
        Field(description="Environment variables for the command."),
    ] = None
    # Maximum number of output bytes to retain.
    #
    # When the limit is exceeded, the Client truncates from the beginning of the output
    # to stay within the limit.
    #
    # The Client MUST ensure truncation happens at a character boundary to maintain valid
    # string output, even if this means the retained output is slightly less than the
    # specified limit.
    output_byte_limit: Annotated[
        Optional[int],
        Field(
            alias="outputByteLimit",
            description="Maximum number of output bytes to retain.\n\nWhen the limit is exceeded, the Client truncates from the beginning of the output\nto stay within the limit.\n\nThe Client MUST ensure truncation happens at a character boundary to maintain valid\nstring output, even if this means the retained output is slightly less than the\nspecified limit.",
            ge=0,
        ),
    ] = None
    # The session ID for this request.
    session_id: Annotated[str, Field(alias="sessionId", description="The session ID for this request.")]


class _CurrentModeUpdate(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The ID of the current mode
    current_mode_id: Annotated[str, Field(alias="currentModeId", description="The ID of the current mode")]


class Error(BaseModel):
    # A number indicating the error type that occurred.
    # This must be an integer as defined in the JSON-RPC specification.
    code: Annotated[
        int,
        Field(
            description="A number indicating the error type that occurred.\nThis must be an integer as defined in the JSON-RPC specification."
        ),
    ]
    # Optional primitive or structured value that contains additional information about the error.
    # This may include debugging information or context-specific details.
    data: Annotated[
        Optional[Any],
        Field(
            description="Optional primitive or structured value that contains additional information about the error.\nThis may include debugging information or context-specific details."
        ),
    ] = None
    # A string providing a short description of the error.
    # The message should be limited to a concise single sentence.
    message: Annotated[
        str,
        Field(
            description="A string providing a short description of the error.\nThe message should be limited to a concise single sentence."
        ),
    ]


class ImageContent(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    annotations: Optional[Annotations] = None
    data: str
    mime_type: Annotated[str, Field(alias="mimeType")]
    uri: Optional[str] = None


class InitializeRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Capabilities supported by the client.
    client_capabilities: Annotated[
        Optional[ClientCapabilities],
        Field(
            alias="clientCapabilities",
            description="Capabilities supported by the client.",
        ),
    ] = ClientCapabilities()
    # Information about the Client name and version sent to the Agent.
    #
    # Note: in future versions of the protocol, this will be required.
    client_info: Annotated[
        Optional[Implementation],
        Field(
            alias="clientInfo",
            description="Information about the Client name and version sent to the Agent.\n\nNote: in future versions of the protocol, this will be required.",
        ),
    ] = None
    # The latest protocol version supported by the client.
    protocol_version: Annotated[
        int,
        Field(
            alias="protocolVersion",
            description="The latest protocol version supported by the client.",
            ge=0,
            le=65535,
        ),
    ]


class KillTerminalCommandRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The session ID for this request.
    session_id: Annotated[str, Field(alias="sessionId", description="The session ID for this request.")]
    # The ID of the terminal to kill.
    terminal_id: Annotated[str, Field(alias="terminalId", description="The ID of the terminal to kill.")]


class ListSessionsResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Opaque cursor token. If present, pass this in the next request's cursor parameter
    # to fetch the next page. If absent, there are no more results.
    next_cursor: Annotated[
        Optional[str],
        Field(
            alias="nextCursor",
            description="Opaque cursor token. If present, pass this in the next request's cursor parameter\nto fetch the next page. If absent, there are no more results.",
        ),
    ] = None
    # Array of session information objects
    sessions: Annotated[List[SessionInfo], Field(description="Array of session information objects")]


class HttpMcpServer(McpServerHttp):
    type: Literal["http"]


class SseMcpServer(McpServerSse):
    type: Literal["sse"]


class NewSessionRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The working directory for this session. Must be an absolute path.
    cwd: Annotated[
        str,
        Field(description="The working directory for this session. Must be an absolute path."),
    ]
    # List of MCP (Model Context Protocol) servers the agent should connect to.
    mcp_servers: Annotated[
        List[Union[HttpMcpServer, SseMcpServer, McpServerStdio]],
        Field(
            alias="mcpServers",
            description="List of MCP (Model Context Protocol) servers the agent should connect to.",
        ),
    ]


class PermissionOption(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Hint about the nature of this permission option.
    kind: Annotated[PermissionOptionKind, Field(description="Hint about the nature of this permission option.")]
    # Human-readable label to display to the user.
    name: Annotated[str, Field(description="Human-readable label to display to the user.")]
    # Unique identifier for this permission option.
    option_id: Annotated[
        str,
        Field(
            alias="optionId",
            description="Unique identifier for this permission option.",
        ),
    ]


class PlanEntry(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Human-readable description of what this task aims to accomplish.
    content: Annotated[
        str,
        Field(description="Human-readable description of what this task aims to accomplish."),
    ]
    # The relative importance of this task.
    # Used to indicate which tasks are most critical to the overall goal.
    priority: Annotated[
        PlanEntryPriority,
        Field(
            description="The relative importance of this task.\nUsed to indicate which tasks are most critical to the overall goal."
        ),
    ]
    # Current execution status of this task.
    status: Annotated[PlanEntryStatus, Field(description="Current execution status of this task.")]


class PromptResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Indicates why the agent stopped processing the turn.
    stop_reason: Annotated[
        StopReason,
        Field(
            alias="stopReason",
            description="Indicates why the agent stopped processing the turn.",
        ),
    ]


class ReadTextFileRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Maximum number of lines to read.
    limit: Annotated[Optional[int], Field(description="Maximum number of lines to read.", ge=0)] = None
    # Line number to start reading from (1-based).
    line: Annotated[
        Optional[int],
        Field(description="Line number to start reading from (1-based).", ge=0),
    ] = None
    # Absolute path to the file to read.
    path: Annotated[str, Field(description="Absolute path to the file to read.")]
    # The session ID for this request.
    session_id: Annotated[str, Field(alias="sessionId", description="The session ID for this request.")]


class ReleaseTerminalRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The session ID for this request.
    session_id: Annotated[str, Field(alias="sessionId", description="The session ID for this request.")]
    # The ID of the terminal to release.
    terminal_id: Annotated[str, Field(alias="terminalId", description="The ID of the terminal to release.")]


class AllowedOutcome(SelectedPermissionOutcome):
    outcome: Literal["selected"]


class RequestPermissionResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The user's decision on the permission request.
    outcome: Annotated[
        Union[DeniedOutcome, AllowedOutcome],
        Field(
            description="The user's decision on the permission request.",
            discriminator="outcome",
        ),
    ]


class ResourceLink(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    annotations: Optional[Annotations] = None
    description: Optional[str] = None
    mime_type: Annotated[Optional[str], Field(alias="mimeType")] = None
    name: str
    size: Optional[int] = None
    title: Optional[str] = None
    uri: str


class ResumeSessionRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The working directory for this session.
    cwd: Annotated[str, Field(description="The working directory for this session.")]
    # List of MCP servers to connect to for this session.
    mcp_servers: Annotated[
        Optional[List[Union[HttpMcpServer, SseMcpServer, McpServerStdio]]],
        Field(
            alias="mcpServers",
            description="List of MCP servers to connect to for this session.",
        ),
    ] = None
    # The ID of the session to resume.
    session_id: Annotated[str, Field(alias="sessionId", description="The ID of the session to resume.")]


class SessionCapabilities(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # **UNSTABLE**
    #
    # This capability is not part of the spec yet, and may be removed or changed at any point.
    #
    # Whether the agent supports `session/fork`.
    fork: Annotated[
        Optional[SessionForkCapabilities],
        Field(
            description="**UNSTABLE**\n\nThis capability is not part of the spec yet, and may be removed or changed at any point.\n\nWhether the agent supports `session/fork`."
        ),
    ] = None
    # **UNSTABLE**
    #
    # This capability is not part of the spec yet, and may be removed or changed at any point.
    #
    # Whether the agent supports `session/list`.
    list: Annotated[
        Optional[SessionListCapabilities],
        Field(
            description="**UNSTABLE**\n\nThis capability is not part of the spec yet, and may be removed or changed at any point.\n\nWhether the agent supports `session/list`."
        ),
    ] = None
    # **UNSTABLE**
    #
    # This capability is not part of the spec yet, and may be removed or changed at any point.
    #
    # Whether the agent supports `session/resume`.
    resume: Annotated[
        Optional[SessionResumeCapabilities],
        Field(
            description="**UNSTABLE**\n\nThis capability is not part of the spec yet, and may be removed or changed at any point.\n\nWhether the agent supports `session/resume`."
        ),
    ] = None


class SessionMode(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    description: Optional[str] = None
    # Unique identifier for a Session Mode.
    id: Annotated[str, Field(description="Unique identifier for a Session Mode.")]
    name: str


class SessionModeState(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The set of modes that the Agent can operate in
    available_modes: Annotated[
        List[SessionMode],
        Field(
            alias="availableModes",
            description="The set of modes that the Agent can operate in",
        ),
    ]
    # The current mode the Agent is in.
    current_mode_id: Annotated[
        str,
        Field(alias="currentModeId", description="The current mode the Agent is in."),
    ]


class CurrentModeUpdate(_CurrentModeUpdate):
    session_update: Annotated[Literal["current_mode_update"], Field(alias="sessionUpdate")]


class TextContent(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    annotations: Optional[Annotations] = None
    text: str


class AgentCapabilities(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Whether the agent supports `session/load`.
    load_session: Annotated[
        Optional[bool],
        Field(
            alias="loadSession",
            description="Whether the agent supports `session/load`.",
        ),
    ] = False
    # MCP capabilities supported by the agent.
    mcp_capabilities: Annotated[
        Optional[McpCapabilities],
        Field(
            alias="mcpCapabilities",
            description="MCP capabilities supported by the agent.",
        ),
    ] = McpCapabilities()
    # Prompt capabilities supported by the agent.
    prompt_capabilities: Annotated[
        Optional[PromptCapabilities],
        Field(
            alias="promptCapabilities",
            description="Prompt capabilities supported by the agent.",
        ),
    ] = PromptCapabilities()
    session_capabilities: Annotated[Optional[SessionCapabilities], Field(alias="sessionCapabilities")] = (
        SessionCapabilities()
    )


class AgentErrorMessage(BaseModel):
    error: Error
    # JSON RPC Request Id
    #
    # An identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]
    #
    # The Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.
    #
    # [1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.
    #
    # [2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions.
    id: Annotated[
        Optional[Union[int, str]],
        Field(
            description="JSON RPC Request Id\n\nAn identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]\n\nThe Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.\n\n[1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.\n\n[2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions."
        ),
    ] = None


class AvailableCommand(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Human-readable description of what the command does.
    description: Annotated[str, Field(description="Human-readable description of what the command does.")]
    # Input for the command if required
    input: Annotated[
        Optional[AvailableCommandInput],
        Field(description="Input for the command if required"),
    ] = None
    # Command name (e.g., `create_plan`, `research_codebase`).
    name: Annotated[
        str,
        Field(description="Command name (e.g., `create_plan`, `research_codebase`)."),
    ]


class _AvailableCommandsUpdate(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Commands the agent can execute
    available_commands: Annotated[
        List[AvailableCommand],
        Field(alias="availableCommands", description="Commands the agent can execute"),
    ]


class ClientResponseMessage(BaseModel):
    # JSON RPC Request Id
    #
    # An identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]
    #
    # The Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.
    #
    # [1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.
    #
    # [2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions.
    id: Annotated[
        Optional[Union[int, str]],
        Field(
            description="JSON RPC Request Id\n\nAn identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]\n\nThe Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.\n\n[1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.\n\n[2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions."
        ),
    ] = None
    # All possible responses that a client can send to an agent.
    #
    # This enum is used internally for routing RPC responses. You typically won't need
    # to use this directly - the responses are handled automatically by the connection.
    #
    # These are responses to the corresponding `AgentRequest` variants.
    result: Annotated[
        Union[
            WriteTextFileResponse,
            ReadTextFileResponse,
            RequestPermissionResponse,
            CreateTerminalResponse,
            TerminalOutputResponse,
            ReleaseTerminalResponse,
            WaitForTerminalExitResponse,
            KillTerminalCommandResponse,
            Any,
        ],
        Field(
            description="All possible responses that a client can send to an agent.\n\nThis enum is used internally for routing RPC responses. You typically won't need\nto use this directly - the responses are handled automatically by the connection.\n\nThese are responses to the corresponding `AgentRequest` variants."
        ),
    ]


class ClientErrorMessage(BaseModel):
    error: Error
    # JSON RPC Request Id
    #
    # An identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]
    #
    # The Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.
    #
    # [1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.
    #
    # [2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions.
    id: Annotated[
        Optional[Union[int, str]],
        Field(
            description="JSON RPC Request Id\n\nAn identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]\n\nThe Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.\n\n[1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.\n\n[2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions."
        ),
    ] = None


class ClientResponse(RootModel[Union[ClientResponseMessage, ClientErrorMessage]]):
    root: Union[ClientResponseMessage, ClientErrorMessage]


class TextContentBlock(TextContent):
    type: Literal["text"]


class ImageContentBlock(ImageContent):
    type: Literal["image"]


class ResourceContentBlock(ResourceLink):
    type: Literal["resource_link"]


class EmbeddedResource(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    annotations: Optional[Annotations] = None
    # Resource content that can be embedded in a message.
    resource: Annotated[
        Union[TextResourceContents, BlobResourceContents],
        Field(description="Resource content that can be embedded in a message."),
    ]


class ForkSessionRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The working directory for this session.
    cwd: Annotated[str, Field(description="The working directory for this session.")]
    # List of MCP servers to connect to for this session.
    mcp_servers: Annotated[
        Optional[List[Union[HttpMcpServer, SseMcpServer, McpServerStdio]]],
        Field(
            alias="mcpServers",
            description="List of MCP servers to connect to for this session.",
        ),
    ] = None
    # The ID of the session to fork.
    session_id: Annotated[str, Field(alias="sessionId", description="The ID of the session to fork.")]


class ForkSessionResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # **UNSTABLE**
    #
    # This capability is not part of the spec yet, and may be removed or changed at any point.
    #
    # Initial model state if supported by the Agent
    models: Annotated[
        Optional[SessionModelState],
        Field(
            description="**UNSTABLE**\n\nThis capability is not part of the spec yet, and may be removed or changed at any point.\n\nInitial model state if supported by the Agent"
        ),
    ] = None
    # Initial mode state if supported by the Agent
    #
    # See protocol docs: [Session Modes](https://agentclientprotocol.com/protocol/session-modes)
    modes: Annotated[
        Optional[SessionModeState],
        Field(
            description="Initial mode state if supported by the Agent\n\nSee protocol docs: [Session Modes](https://agentclientprotocol.com/protocol/session-modes)"
        ),
    ] = None
    # Unique identifier for the newly created forked session.
    session_id: Annotated[
        str,
        Field(
            alias="sessionId",
            description="Unique identifier for the newly created forked session.",
        ),
    ]


class InitializeResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Capabilities supported by the agent.
    agent_capabilities: Annotated[
        Optional[AgentCapabilities],
        Field(
            alias="agentCapabilities",
            description="Capabilities supported by the agent.",
        ),
    ] = AgentCapabilities()
    # Information about the Agent name and version sent to the Client.
    #
    # Note: in future versions of the protocol, this will be required.
    agent_info: Annotated[
        Optional[Implementation],
        Field(
            alias="agentInfo",
            description="Information about the Agent name and version sent to the Client.\n\nNote: in future versions of the protocol, this will be required.",
        ),
    ] = None
    # Authentication methods supported by the agent.
    auth_methods: Annotated[
        Optional[List[AuthMethod]],
        Field(
            alias="authMethods",
            description="Authentication methods supported by the agent.",
        ),
    ] = []
    # The protocol version the client specified if supported by the agent,
    # or the latest protocol version supported by the agent.
    #
    # The client should disconnect, if it doesn't support this version.
    protocol_version: Annotated[
        int,
        Field(
            alias="protocolVersion",
            description="The protocol version the client specified if supported by the agent,\nor the latest protocol version supported by the agent.\n\nThe client should disconnect, if it doesn't support this version.",
            ge=0,
            le=65535,
        ),
    ]


class LoadSessionRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The working directory for this session.
    cwd: Annotated[str, Field(description="The working directory for this session.")]
    # List of MCP servers to connect to for this session.
    mcp_servers: Annotated[
        List[Union[HttpMcpServer, SseMcpServer, McpServerStdio]],
        Field(
            alias="mcpServers",
            description="List of MCP servers to connect to for this session.",
        ),
    ]
    # The ID of the session to load.
    session_id: Annotated[str, Field(alias="sessionId", description="The ID of the session to load.")]


class LoadSessionResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # **UNSTABLE**
    #
    # This capability is not part of the spec yet, and may be removed or changed at any point.
    #
    # Initial model state if supported by the Agent
    models: Annotated[
        Optional[SessionModelState],
        Field(
            description="**UNSTABLE**\n\nThis capability is not part of the spec yet, and may be removed or changed at any point.\n\nInitial model state if supported by the Agent"
        ),
    ] = None
    # Initial mode state if supported by the Agent
    #
    # See protocol docs: [Session Modes](https://agentclientprotocol.com/protocol/session-modes)
    modes: Annotated[
        Optional[SessionModeState],
        Field(
            description="Initial mode state if supported by the Agent\n\nSee protocol docs: [Session Modes](https://agentclientprotocol.com/protocol/session-modes)"
        ),
    ] = None


class NewSessionResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # **UNSTABLE**
    #
    # This capability is not part of the spec yet, and may be removed or changed at any point.
    #
    # Initial model state if supported by the Agent
    models: Annotated[
        Optional[SessionModelState],
        Field(
            description="**UNSTABLE**\n\nThis capability is not part of the spec yet, and may be removed or changed at any point.\n\nInitial model state if supported by the Agent"
        ),
    ] = None
    # Initial mode state if supported by the Agent
    #
    # See protocol docs: [Session Modes](https://agentclientprotocol.com/protocol/session-modes)
    modes: Annotated[
        Optional[SessionModeState],
        Field(
            description="Initial mode state if supported by the Agent\n\nSee protocol docs: [Session Modes](https://agentclientprotocol.com/protocol/session-modes)"
        ),
    ] = None
    # Unique identifier for the created session.
    #
    # Used in all subsequent requests for this conversation.
    session_id: Annotated[
        str,
        Field(
            alias="sessionId",
            description="Unique identifier for the created session.\n\nUsed in all subsequent requests for this conversation.",
        ),
    ]


class Plan(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The list of tasks to be accomplished.
    #
    # When updating a plan, the agent must send a complete list of all entries
    # with their current status. The client replaces the entire plan with each update.
    entries: Annotated[
        List[PlanEntry],
        Field(
            description="The list of tasks to be accomplished.\n\nWhen updating a plan, the agent must send a complete list of all entries\nwith their current status. The client replaces the entire plan with each update."
        ),
    ]


class ResumeSessionResponse(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # **UNSTABLE**
    #
    # This capability is not part of the spec yet, and may be removed or changed at any point.
    #
    # Initial model state if supported by the Agent
    models: Annotated[
        Optional[SessionModelState],
        Field(
            description="**UNSTABLE**\n\nThis capability is not part of the spec yet, and may be removed or changed at any point.\n\nInitial model state if supported by the Agent"
        ),
    ] = None
    # Initial mode state if supported by the Agent
    #
    # See protocol docs: [Session Modes](https://agentclientprotocol.com/protocol/session-modes)
    modes: Annotated[
        Optional[SessionModeState],
        Field(
            description="Initial mode state if supported by the Agent\n\nSee protocol docs: [Session Modes](https://agentclientprotocol.com/protocol/session-modes)"
        ),
    ] = None


class AgentPlanUpdate(Plan):
    session_update: Annotated[Literal["plan"], Field(alias="sessionUpdate")]


class AvailableCommandsUpdate(_AvailableCommandsUpdate):
    session_update: Annotated[Literal["available_commands_update"], Field(alias="sessionUpdate")]


class AgentResponseMessage(BaseModel):
    # JSON RPC Request Id
    #
    # An identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]
    #
    # The Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.
    #
    # [1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.
    #
    # [2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions.
    id: Annotated[
        Optional[Union[int, str]],
        Field(
            description="JSON RPC Request Id\n\nAn identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]\n\nThe Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.\n\n[1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.\n\n[2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions."
        ),
    ] = None
    # All possible responses that an agent can send to a client.
    #
    # This enum is used internally for routing RPC responses. You typically won't need
    # to use this directly - the responses are handled automatically by the connection.
    #
    # These are responses to the corresponding `ClientRequest` variants.
    result: Annotated[
        Union[
            InitializeResponse,
            AuthenticateResponse,
            NewSessionResponse,
            LoadSessionResponse,
            ListSessionsResponse,
            ForkSessionResponse,
            ResumeSessionResponse,
            SetSessionModeResponse,
            PromptResponse,
            SetSessionModelResponse,
            Any,
        ],
        Field(
            description="All possible responses that an agent can send to a client.\n\nThis enum is used internally for routing RPC responses. You typically won't need\nto use this directly - the responses are handled automatically by the connection.\n\nThese are responses to the corresponding `ClientRequest` variants."
        ),
    ]


class AgentResponse(RootModel[Union[AgentResponseMessage, AgentErrorMessage]]):
    root: Union[AgentResponseMessage, AgentErrorMessage]


class EmbeddedResourceContentBlock(EmbeddedResource):
    type: Literal["resource"]


class ContentChunk(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # A single item of content
    content: Annotated[
        Union[
            TextContentBlock, ImageContentBlock, AudioContentBlock, ResourceContentBlock, EmbeddedResourceContentBlock
        ],
        Field(description="A single item of content", discriminator="type"),
    ]


class PromptRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The blocks of content that compose the user's message.
    #
    # As a baseline, the Agent MUST support [`ContentBlock::Text`] and [`ContentBlock::ResourceLink`],
    # while other variants are optionally enabled via [`PromptCapabilities`].
    #
    # The Client MUST adapt its interface according to [`PromptCapabilities`].
    #
    # The client MAY include referenced pieces of context as either
    # [`ContentBlock::Resource`] or [`ContentBlock::ResourceLink`].
    #
    # When available, [`ContentBlock::Resource`] is preferred
    # as it avoids extra round-trips and allows the message to include
    # pieces of context from sources the agent may not have access to.
    prompt: Annotated[
        List[
            Union[
                TextContentBlock,
                ImageContentBlock,
                AudioContentBlock,
                ResourceContentBlock,
                EmbeddedResourceContentBlock,
            ]
        ],
        Field(
            description="The blocks of content that compose the user's message.\n\nAs a baseline, the Agent MUST support [`ContentBlock::Text`] and [`ContentBlock::ResourceLink`],\nwhile other variants are optionally enabled via [`PromptCapabilities`].\n\nThe Client MUST adapt its interface according to [`PromptCapabilities`].\n\nThe client MAY include referenced pieces of context as either\n[`ContentBlock::Resource`] or [`ContentBlock::ResourceLink`].\n\nWhen available, [`ContentBlock::Resource`] is preferred\nas it avoids extra round-trips and allows the message to include\npieces of context from sources the agent may not have access to."
        ),
    ]
    # The ID of the session to send this user message to
    session_id: Annotated[
        str,
        Field(
            alias="sessionId",
            description="The ID of the session to send this user message to",
        ),
    ]


class UserMessageChunk(ContentChunk):
    session_update: Annotated[Literal["user_message_chunk"], Field(alias="sessionUpdate")]


class AgentMessageChunk(ContentChunk):
    session_update: Annotated[Literal["agent_message_chunk"], Field(alias="sessionUpdate")]


class AgentThoughtChunk(ContentChunk):
    session_update: Annotated[Literal["agent_thought_chunk"], Field(alias="sessionUpdate")]


class ClientRequest(BaseModel):
    # JSON RPC Request Id
    #
    # An identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]
    #
    # The Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.
    #
    # [1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.
    #
    # [2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions.
    id: Annotated[
        Optional[Union[int, str]],
        Field(
            description="JSON RPC Request Id\n\nAn identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]\n\nThe Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.\n\n[1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.\n\n[2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions."
        ),
    ] = None
    method: str
    params: Optional[
        Union[
            InitializeRequest,
            AuthenticateRequest,
            NewSessionRequest,
            LoadSessionRequest,
            ListSessionsRequest,
            ForkSessionRequest,
            ResumeSessionRequest,
            SetSessionModeRequest,
            PromptRequest,
            SetSessionModelRequest,
            Any,
        ]
    ] = None


class Content(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The actual content block.
    content: Annotated[
        Union[
            TextContentBlock, ImageContentBlock, AudioContentBlock, ResourceContentBlock, EmbeddedResourceContentBlock
        ],
        Field(description="The actual content block.", discriminator="type"),
    ]


class ContentToolCallContent(Content):
    type: Literal["content"]


class ToolCallUpdate(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Replace the content collection.
    content: Annotated[
        Optional[List[Union[ContentToolCallContent, FileEditToolCallContent, TerminalToolCallContent]]],
        Field(description="Replace the content collection."),
    ] = None
    # Update the tool kind.
    kind: Annotated[Optional[ToolKind], Field(description="Update the tool kind.")] = None
    # Replace the locations collection.
    locations: Annotated[
        Optional[List[ToolCallLocation]],
        Field(description="Replace the locations collection."),
    ] = None
    # Update the raw input.
    raw_input: Annotated[Optional[Any], Field(alias="rawInput", description="Update the raw input.")] = None
    # Update the raw output.
    raw_output: Annotated[Optional[Any], Field(alias="rawOutput", description="Update the raw output.")] = None
    # Update the execution status.
    status: Annotated[Optional[ToolCallStatus], Field(description="Update the execution status.")] = None
    # Update the human-readable title.
    title: Annotated[Optional[str], Field(description="Update the human-readable title.")] = None
    # The ID of the tool call being updated.
    tool_call_id: Annotated[
        str,
        Field(alias="toolCallId", description="The ID of the tool call being updated."),
    ]


class RequestPermissionRequest(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Available permission options for the user to choose from.
    options: Annotated[
        List[PermissionOption],
        Field(description="Available permission options for the user to choose from."),
    ]
    # The session ID for this request.
    session_id: Annotated[str, Field(alias="sessionId", description="The session ID for this request.")]
    # Details about the tool call requiring permission.
    tool_call: Annotated[
        ToolCallUpdate,
        Field(
            alias="toolCall",
            description="Details about the tool call requiring permission.",
        ),
    ]


class ToolCallProgress(ToolCallUpdate):
    session_update: Annotated[Literal["tool_call_update"], Field(alias="sessionUpdate")]


class ToolCall(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # Content produced by the tool call.
    content: Annotated[
        Optional[List[Union[ContentToolCallContent, FileEditToolCallContent, TerminalToolCallContent]]],
        Field(description="Content produced by the tool call."),
    ] = None
    # The category of tool being invoked.
    # Helps clients choose appropriate icons and UI treatment.
    kind: Annotated[
        Optional[ToolKind],
        Field(
            description="The category of tool being invoked.\nHelps clients choose appropriate icons and UI treatment."
        ),
    ] = None
    # File locations affected by this tool call.
    # Enables "follow-along" features in clients.
    locations: Annotated[
        Optional[List[ToolCallLocation]],
        Field(description='File locations affected by this tool call.\nEnables "follow-along" features in clients.'),
    ] = None
    # Raw input parameters sent to the tool.
    raw_input: Annotated[
        Optional[Any],
        Field(alias="rawInput", description="Raw input parameters sent to the tool."),
    ] = None
    # Raw output returned by the tool.
    raw_output: Annotated[
        Optional[Any],
        Field(alias="rawOutput", description="Raw output returned by the tool."),
    ] = None
    # Current execution status of the tool call.
    status: Annotated[Optional[ToolCallStatus], Field(description="Current execution status of the tool call.")] = None
    # Human-readable title describing what the tool is doing.
    title: Annotated[
        str,
        Field(description="Human-readable title describing what the tool is doing."),
    ]
    # Unique identifier for this tool call within the session.
    tool_call_id: Annotated[
        str,
        Field(
            alias="toolCallId",
            description="Unique identifier for this tool call within the session.",
        ),
    ]


class AgentRequest(BaseModel):
    # JSON RPC Request Id
    #
    # An identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]
    #
    # The Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.
    #
    # [1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.
    #
    # [2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions.
    id: Annotated[
        Optional[Union[int, str]],
        Field(
            description="JSON RPC Request Id\n\nAn identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification. The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts [2]\n\nThe Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.\n\n[1] The use of Null as a value for the id member in a Request object is discouraged, because this specification uses a value of Null for Responses with an unknown id. Also, because JSON-RPC 1.0 uses an id value of Null for Notifications this could cause confusion in handling.\n\n[2] Fractional parts may be problematic, since many decimal fractions cannot be represented exactly as binary fractions."
        ),
    ] = None
    method: str
    params: Optional[
        Union[
            WriteTextFileRequest,
            ReadTextFileRequest,
            RequestPermissionRequest,
            CreateTerminalRequest,
            TerminalOutputRequest,
            ReleaseTerminalRequest,
            WaitForTerminalExitRequest,
            KillTerminalCommandRequest,
            Any,
        ]
    ] = None


class ToolCallStart(ToolCall):
    session_update: Annotated[Literal["tool_call"], Field(alias="sessionUpdate")]


class SessionNotification(BaseModel):
    # The _meta property is reserved by ACP to allow clients and agents to attach additional
    # metadata to their interactions. Implementations MUST NOT make assumptions about values at
    # these keys.
    #
    # See protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)
    field_meta: Annotated[
        Optional[Dict[str, Any]],
        Field(
            alias="_meta",
            description="The _meta property is reserved by ACP to allow clients and agents to attach additional\nmetadata to their interactions. Implementations MUST NOT make assumptions about values at\nthese keys.\n\nSee protocol docs: [Extensibility](https://agentclientprotocol.com/protocol/extensibility)",
        ),
    ] = None
    # The ID of the session this update pertains to.
    session_id: Annotated[
        str,
        Field(
            alias="sessionId",
            description="The ID of the session this update pertains to.",
        ),
    ]
    # The actual update content.
    update: Annotated[
        Union[
            UserMessageChunk,
            AgentMessageChunk,
            AgentThoughtChunk,
            ToolCallStart,
            ToolCallProgress,
            AgentPlanUpdate,
            AvailableCommandsUpdate,
            CurrentModeUpdate,
            SessionInfoUpdate,
        ],
        Field(description="The actual update content.", discriminator="session_update"),
    ]


class AgentNotification(BaseModel):
    method: str
    params: Optional[Union[SessionNotification, Any]] = None


# Backwards compatibility aliases
AgentResponse1 = AgentResponseMessage
AgentResponse2 = AgentErrorMessage
ClientResponse1 = ClientResponseMessage
ClientResponse2 = ClientErrorMessage
ContentBlock1 = TextContentBlock
ContentBlock2 = ImageContentBlock
ContentBlock3 = AudioContentBlock
ContentBlock4 = ResourceContentBlock
ContentBlock5 = EmbeddedResourceContentBlock
McpServer1 = HttpMcpServer
McpServer2 = SseMcpServer
RequestPermissionOutcome1 = DeniedOutcome
RequestPermissionOutcome2 = AllowedOutcome
SessionUpdate1 = UserMessageChunk
SessionUpdate2 = AgentMessageChunk
SessionUpdate3 = AgentThoughtChunk
SessionUpdate4 = ToolCallStart
SessionUpdate5 = ToolCallProgress
SessionUpdate6 = AgentPlanUpdate
SessionUpdate7 = AvailableCommandsUpdate
SessionUpdate8 = CurrentModeUpdate
SessionUpdate9 = SessionInfoUpdate
ToolCallContent1 = ContentToolCallContent
ToolCallContent2 = FileEditToolCallContent
ToolCallContent3 = TerminalToolCallContent
StdioMcpServer = McpServerStdio
