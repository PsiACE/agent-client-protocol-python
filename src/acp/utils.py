from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from .connection import Connection

__all__ = [
    "ensure_dict",
    "normalize_result",
    "notify_model",
    "request_model",
    "request_model_from_dict",
    "request_optional_model",
    "serialize_params",
    "validate_model",
    "validate_model_from_dict",
    "validate_optional_model",
]

ModelT = TypeVar("ModelT", bound=BaseModel)


def serialize_params(params: BaseModel) -> dict[str, Any]:
    """Return a JSON-serializable representation used for RPC calls."""
    return params.model_dump(by_alias=True, exclude_none=True, exclude_defaults=True)


def normalize_result(payload: Any) -> dict[str, Any]:
    """Convert optional BaseModel/None responses into JSON-friendly payloads."""
    if payload is None:
        return {}
    if isinstance(payload, BaseModel):
        return serialize_params(payload)
    return payload


def ensure_dict(payload: Any) -> dict[str, Any]:
    """Return payload when it is a dict, otherwise an empty dict."""
    return payload if isinstance(payload, dict) else {}


def validate_model(payload: Any, model_type: type[ModelT]) -> ModelT:
    """Validate payload using the provided Pydantic model."""
    return model_type.model_validate(payload)


def validate_model_from_dict(payload: Any, model_type: type[ModelT]) -> ModelT:
    """Validate payload, coercing non-dict values to an empty dict first."""
    return model_type.model_validate(ensure_dict(payload))


def validate_optional_model(payload: Any, model_type: type[ModelT]) -> ModelT | None:
    """Validate payload when it is a dict, otherwise return None."""
    if isinstance(payload, dict):
        return model_type.model_validate(payload)
    return None


async def request_model(
    conn: Connection,
    method: str,
    params: BaseModel,
    response_model: type[ModelT],
) -> ModelT:
    """Send a request with serialized params and validate the response."""
    response = await conn.send_request(method, serialize_params(params))
    return validate_model(response, response_model)


async def request_model_from_dict(
    conn: Connection,
    method: str,
    params: BaseModel,
    response_model: type[ModelT],
) -> ModelT:
    """Send a request and validate the response, coercing non-dict payloads."""
    response = await conn.send_request(method, serialize_params(params))
    return validate_model_from_dict(response, response_model)


async def request_optional_model(
    conn: Connection,
    method: str,
    params: BaseModel,
    response_model: type[ModelT],
) -> ModelT | None:
    """Send a request and validate optional dict responses."""
    response = await conn.send_request(method, serialize_params(params))
    return validate_optional_model(response, response_model)


async def notify_model(conn: Connection, method: str, params: BaseModel) -> None:
    """Send a notification with serialized params."""
    await conn.send_notification(method, serialize_params(params))
