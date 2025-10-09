# Generated from schema/schema.json. Do not edit by hand.
# Schema ref: refs/tags/v0.4.5

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field, RootModel


class AuthenticateRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    methodId: Annotated[
        str,
        Field(
            description="The ID of the authentication method to use.\nMust be one of the methods advertised in the initialize response."
        ),
    ]


class AuthenticateResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None


class CommandInputHint(BaseModel):
    hint: Annotated[
        str,
        Field(description="A hint to display when the input hasn't been provided yet"),
    ]


class AvailableCommandInput(RootModel[CommandInputHint]):
    root: Annotated[
        CommandInputHint,
        Field(description="The input specification for a command."),
    ]


class BlobResourceContents(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    blob: str
    mimeType: Optional[str] = None
    uri: str


class CreateTerminalResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    terminalId: Annotated[str, Field(description="The unique identifier for the created terminal.")]


class EnvVariable(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    name: Annotated[str, Field(description="The name of the environment variable.")]
    value: Annotated[str, Field(description="The value to set for the environment variable.")]


class FileSystemCapability(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    readTextFile: Annotated[
        Optional[bool],
        Field(description="Whether the Client supports `fs/read_text_file` requests."),
    ] = False
    writeTextFile: Annotated[
        Optional[bool],
        Field(description="Whether the Client supports `fs/write_text_file` requests."),
    ] = False


class HttpHeader(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    name: Annotated[str, Field(description="The name of the HTTP header.")]
    value: Annotated[str, Field(description="The value to set for the HTTP header.")]


class KillTerminalCommandResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None


class McpCapabilities(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    http: Annotated[Optional[bool], Field(description="Agent supports [`McpServer::Http`].")] = False
    sse: Annotated[Optional[bool], Field(description="Agent supports [`McpServer::Sse`].")] = False


class HttpMcpServer(BaseModel):
    headers: Annotated[
        List[HttpHeader],
        Field(description="HTTP headers to set when making requests to the MCP server."),
    ]
    name: Annotated[str, Field(description="Human-readable name identifying this MCP server.")]
    type: Literal["http"]
    url: Annotated[str, Field(description="URL to the MCP server.")]


class SseMcpServer(BaseModel):
    headers: Annotated[
        List[HttpHeader],
        Field(description="HTTP headers to set when making requests to the MCP server."),
    ]
    name: Annotated[str, Field(description="Human-readable name identifying this MCP server.")]
    type: Literal["sse"]
    url: Annotated[str, Field(description="URL to the MCP server.")]


class StdioMcpServer(BaseModel):
    args: Annotated[
        List[str],
        Field(description="Command-line arguments to pass to the MCP server."),
    ]
    command: Annotated[str, Field(description="Path to the MCP server executable.")]
    env: Annotated[
        List[EnvVariable],
        Field(description="Environment variables to set when launching the MCP server."),
    ]
    name: Annotated[str, Field(description="Human-readable name identifying this MCP server.")]


class ModelInfo(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    description: Annotated[Optional[str], Field(description="Optional description of the model.")] = None
    modelId: Annotated[str, Field(description="Unique identifier for the model.")]
    name: Annotated[str, Field(description="Human-readable name of the model.")]


class NewSessionRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    cwd: Annotated[
        str,
        Field(description="The working directory for this session. Must be an absolute path."),
    ]
    mcpServers: Annotated[
        List[Union[HttpMcpServer, SseMcpServer, StdioMcpServer]],
        Field(description="List of MCP (Model Context Protocol) servers the agent should connect to."),
    ]


class PromptCapabilities(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    audio: Annotated[Optional[bool], Field(description="Agent supports [`ContentBlock::Audio`].")] = False
    embeddedContext: Annotated[
        Optional[bool],
        Field(
            description="Agent supports embedded context in `session/prompt` requests.\n\nWhen enabled, the Client is allowed to include [`ContentBlock::Resource`]\nin prompt requests for pieces of context that are referenced in the message."
        ),
    ] = False
    image: Annotated[Optional[bool], Field(description="Agent supports [`ContentBlock::Image`].")] = False


class ReadTextFileResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    content: str


class ReleaseTerminalResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None


class DeniedOutcome(BaseModel):
    outcome: Literal["cancelled"]


class AllowedOutcome(BaseModel):
    optionId: Annotated[str, Field(description="The ID of the option the user selected.")]
    outcome: Literal["selected"]


class RequestPermissionResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    outcome: Annotated[
        Union[DeniedOutcome, AllowedOutcome],
        Field(description="The user's decision on the permission request."),
    ]


class Role(Enum):
    assistant = "assistant"
    user = "user"


class SessionModelState(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    availableModels: Annotated[List[ModelInfo], Field(description="The set of models that the Agent can use")]
    currentModelId: Annotated[str, Field(description="The current model the Agent is in.")]


class CurrentModeUpdate(BaseModel):
    currentModeId: Annotated[str, Field(description="Unique identifier for a Session Mode.")]
    sessionUpdate: Literal["current_mode_update"]


class SetSessionModeRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    modeId: Annotated[str, Field(description="The ID of the mode to set.")]
    sessionId: Annotated[str, Field(description="The ID of the session to set the mode for.")]


class SetSessionModeResponse(BaseModel):
    meta: Optional[Any] = None


class SetSessionModelRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    modelId: Annotated[str, Field(description="The ID of the model to set.")]
    sessionId: Annotated[str, Field(description="The ID of the session to set the model for.")]


class SetSessionModelResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None


class TerminalExitStatus(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    exitCode: Annotated[
        Optional[int],
        Field(
            description="The process exit code (may be null if terminated by signal).",
            ge=0,
        ),
    ] = None
    signal: Annotated[
        Optional[str],
        Field(description="The signal that terminated the process (may be null if exited normally)."),
    ] = None


class TerminalOutputRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    sessionId: Annotated[str, Field(description="The session ID for this request.")]
    terminalId: Annotated[str, Field(description="The ID of the terminal to get output from.")]


class TerminalOutputResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    exitStatus: Annotated[
        Optional[TerminalExitStatus],
        Field(description="Exit status if the command has completed."),
    ] = None
    output: Annotated[str, Field(description="The terminal output captured so far.")]
    truncated: Annotated[bool, Field(description="Whether the output was truncated due to byte limits.")]


class TextResourceContents(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    mimeType: Optional[str] = None
    text: str
    uri: str


class FileEditToolCallContent(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    newText: Annotated[str, Field(description="The new content after modification.")]
    oldText: Annotated[Optional[str], Field(description="The original content (None for new files).")] = None
    path: Annotated[str, Field(description="The file path being modified.")]
    type: Literal["diff"]


class TerminalToolCallContent(BaseModel):
    terminalId: str
    type: Literal["terminal"]


class ToolCallLocation(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    line: Annotated[Optional[int], Field(description="Optional line number within the file.", ge=0)] = None
    path: Annotated[str, Field(description="The file path being accessed or modified.")]


class WaitForTerminalExitRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    sessionId: Annotated[str, Field(description="The session ID for this request.")]
    terminalId: Annotated[str, Field(description="The ID of the terminal to wait for.")]


class WaitForTerminalExitResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    exitCode: Annotated[
        Optional[int],
        Field(
            description="The process exit code (may be null if terminated by signal).",
            ge=0,
        ),
    ] = None
    signal: Annotated[
        Optional[str],
        Field(description="The signal that terminated the process (may be null if exited normally)."),
    ] = None


class WriteTextFileRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    content: Annotated[str, Field(description="The text content to write to the file.")]
    path: Annotated[str, Field(description="Absolute path to the file to write.")]
    sessionId: Annotated[str, Field(description="The session ID for this request.")]


class WriteTextFileResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None


class AgentCapabilities(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    loadSession: Annotated[Optional[bool], Field(description="Whether the agent supports `session/load`.")] = False
    mcpCapabilities: Annotated[
        Optional[McpCapabilities],
        Field(description="MCP capabilities supported by the agent."),
    ] = {"http": False, "sse": False}
    promptCapabilities: Annotated[
        Optional[PromptCapabilities],
        Field(description="Prompt capabilities supported by the agent."),
    ] = {"audio": False, "embeddedContext": False, "image": False}


class Annotations(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    audience: Optional[List[Role]] = None
    lastModified: Optional[str] = None
    priority: Optional[float] = None


class AudioContent(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    annotations: Optional[Annotations] = None
    data: str
    mimeType: str


class AuthMethod(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    description: Annotated[
        Optional[str],
        Field(description="Optional description providing more details about this authentication method."),
    ] = None
    id: Annotated[str, Field(description="Unique identifier for this authentication method.")]
    name: Annotated[str, Field(description="Human-readable name of the authentication method.")]


class AvailableCommand(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    description: Annotated[str, Field(description="Human-readable description of what the command does.")]
    input: Annotated[
        Optional[AvailableCommandInput],
        Field(description="Input for the command if required"),
    ] = None
    name: Annotated[
        str,
        Field(description="Command name (e.g., `create_plan`, `research_codebase`)."),
    ]


class CancelNotification(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    sessionId: Annotated[str, Field(description="The ID of the session to cancel operations for.")]


class ClientCapabilities(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    fs: Annotated[
        Optional[FileSystemCapability],
        Field(
            description="File system capabilities supported by the client.\nDetermines which file operations the agent can request."
        ),
    ] = {"readTextFile": False, "writeTextFile": False}
    terminal: Annotated[
        Optional[bool],
        Field(description="Whether the Client support all `terminal/*` methods."),
    ] = False


class TextContentBlock(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    annotations: Optional[Annotations] = None
    text: str
    type: Literal["text"]


class ImageContentBlock(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    annotations: Optional[Annotations] = None
    data: str
    mimeType: str
    type: Literal["image"]
    uri: Optional[str] = None


class AudioContentBlock(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    annotations: Optional[Annotations] = None
    data: str
    mimeType: str
    type: Literal["audio"]


class ResourceContentBlock(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    annotations: Optional[Annotations] = None
    description: Optional[str] = None
    mimeType: Optional[str] = None
    name: str
    size: Optional[int] = None
    title: Optional[str] = None
    type: Literal["resource_link"]
    uri: str


class CreateTerminalRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    args: Annotated[Optional[List[str]], Field(description="Array of command arguments.")] = None
    command: Annotated[str, Field(description="The command to execute.")]
    cwd: Annotated[
        Optional[str],
        Field(description="Working directory for the command (absolute path)."),
    ] = None
    env: Annotated[
        Optional[List[EnvVariable]],
        Field(description="Environment variables for the command."),
    ] = None
    outputByteLimit: Annotated[
        Optional[int],
        Field(
            description="Maximum number of output bytes to retain.\n\nWhen the limit is exceeded, the Client truncates from the beginning of the output\nto stay within the limit.\n\nThe Client MUST ensure truncation happens at a character boundary to maintain valid\nstring output, even if this means the retained output is slightly less than the\nspecified limit.",
            ge=0,
        ),
    ] = None
    sessionId: Annotated[str, Field(description="The session ID for this request.")]


class ImageContent(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    annotations: Optional[Annotations] = None
    data: str
    mimeType: str
    uri: Optional[str] = None


class InitializeRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    clientCapabilities: Annotated[
        Optional[ClientCapabilities],
        Field(description="Capabilities supported by the client."),
    ] = {"fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False}
    protocolVersion: Annotated[
        int,
        Field(
            description="The latest protocol version supported by the client.",
            ge=0,
            le=65535,
        ),
    ]


class InitializeResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    agentCapabilities: Annotated[
        Optional[AgentCapabilities],
        Field(description="Capabilities supported by the agent."),
    ] = {
        "loadSession": False,
        "mcpCapabilities": {"http": False, "sse": False},
        "promptCapabilities": {
            "audio": False,
            "embeddedContext": False,
            "image": False,
        },
    }
    authMethods: Annotated[
        Optional[List[AuthMethod]],
        Field(description="Authentication methods supported by the agent."),
    ] = []
    protocolVersion: Annotated[
        int,
        Field(
            description="The protocol version the client specified if supported by the agent,\nor the latest protocol version supported by the agent.\n\nThe client should disconnect, if it doesn't support this version.",
            ge=0,
            le=65535,
        ),
    ]


class KillTerminalCommandRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    sessionId: Annotated[str, Field(description="The session ID for this request.")]
    terminalId: Annotated[str, Field(description="The ID of the terminal to kill.")]


class LoadSessionRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    cwd: Annotated[str, Field(description="The working directory for this session.")]
    mcpServers: Annotated[
        List[Union[HttpMcpServer, SseMcpServer, StdioMcpServer]],
        Field(description="List of MCP servers to connect to for this session."),
    ]
    sessionId: Annotated[str, Field(description="The ID of the session to load.")]


class PermissionOption(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    kind: Annotated[str, Field(description="Hint about the nature of this permission option.")]
    name: Annotated[str, Field(description="Human-readable label to display to the user.")]
    optionId: Annotated[str, Field(description="Unique identifier for this permission option.")]


class PlanEntry(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    content: Annotated[
        str,
        Field(description="Human-readable description of what this task aims to accomplish."),
    ]
    priority: Annotated[
        str,
        Field(
            description="The relative importance of this task.\nUsed to indicate which tasks are most critical to the overall goal."
        ),
    ]
    status: Annotated[str, Field(description="Current execution status of this task.")]


class PromptResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    stopReason: Annotated[str, Field(description="Indicates why the agent stopped processing the turn.")]


class ReadTextFileRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    limit: Annotated[Optional[int], Field(description="Maximum number of lines to read.", ge=0)] = None
    line: Annotated[
        Optional[int],
        Field(description="Line number to start reading from (1-based).", ge=0),
    ] = None
    path: Annotated[str, Field(description="Absolute path to the file to read.")]
    sessionId: Annotated[str, Field(description="The session ID for this request.")]


class ReleaseTerminalRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    sessionId: Annotated[str, Field(description="The session ID for this request.")]
    terminalId: Annotated[str, Field(description="The ID of the terminal to release.")]


class ResourceLink(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    annotations: Optional[Annotations] = None
    description: Optional[str] = None
    mimeType: Optional[str] = None
    name: str
    size: Optional[int] = None
    title: Optional[str] = None
    uri: str


class SessionMode(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    description: Optional[str] = None
    id: Annotated[str, Field(description="Unique identifier for a Session Mode.")]
    name: str


class SessionModeState(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    availableModes: Annotated[
        List[SessionMode],
        Field(description="The set of modes that the Agent can operate in"),
    ]
    currentModeId: Annotated[str, Field(description="The current mode the Agent is in.")]


class AgentPlanUpdate(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    entries: Annotated[
        List[PlanEntry],
        Field(
            description="The list of tasks to be accomplished.\n\nWhen updating a plan, the agent must send a complete list of all entries\nwith their current status. The client replaces the entire plan with each update."
        ),
    ]
    sessionUpdate: Literal["plan"]


class AvailableCommandsUpdate(BaseModel):
    availableCommands: List[AvailableCommand]
    sessionUpdate: Literal["available_commands_update"]


class TextContent(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    annotations: Optional[Annotations] = None
    text: str


class EmbeddedResourceContentBlock(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    annotations: Optional[Annotations] = None
    resource: Annotated[
        Union[TextResourceContents, BlobResourceContents],
        Field(description="Resource content that can be embedded in a message."),
    ]
    type: Literal["resource"]


class EmbeddedResource(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    annotations: Optional[Annotations] = None
    resource: Annotated[
        Union[TextResourceContents, BlobResourceContents],
        Field(description="Resource content that can be embedded in a message."),
    ]


class LoadSessionResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    models: Annotated[
        Optional[SessionModelState],
        Field(
            description="**UNSTABLE**\n\nThis capability is not part of the spec yet, and may be removed or changed at any point.\n\nInitial model state if supported by the Agent"
        ),
    ] = None
    modes: Annotated[
        Optional[SessionModeState],
        Field(
            description="Initial mode state if supported by the Agent\n\nSee protocol docs: [Session Modes](https://agentclientprotocol.com/protocol/session-modes)"
        ),
    ] = None


class NewSessionResponse(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    models: Annotated[
        Optional[SessionModelState],
        Field(
            description="**UNSTABLE**\n\nThis capability is not part of the spec yet, and may be removed or changed at any point.\n\nInitial model state if supported by the Agent"
        ),
    ] = None
    modes: Annotated[
        Optional[SessionModeState],
        Field(
            description="Initial mode state if supported by the Agent\n\nSee protocol docs: [Session Modes](https://agentclientprotocol.com/protocol/session-modes)"
        ),
    ] = None
    sessionId: Annotated[
        str,
        Field(
            description="Unique identifier for the created session.\n\nUsed in all subsequent requests for this conversation."
        ),
    ]


class Plan(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    entries: Annotated[
        List[PlanEntry],
        Field(
            description="The list of tasks to be accomplished.\n\nWhen updating a plan, the agent must send a complete list of all entries\nwith their current status. The client replaces the entire plan with each update."
        ),
    ]


class PromptRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
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
    sessionId: Annotated[str, Field(description="The ID of the session to send this user message to")]


class UserMessageChunk(BaseModel):
    content: Annotated[
        Union[
            TextContentBlock, ImageContentBlock, AudioContentBlock, ResourceContentBlock, EmbeddedResourceContentBlock
        ],
        Field(
            description="Content blocks represent displayable information in the Agent Client Protocol.\n\nThey provide a structured way to handle various types of user-facing content—whether\nit's text from language models, images for analysis, or embedded resources for context.\n\nContent blocks appear in:\n- User prompts sent via `session/prompt`\n- Language model output streamed through `session/update` notifications\n- Progress updates and results from tool calls\n\nThis structure is compatible with the Model Context Protocol (MCP), enabling\nagents to seamlessly forward content from MCP tool outputs without transformation.\n\nSee protocol docs: [Content](https://agentclientprotocol.com/protocol/content)"
        ),
    ]
    sessionUpdate: Literal["user_message_chunk"]


class AgentMessageChunk(BaseModel):
    content: Annotated[
        Union[
            TextContentBlock, ImageContentBlock, AudioContentBlock, ResourceContentBlock, EmbeddedResourceContentBlock
        ],
        Field(
            description="Content blocks represent displayable information in the Agent Client Protocol.\n\nThey provide a structured way to handle various types of user-facing content—whether\nit's text from language models, images for analysis, or embedded resources for context.\n\nContent blocks appear in:\n- User prompts sent via `session/prompt`\n- Language model output streamed through `session/update` notifications\n- Progress updates and results from tool calls\n\nThis structure is compatible with the Model Context Protocol (MCP), enabling\nagents to seamlessly forward content from MCP tool outputs without transformation.\n\nSee protocol docs: [Content](https://agentclientprotocol.com/protocol/content)"
        ),
    ]
    sessionUpdate: Literal["agent_message_chunk"]


class AgentThoughtChunk(BaseModel):
    content: Annotated[
        Union[
            TextContentBlock, ImageContentBlock, AudioContentBlock, ResourceContentBlock, EmbeddedResourceContentBlock
        ],
        Field(
            description="Content blocks represent displayable information in the Agent Client Protocol.\n\nThey provide a structured way to handle various types of user-facing content—whether\nit's text from language models, images for analysis, or embedded resources for context.\n\nContent blocks appear in:\n- User prompts sent via `session/prompt`\n- Language model output streamed through `session/update` notifications\n- Progress updates and results from tool calls\n\nThis structure is compatible with the Model Context Protocol (MCP), enabling\nagents to seamlessly forward content from MCP tool outputs without transformation.\n\nSee protocol docs: [Content](https://agentclientprotocol.com/protocol/content)"
        ),
    ]
    sessionUpdate: Literal["agent_thought_chunk"]


class ContentToolCallContent(BaseModel):
    content: Annotated[
        Union[
            TextContentBlock, ImageContentBlock, AudioContentBlock, ResourceContentBlock, EmbeddedResourceContentBlock
        ],
        Field(description="The actual content block."),
    ]
    type: Literal["content"]


class ToolCallUpdate(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    content: Annotated[
        Optional[List[Union[ContentToolCallContent, FileEditToolCallContent, TerminalToolCallContent]]],
        Field(description="Replace the content collection."),
    ] = None
    kind: Annotated[Optional[str], Field(description="Update the tool kind.")] = None
    locations: Annotated[
        Optional[List[ToolCallLocation]],
        Field(description="Replace the locations collection."),
    ] = None
    rawInput: Annotated[Optional[Any], Field(description="Update the raw input.")] = None
    rawOutput: Annotated[Optional[Any], Field(description="Update the raw output.")] = None
    status: Annotated[Optional[str], Field(description="Update the execution status.")] = None
    title: Annotated[Optional[str], Field(description="Update the human-readable title.")] = None
    toolCallId: Annotated[str, Field(description="The ID of the tool call being updated.")]


class RequestPermissionRequest(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    options: Annotated[
        List[PermissionOption],
        Field(description="Available permission options for the user to choose from."),
    ]
    sessionId: Annotated[str, Field(description="The session ID for this request.")]
    toolCall: Annotated[
        ToolCallUpdate,
        Field(description="Details about the tool call requiring permission."),
    ]


class ToolCallStart(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    content: Annotated[
        Optional[List[Union[ContentToolCallContent, FileEditToolCallContent, TerminalToolCallContent]]],
        Field(description="Content produced by the tool call."),
    ] = None
    kind: Annotated[
        Optional[str],
        Field(
            description="The category of tool being invoked.\nHelps clients choose appropriate icons and UI treatment."
        ),
    ] = None
    locations: Annotated[
        Optional[List[ToolCallLocation]],
        Field(description='File locations affected by this tool call.\nEnables "follow-along" features in clients.'),
    ] = None
    rawInput: Annotated[Optional[Any], Field(description="Raw input parameters sent to the tool.")] = None
    rawOutput: Annotated[Optional[Any], Field(description="Raw output returned by the tool.")] = None
    sessionUpdate: Literal["tool_call"]
    status: Annotated[Optional[str], Field(description="Current execution status of the tool call.")] = None
    title: Annotated[
        str,
        Field(description="Human-readable title describing what the tool is doing."),
    ]
    toolCallId: Annotated[
        str,
        Field(description="Unique identifier for this tool call within the session."),
    ]


class ToolCallProgress(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    content: Annotated[
        Optional[List[Union[ContentToolCallContent, FileEditToolCallContent, TerminalToolCallContent]]],
        Field(description="Replace the content collection."),
    ] = None
    kind: Annotated[Optional[str], Field(description="Update the tool kind.")] = None
    locations: Annotated[
        Optional[List[ToolCallLocation]],
        Field(description="Replace the locations collection."),
    ] = None
    rawInput: Annotated[Optional[Any], Field(description="Update the raw input.")] = None
    rawOutput: Annotated[Optional[Any], Field(description="Update the raw output.")] = None
    sessionUpdate: Literal["tool_call_update"]
    status: Annotated[Optional[str], Field(description="Update the execution status.")] = None
    title: Annotated[Optional[str], Field(description="Update the human-readable title.")] = None
    toolCallId: Annotated[str, Field(description="The ID of the tool call being updated.")]


class ToolCall(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    content: Annotated[
        Optional[List[Union[ContentToolCallContent, FileEditToolCallContent, TerminalToolCallContent]]],
        Field(description="Content produced by the tool call."),
    ] = None
    kind: Annotated[
        Optional[str],
        Field(
            description="The category of tool being invoked.\nHelps clients choose appropriate icons and UI treatment."
        ),
    ] = None
    locations: Annotated[
        Optional[List[ToolCallLocation]],
        Field(description='File locations affected by this tool call.\nEnables "follow-along" features in clients.'),
    ] = None
    rawInput: Annotated[Optional[Any], Field(description="Raw input parameters sent to the tool.")] = None
    rawOutput: Annotated[Optional[Any], Field(description="Raw output returned by the tool.")] = None
    status: Annotated[Optional[str], Field(description="Current execution status of the tool call.")] = None
    title: Annotated[
        str,
        Field(description="Human-readable title describing what the tool is doing."),
    ]
    toolCallId: Annotated[
        str,
        Field(description="Unique identifier for this tool call within the session."),
    ]


class SessionNotification(BaseModel):
    field_meta: Annotated[
        Optional[Any],
        Field(alias="_meta", description="Extension point for implementations"),
    ] = None
    sessionId: Annotated[str, Field(description="The ID of the session this update pertains to.")]
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
        ],
        Field(description="The actual update content."),
    ]


class Model(
    RootModel[
        Union[
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
            ],
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
            Union[CancelNotification, Any],
            Union[
                InitializeRequest,
                AuthenticateRequest,
                NewSessionRequest,
                LoadSessionRequest,
                SetSessionModeRequest,
                PromptRequest,
                SetSessionModelRequest,
                Any,
            ],
            Union[
                InitializeResponse,
                AuthenticateResponse,
                NewSessionResponse,
                LoadSessionResponse,
                SetSessionModeResponse,
                PromptResponse,
                SetSessionModelResponse,
                Any,
            ],
            Union[SessionNotification, Any],
        ]
    ]
):
    root: Union[
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
        ],
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
        Union[CancelNotification, Any],
        Union[
            InitializeRequest,
            AuthenticateRequest,
            NewSessionRequest,
            LoadSessionRequest,
            SetSessionModeRequest,
            PromptRequest,
            SetSessionModelRequest,
            Any,
        ],
        Union[
            InitializeResponse,
            AuthenticateResponse,
            NewSessionResponse,
            LoadSessionResponse,
            SetSessionModeResponse,
            PromptResponse,
            SetSessionModelResponse,
            Any,
        ],
        Union[SessionNotification, Any],
    ]


# Backwards compatibility aliases
AvailableCommandInput1 = CommandInputHint
ContentBlock1 = TextContentBlock
ContentBlock2 = ImageContentBlock
ContentBlock3 = AudioContentBlock
ContentBlock4 = ResourceContentBlock
ContentBlock5 = EmbeddedResourceContentBlock
McpServer1 = HttpMcpServer
McpServer2 = SseMcpServer
McpServer3 = StdioMcpServer
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
ToolCallContent1 = ContentToolCallContent
ToolCallContent2 = FileEditToolCallContent
ToolCallContent3 = TerminalToolCallContent
