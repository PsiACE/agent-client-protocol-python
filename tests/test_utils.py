import pytest

from acp.schema import AgentMessageChunk, TextContentBlock
from acp.utils import serialize_params


def test_serialize_params_uses_meta_aliases() -> None:
    chunk = AgentMessageChunk(
        session_update="agent_message_chunk",
        content=TextContentBlock(type="text", text="demo", field_meta={"inner": "value"}),
        field_meta={"outer": "value"},
    )

    payload = serialize_params(chunk)

    assert payload["_meta"] == {"outer": "value"}
    assert payload["content"]["_meta"] == {"inner": "value"}


def test_serialize_params_omits_meta_when_absent() -> None:
    chunk = AgentMessageChunk(
        session_update="agent_message_chunk",
        content=TextContentBlock(type="text", text="demo"),
    )

    payload = serialize_params(chunk)

    assert "_meta" not in payload
    assert "_meta" not in payload["content"]


def test_field_meta_can_be_set_by_name_on_models() -> None:
    chunk = AgentMessageChunk(
        session_update="agent_message_chunk",
        content=TextContentBlock(type="text", text="demo", field_meta={"inner": "value"}),
        field_meta={"outer": "value"},
    )

    assert chunk.field_meta == {"outer": "value"}
    assert chunk.content.field_meta == {"inner": "value"}


@pytest.mark.parametrize(
    "original, expected",
    [
        ("simple_test", "simpleTest"),
        ("another_example_here", "anotherExampleHere"),
        ("lowercase", "lowercase"),
        ("alreadyCamelCase", "alreadyCamelCase"),
    ],
)
def test_to_camel_case(original, expected) -> None:
    from acp.utils import to_camel_case

    assert to_camel_case(original) == expected
