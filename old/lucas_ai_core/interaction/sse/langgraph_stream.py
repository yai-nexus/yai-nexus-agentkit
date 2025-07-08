import asyncio
import json
import os
import uuid
from typing import (
    Union,
    Any,
    Optional,
)

from langfuse.callback import CallbackHandler
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from sse_starlette.sse import AsyncContentStream

from .base_stream import BaseStream
from .message import SSEBaseMessage, MessageTypeEnum
from .validators import SSEConfig


class LangGraphStream(BaseStream):
    def __init__(
        self,
        conversation_id: str,
        state: Union[dict[str, Any], Any],
        graph: CompiledStateGraph,
        config: Optional[SSEConfig] = None,
    ):
        super().__init__(config)
        self._graph = graph
        self.conversation_id = conversation_id if conversation_id else str(uuid.uuid4())
        self.state = state

    async def stream(self) -> AsyncContentStream:
        """生成SSE流
        使用graph.astream处理状态并生成事件流
        Yields:
        str: 格式化的SSE消息
        """
        try:
            yield {"retry": self._config.retry_timeout}

            handler = CallbackHandler(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST"),
                session_id=self.conversation_id,
                debug=os.getenv("DEBUG", "False").strip().lower() == "true",
            )
            config = {
                "callbacks": [handler],
                "configurable": {"thread_id": self.conversation_id},
                "run_name": f"sse_stream_{self.conversation_id}",
            }
            async for chunk in self._graph.astream(
                self.state,
                config=config,
                stream_mode=["custom"],
                subgraphs=True,
            ):
                # 优化：添加类型检查和更好的错误处理
                if not chunk:
                    continue

                if isinstance(chunk, tuple):
                    start, mode, data = chunk
                    chunk = data

                # 优化：根据不同的stream_mode处理不同类型的数据
                if isinstance(chunk, BaseModel):
                    data = chunk.model_dump_json()
                elif isinstance(chunk, dict):
                    data = json.dumps(chunk)
                else:
                    data = str(chunk)

                yield {"event": "message", "data": data}
            yield {
                "event": "message",
                "data": SSEBaseMessage(
                    finish=True, type=MessageTypeEnum.CHAT.value
                ).model_dump_json(),
            }
        except asyncio.CancelledError:
            raise
        except Exception as e:
            error_response = self.format_error(e)
            yield error_response
            raise
        finally:
            pass
