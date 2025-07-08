import uuid
from typing import (
    Union,
    Any,
    Optional,
    AsyncIterator,
)

from langchain.chains.base import Chain
from langchain.chains.sequential import SequentialChain
from langchain.schema.runnable import Runnable
from langchain_core.messages import AIMessageChunk
from sse_starlette.sse import AsyncContentStream

from .base_stream import BaseStream
from .message import BlockMessage, ContentBlock, MessageTypeEnum
from .validators import SSEConfig


class LangChainStream(BaseStream):
    """LangChain流式输出实现"""

    def __init__(
        self,
        chain: Union[Chain, SequentialChain, Runnable],  # LangChain Chain
        inputs: dict[str, Any],
        conversation_id: Optional[str] = None,
        message_type: Optional[MessageTypeEnum] = None,
        config: Optional[SSEConfig] = None,
    ):
        super().__init__(config)
        self._chain = chain | self.convert_message
        self._inputs = inputs
        self.conversation_id = conversation_id if conversation_id else str(uuid.uuid4())
        self.message_type = message_type

    def _create_finish_message(self) -> BlockMessage:
        """创建BlockMessage"""
        return BlockMessage(
            conversationId=self.conversation_id,
            finish=True,
            blocks=[ContentBlock(blockId=f"block-{uuid.uuid4().hex}", content="")],
        )

    def _create_block_message(self, token: str) -> BlockMessage:
        """创建BlockMessage"""
        return BlockMessage(
            conversationId=self.conversation_id,
            blocks=[ContentBlock(blockId=f"block-{uuid.uuid4().hex}", content=token)],
        )

    async def convert_message(
        self, input: AsyncIterator[str]
    ) -> AsyncIterator[BlockMessage]:  # async def
        buffer = ""
        async for chunk in input:
            if isinstance(chunk, AIMessageChunk):
                content = chunk.content
                buffer += content
                yield self._create_block_message(content)

    async def stream(self) -> AsyncContentStream:
        """生成SSE流
        使用LangChain的astream_chain处理输入并生成事件流

        Yields:
            str: 格式化的SSE消息
        """
        try:
            # 发送重试超时配置
            yield {"retry": self._config.retry_timeout}
            # 使用chain.astream处理输入
            async for chunk in self._chain.astream(
                input=self._inputs,
            ):
                yield {"event": "message", "data": chunk}

            yield {"event": "message", "data": self._create_finish_message()}

        except Exception as e:
            error_response = self.format_error(e)
            yield error_response
            raise
