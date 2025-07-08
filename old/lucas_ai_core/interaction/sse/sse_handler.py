import logging
from typing import (
    Optional,
)

from sse_starlette.sse import EventSourceResponse, ServerSentEvent, ContentStream

from .validators import SSEConfig

logger = logging.getLogger(__name__)


class SSEHandler:
    """SSE流管理器"""

    def __init__(
        self,
        source: ContentStream,
        config: Optional[SSEConfig] = None,
    ):
        """初始化SSE管理器

        Args:
            source: 数据源
            config: 心跳间隔（秒） or 重连超时时间（毫秒）等设置
        """
        self.source = source
        self._config = config or SSEConfig()
        self.heartbeat_interval = self._config.heartbeat_interval

    async def sse_response(self) -> EventSourceResponse:
        """获取EventSourceResponse

        Returns:
            EventSourceResponse: SSE响应对象
        """
        return EventSourceResponse(
            content=self.source,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
            ping_message_factory=lambda: ServerSentEvent(
                event="ping",
                retry=self._config.heartbeat_interval,
            ),
        )
