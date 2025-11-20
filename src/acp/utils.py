from __future__ import annotations

import functools
import warnings
from collections.abc import Callable
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
MethodT = TypeVar("MethodT", bound=Callable)
ClassT = TypeVar("ClassT", bound=type)
T = TypeVar("T")


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


def param_model(param_cls: type[BaseModel]) -> Callable[[MethodT], MethodT]:
    """Decorator to map the method parameters to a Pydantic model.
    It is just a marker and does nothing at runtime.
    """

    def decorator(func: MethodT) -> MethodT:
        func.__param_model__ = param_cls  # type: ignore[attr-defined]
        return func

    return decorator


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case strings to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _make_legacy_func(func: Callable[..., T], model: type[BaseModel]) -> Callable[[Any, BaseModel], T]:
    @functools.wraps(func)
    def wrapped(self, params: BaseModel) -> T:
        warnings.warn(
            f"Calling {func.__name__} with {model.__name__} parameter is "  # type: ignore[attr-defined]
            "deprecated, please update to the new API style.",
            DeprecationWarning,
            stacklevel=3,
        )
        kwargs = {k: getattr(params, k) for k in model.model_fields if k != "field_meta"}
        if meta := getattr(params, "field_meta", None):
            kwargs.update(meta)
        return func(self, **kwargs)  # type: ignore[arg-type]

    return wrapped


def _make_compatible_func(func: Callable[..., T], model: type[BaseModel]) -> Callable[..., T]:
    @functools.wraps(func)
    def wrapped(self, *args: Any, **kwargs: Any) -> T:
        param = None
        if not kwargs and len(args) == 1:
            param = args[0]
        elif not args and len(kwargs) == 1:
            param = kwargs.get("params")
        if isinstance(param, model):
            warnings.warn(
                f"Calling {func.__name__} with {model.__name__} parameter "  # type: ignore[attr-defined]
                "is deprecated, please update to the new API style.",
                DeprecationWarning,
                stacklevel=3,
            )
            kwargs = {k: getattr(param, k) for k in model.model_fields if k != "field_meta"}
            if meta := getattr(param, "field_meta", None):
                kwargs.update(meta)
            return func(self, **kwargs)  # type: ignore[arg-type]
        return func(self, *args, **kwargs)

    return wrapped


def compatible_class(cls: ClassT) -> ClassT:
    """Mark a class as backward compatible with old API style."""
    for attr in dir(cls):
        func = getattr(cls, attr)
        if not callable(func) or (model := getattr(func, "__param_model__", None)) is None:
            continue
        if "_" in attr:
            setattr(cls, to_camel_case(attr), _make_legacy_func(func, model))
        else:
            setattr(cls, attr, _make_compatible_func(func, model))
    return cls
