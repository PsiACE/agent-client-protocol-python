from __future__ import annotations

import inspect
import warnings
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

from pydantic import BaseModel

from acp.utils import to_camel_case

from .exceptions import RequestError

__all__ = ["MessageRouter", "Route"]


AsyncHandler = Callable[[Any], Awaitable[Any | None]]
RequestHandler = Callable[[str, dict[str, Any]], Awaitable[Any]]
HandlerT = TypeVar("HandlerT", bound=RequestHandler)


@dataclass(slots=True)
class Route:
    method: str
    func: AsyncHandler | None
    kind: Literal["request", "notification"]
    optional: bool = False
    default_result: Any = None
    adapt_result: Callable[[Any | None], Any] | None = None
    warn_unstable: bool = False

    async def handle(self, params: Any) -> Any:
        if self.func is None:
            if self.optional:
                return self.default_result
            raise RequestError.method_not_found(self.method)
        if self.warn_unstable:
            warnings.warn(
                f"The method {self.method} is part of the unstable protocol, please enable `use_unstable_protocol` flag to use it.",
                UserWarning,
                stacklevel=3,
            )
            raise RequestError.method_not_found(self.method)
        result = await self.func(params)
        if self.adapt_result is not None and self.kind == "request":
            return self.adapt_result(result)
        return result


class MessageRouter:
    def __init__(self, use_unstable_protocol: bool = False) -> None:
        self._requests: dict[str, Route] = {}
        self._notifications: dict[str, Route] = {}
        self._request_extensions: RequestHandler | None = None
        self._notification_extensions: RequestHandler | None = None
        self._use_unstable_protocol = use_unstable_protocol

    def add_route(self, route: Route) -> None:
        if route.kind == "request":
            self._requests[route.method] = route
        else:
            self._notifications[route.method] = route

    def _make_func(self, model: type[BaseModel], obj: Any, attr: str) -> AsyncHandler | None:
        legacy_api = False
        func = getattr(obj, attr, None)
        if func is None and "_" in attr:
            attr = to_camel_case(attr)
            func = getattr(obj, attr, None)
            legacy_api = True
        elif callable(func) and "_" not in attr:
            original_func = func
            if hasattr(func, "__func__"):
                original_func = func.__func__
            parameters = inspect.signature(original_func).parameters
            if len(parameters) == 2 and "params" in parameters:
                legacy_api = True

        if func is None or not callable(func):
            return None

        async def wrapper(params: Any) -> Any:
            if legacy_api:
                warnings.warn(
                    f"The old style method {type(obj).__name__}.{attr} is deprecated, "
                    "please update to the snake-cased form.",
                    DeprecationWarning,
                    stacklevel=3,
                )
            model_obj = model.model_validate(params)
            if legacy_api:
                return await func(model_obj)  # type: ignore[arg-type]
            params = {k: getattr(model_obj, k) for k in model.model_fields if k != "field_meta"}
            if meta := getattr(model_obj, "field_meta", None):
                params.update(meta)
            return await func(**params)  # type: ignore[arg-type]

        return wrapper

    def route_request(
        self,
        method: str,
        model: type[BaseModel],
        obj: Any,
        attr: str,
        optional: bool = False,
        default_result: Any = None,
        adapt_result: Callable[[Any | None], Any] | None = None,
        unstable: bool = False,
    ) -> Route:
        """Register a request route with obj and attribute name."""
        route = Route(
            method=method,
            func=self._make_func(model, obj, attr),
            kind="request",
            optional=optional,
            default_result=default_result,
            adapt_result=adapt_result,
            warn_unstable=unstable and not self._use_unstable_protocol,
        )
        self.add_route(route)
        return route

    def route_notification(
        self,
        method: str,
        model: type[BaseModel],
        obj: Any,
        attr: str,
        optional: bool = False,
        unstable: bool = False,
    ) -> Route:
        """Register a notification route with obj and attribute name."""
        route = Route(
            method=method,
            func=self._make_func(model, obj, attr),
            kind="notification",
            optional=optional,
            warn_unstable=unstable and not self._use_unstable_protocol,
        )
        self.add_route(route)
        return route

    def handle_extension_request(self, handler: HandlerT) -> HandlerT:
        """Register a handler for extension requests."""
        self._request_extensions = handler
        return handler

    def handle_extension_notification(self, handler: HandlerT) -> HandlerT:
        """Register a handler for extension notifications."""
        self._notification_extensions = handler
        return handler

    async def __call__(self, method: str, params: Any | None, is_notification: bool) -> Any:
        """The main router call to handle a request or notification."""
        if is_notification:
            ext_handler = self._notification_extensions
            routes = self._notifications
        else:
            ext_handler = self._request_extensions
            routes = self._requests

        if isinstance(method, str) and method.startswith("_"):
            if ext_handler is None:
                raise RequestError.method_not_found(method)
            payload = params if isinstance(params, dict) else {}
            return await ext_handler(method[1:], payload)

        route = routes.get(method)
        if route is None:
            raise RequestError.method_not_found(method)

        return await route.handle(params)
