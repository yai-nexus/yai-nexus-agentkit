import logging
import uuid
from typing import (
    Union,
    Any,
    Optional,
)

from langchain.chains.base import Chain
from langchain.chains.sequential import SequentialChain
from langchain.schema.runnable import Runnable
from sse_starlette.sse import EventSourceResponse

from .langchain_stream import LangChainStream
from .message import MessageTypeEnum
from .sse_handler import SSEHandler
from .validators import SSEConfig

logger = logging.getLogger(__name__)


class LangChainSSEHandler:
    """LangChainSSEHandler 流管理器"""

    def __init__(
        self,
        chain: Union[Chain, SequentialChain, Runnable],  # LangChain Chain
        inputs: dict[str, Any],
        conversation_id: Optional[str] = None,
        message_type: Optional[MessageTypeEnum] = None,
        config: Optional[SSEConfig] = None,
    ):
        self._chain = chain
        self._inputs = inputs
        self.conversation_id = conversation_id if conversation_id else str(uuid.uuid4())
        self.message_type = message_type
        self.config = config

    async def langchain_sse_response(self) -> EventSourceResponse:
        """获取EventSourceResponse

        Returns:
            EventSourceResponse: SSE响应对象
        """
        stream_handler = LangChainStream(
            chain=self._chain,
            inputs=self._inputs,
            conversation_id=self.conversation_id,
            message_type=self.message_type,
            config=self.config,
        )
        handler = SSEHandler(source=stream_handler.stream())
        return await handler.sse_response()
