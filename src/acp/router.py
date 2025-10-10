from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel

from .exceptions import RequestError

__all__ = [
    "MessageRouter",
    "Route",
    "RouterBuilder",
    "attribute_handler",
]


AsyncHandler = Callable[[Any], Awaitable[Any | None]]


@dataclass(slots=True)
class Route:
    method: str
    model: type[BaseModel]
    handle: Callable[[], AsyncHandler | None]
    kind: Literal["request", "notification"]
    optional: bool = False
    default_result: Any = None
    adapt_result: Callable[[Any | None], Any] | None = None


class MessageRouter:
    def __init__(
        self,
        routes: Sequence[Route],
        *,
        request_extensions: Callable[[str, dict[str, Any]], Awaitable[Any]] | None = None,
        notification_extensions: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None,
    ) -> None:
        self._requests: Mapping[str, Route] = {route.method: route for route in routes if route.kind == "request"}
        self._notifications: Mapping[str, Route] = {
            route.method: route for route in routes if route.kind == "notification"
        }
        self._request_extensions = request_extensions
        self._notification_extensions = notification_extensions

    async def dispatch_request(self, method: str, params: Any | None) -> Any:
        if isinstance(method, str) and method.startswith("_"):
            if self._request_extensions is None:
                raise RequestError.method_not_found(method)
            payload = params if isinstance(params, dict) else {}
            return await self._request_extensions(method[1:], payload)

        route = self._requests.get(method)
        if route is None:
            raise RequestError.method_not_found(method)
        model = route.model
        parsed = model.model_validate(params)

        handler = route.handle()
        if handler is None:
            if route.optional:
                return route.default_result
            raise RequestError.method_not_found(method)

        result = await handler(parsed)
        if route.adapt_result is not None:
            return route.adapt_result(result)
        return result

    async def dispatch_notification(self, method: str, params: Any | None) -> None:
        if isinstance(method, str) and method.startswith("_"):
            if self._notification_extensions is None:
                return
            payload = params if isinstance(params, dict) else {}
            await self._notification_extensions(method[1:], payload)
            return

        route = self._notifications.get(method)
        if route is None:
            raise RequestError.method_not_found(method)
        model = route.model
        parsed = model.model_validate(params)

        handler = route.handle()
        if handler is None:
            if route.optional:
                return
            raise RequestError.method_not_found(method)
        await handler(parsed)


class RouterBuilder:
    def __init__(self) -> None:
        self._routes: list[Route] = []

    def request(
        self,
        method: str,
        model: type[BaseModel],
        *,
        optional: bool = False,
        default_result: Any = None,
        adapt_result: Callable[[Any | None], Any] | None = None,
    ) -> Callable[[Callable[[], AsyncHandler | None]], Callable[[], AsyncHandler | None]]:
        def decorator(factory: Callable[[], AsyncHandler | None]) -> Callable[[], AsyncHandler | None]:
            self._routes.append(
                Route(
                    method=method,
                    model=model,
                    handle=factory,
                    kind="request",
                    optional=optional,
                    default_result=default_result,
                    adapt_result=adapt_result,
                )
            )
            return factory

        return decorator

    def notification(
        self,
        method: str,
        model: type[BaseModel],
        *,
        optional: bool = False,
    ) -> Callable[[Callable[[], AsyncHandler | None]], Callable[[], AsyncHandler | None]]:
        def decorator(factory: Callable[[], AsyncHandler | None]) -> Callable[[], AsyncHandler | None]:
            self._routes.append(
                Route(
                    method=method,
                    model=model,
                    handle=factory,
                    kind="notification",
                    optional=optional,
                )
            )
            return factory

        return decorator

    def build(
        self,
        *,
        request_extensions: Callable[[str, dict[str, Any]], Awaitable[Any]] | None = None,
        notification_extensions: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None,
    ) -> MessageRouter:
        return MessageRouter(
            routes=self._routes,
            request_extensions=request_extensions,
            notification_extensions=notification_extensions,
        )

    def request_attr(
        self,
        method: str,
        model: type[BaseModel],
        obj: Any,
        attr: str,
        *,
        optional: bool = False,
        default_result: Any = None,
        adapt_result: Callable[[Any | None], Any] | None = None,
    ) -> None:
        self.request(
            method,
            model,
            optional=optional,
            default_result=default_result,
            adapt_result=adapt_result,
        )(attribute_handler(obj, attr))

    def notification_attr(
        self,
        method: str,
        model: type[BaseModel],
        obj: Any,
        attr: str,
        *,
        optional: bool = False,
    ) -> None:
        self.notification(method, model, optional=optional)(attribute_handler(obj, attr))


def attribute_handler(obj: Any, attr: str) -> Callable[[], AsyncHandler | None]:
    def factory() -> AsyncHandler | None:
        func = getattr(obj, attr, None)
        return func if callable(func) else None

    return factory
