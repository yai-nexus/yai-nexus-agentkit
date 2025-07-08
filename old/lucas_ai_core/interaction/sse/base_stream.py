import json
from abc import ABC, abstractmethod
from typing import (
    Optional,
)

from sse_starlette.sse import ContentStream

from .validators import SSEConfig, SSEHandlerError


class BaseStream(ABC):
    """stream输出基类"""

    def __init__(
        self,
        content: Optional[str] = "",
        config: Optional[SSEConfig] = None,
    ):
        self._config = config or SSEConfig()
        self.content = content

    @abstractmethod
    async def stream(self) -> ContentStream:
        pass

    @classmethod
    def format_error(cls, error: Exception) -> dict:
        """格式化错误响应"""
        if isinstance(error, SSEHandlerError):
            return {
                "event": "error",
                "data": json.dumps(
                    {"error_code": error.error_code, "message": error.message}
                ),
            }
        return {
            "event": "error",
            "data": json.dumps({"error_code": "UNKNOWN_ERROR", "message": str(error)}),
        }
