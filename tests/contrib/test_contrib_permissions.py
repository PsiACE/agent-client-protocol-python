from __future__ import annotations

import pytest

from acp.contrib.permissions import PermissionBroker, default_permission_options
from acp.contrib.tool_calls import ToolCallTracker
from acp.schema import (
    AllowedOutcome,
    ContentToolCallContent,
    PermissionOption,
    RequestPermissionRequest,
    RequestPermissionResponse,
    TextContentBlock,
)


@pytest.mark.asyncio
async def test_permission_broker_uses_tracker_state():
    captured: dict[str, RequestPermissionRequest] = {}

    async def fake_requester(request: RequestPermissionRequest):
        captured["request"] = request
        return RequestPermissionResponse(
            outcome=AllowedOutcome(option_id=request.options[0].option_id, outcome="selected")
        )

    tracker = ToolCallTracker(id_factory=lambda: "perm-id")
    tracker.start("external", title="Need approval")
    broker = PermissionBroker("session", fake_requester, tracker=tracker)

    result = await broker.request_for("external", description="Perform sensitive action")
    assert isinstance(result.outcome, AllowedOutcome)
    assert result.outcome.option_id == captured["request"].options[0].option_id
    assert captured["request"].tool_call.content is not None
    last_content = captured["request"].tool_call.content[-1]
    assert isinstance(last_content, ContentToolCallContent)
    assert isinstance(last_content.content, TextContentBlock)
    assert last_content.content.text.startswith("Perform sensitive action")


@pytest.mark.asyncio
async def test_permission_broker_accepts_custom_options():
    tracker = ToolCallTracker(id_factory=lambda: "custom")
    tracker.start("external", title="Custom options")
    options = [
        PermissionOption(option_id="allow", name="Allow once", kind="allow_once"),
    ]
    recorded: list[str] = []

    async def requester(request: RequestPermissionRequest):
        recorded.append(request.options[0].option_id)
        return RequestPermissionResponse(
            outcome=AllowedOutcome(option_id=request.options[0].option_id, outcome="selected")
        )

    broker = PermissionBroker("session", requester, tracker=tracker)
    await broker.request_for("external", options=options)
    assert recorded == ["allow"]


def test_default_permission_options_shape():
    options = default_permission_options()
    assert len(options) == 3
    assert {opt.option_id for opt in options} == {"approve", "approve_for_session", "reject"}
