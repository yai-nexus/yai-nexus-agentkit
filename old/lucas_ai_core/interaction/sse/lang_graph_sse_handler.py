import logging
import uuid
from typing import (
    Union,
    Any,
    Optional,
)

from langgraph.graph.state import CompiledStateGraph
from sse_starlette.sse import EventSourceResponse

from .langgraph_stream import LangGraphStream
from .sse_handler import SSEHandler
from .validators import SSEConfig

logger = logging.getLogger(__name__)


class LangGraphSSEHandler:
    """SSE流管理器
    泛型参数:
        T: 状态对象类型，必须是TypedDict的子类
    """

    def __init__(
        self,
        state: Union[dict[str, Any], Any],
        graph: CompiledStateGraph,
        conversation_id: Optional[str] = "",
        config: Optional[SSEConfig] = None,
    ):
        """初始化SSE管理器

        Args:
            conversation_id: 会话ID
            state: 状态对象，类型为T
            graph: 工作流对象
        """
        self.graph = graph
        self.conversation_id = conversation_id if conversation_id else str(uuid.uuid4())
        self.state = state
        self.is_connected = True
        self.config = config

    async def langgraph_sse_response(self) -> EventSourceResponse:
        """获取EventSourceResponse

        Returns:
            EventSourceResponse: SSE响应对象
        """
        stream = LangGraphStream(
            conversation_id=self.conversation_id,
            state=self.state,
            graph=self.graph,
            config=self.config,
        )
        handler = SSEHandler(source=stream.stream())
        return await handler.sse_response()
