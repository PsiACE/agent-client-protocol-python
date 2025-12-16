from typing import Any

import pytest

from acp.exceptions import RequestError
from acp.schema import (
    ForkSessionResponse,
    HttpMcpServer,
    ListSessionsResponse,
    McpServerStdio,
    ResumeSessionResponse,
    SetSessionModelResponse,
    SseMcpServer,
)
from tests.conftest import TestAgent


class UnstableAgent(TestAgent):
    async def list_sessions(self, cursor: str | None = None, cwd: str | None = None, **kwargs) -> ListSessionsResponse:
        return ListSessionsResponse(sessions=[])

    async def set_session_model(self, model_id: str, session_id: str, **kwargs: Any) -> SetSessionModelResponse | None:
        return SetSessionModelResponse()

    async def fork_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio] | None = None,
        **kwargs: Any,
    ) -> ForkSessionResponse:
        return ForkSessionResponse(session_id="forked_sess")

    async def resume_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio] | None = None,
        **kwargs: Any,
    ) -> ResumeSessionResponse:
        return ResumeSessionResponse()


@pytest.mark.parametrize("agent", [UnstableAgent()])
@pytest.mark.asyncio
async def test_call_unstable_protocol(connect):
    _, agent_conn = connect(use_unstable_protocol=True)

    resp = await agent_conn.list_sessions()
    assert isinstance(resp, ListSessionsResponse)

    resp = await agent_conn.set_session_model(session_id="sess", model_id="gpt-4o-mini")
    assert isinstance(resp, SetSessionModelResponse)

    resp = await agent_conn.fork_session(cwd="/workspace", session_id="sess")
    assert isinstance(resp, ForkSessionResponse)

    resp = await agent_conn.resume_session(cwd="/workspace", session_id="sess")
    assert isinstance(resp, ResumeSessionResponse)


@pytest.mark.parametrize("agent", [UnstableAgent()])
@pytest.mark.asyncio
async def test_call_unstable_protocol_warning(connect):
    _, agent_conn = connect(use_unstable_protocol=False)

    with pytest.warns(UserWarning) as record:
        with pytest.raises(RequestError):
            await agent_conn.list_sessions()
        assert len(record) == 1

    with pytest.warns(UserWarning) as record:
        with pytest.raises(RequestError):
            await agent_conn.set_session_model(session_id="sess", model_id="gpt-4o-mini")
        assert len(record) == 1
