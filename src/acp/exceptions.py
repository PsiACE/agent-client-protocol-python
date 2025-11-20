from __future__ import annotations

from typing import Any

__all__ = ["RequestError"]


class RequestError(Exception):
    """JSON-RPC 2.0 error helper."""

    def __init__(self, code: int, message: str, data: Any | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.data = data

    @classmethod
    def parse_error(cls, data: dict[str, Any] | None = None) -> RequestError:
        return cls(-32700, "Parse error", data)

    @classmethod
    def invalid_request(cls, data: dict[str, Any] | None = None) -> RequestError:
        return cls(-32600, "Invalid request", data)

    @classmethod
    def method_not_found(cls, method: str) -> RequestError:
        return cls(-32601, "Method not found", {"method": method})

    @classmethod
    def invalid_params(cls, data: dict[str, Any] | None = None) -> RequestError:
        return cls(-32602, "Invalid params", data)

    @classmethod
    def internal_error(cls, data: dict[str, Any] | None = None) -> RequestError:
        return cls(-32603, "Internal error", data)

    @classmethod
    def auth_required(cls, data: dict[str, Any] | None = None) -> RequestError:
        return cls(-32000, "Authentication required", data)

    @classmethod
    def resource_not_found(cls, uri: str | None = None) -> RequestError:
        data = {"uri": uri} if uri is not None else None
        return cls(-32002, "Resource not found", data)

    def to_error_obj(self) -> dict[str, Any]:
        return {"code": self.code, "message": str(self), "data": self.data}
