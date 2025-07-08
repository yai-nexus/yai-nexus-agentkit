
# 技术设计方案: 003-交互适配器

## 1. 背景

现代 Agent 应用的核心体验之一是流式响应。Agent 在思考和生成内容时，应能实时地将中间结果和最终内容“打字机”般地输出到前端。Server-Sent Events (SSE) 是实现这一功能的理想技术。

旧代码库 (`old/lucas_ai_core/interaction/sse/`) 中包含了一套完整的 SSE 处理逻辑，但它与 LangChain、LangGraph 以及特定的消息模型耦合过深，不够通用。

此方案旨在设计一个位于 `src/yai_nexus_agentkit/adapter/` 下的、通用的交互适配器层。它负责将核心业务逻辑（如 LLM 的输出流）与具体的网络协议（如 SSE）进行解耦，并定义一套标准化的数据交换格式。

设计目标：
- **协议封装**: 将 SSE 的实现细节封装起来，业务逻辑无需关心。
- **框架解耦**: 适配器应能处理任何异步生成器 (`AsyncIterator`)，不与特定的 LLM 或 Agent 框架绑定。
- **标准化消息**: 定义一套清晰、可扩展的 Pydantic 模型作为前端和后端之间的数据契约。
- **易于使用**: 在 FastAPI 等 Web 框架中集成应尽可能简单。

## 2. 核心设计

我们将设计一个 `SSEAdapter`，它接收一个数据源（异步生成器）和一个消息格式化策略，将其转换为一个标准的 SSE 响应。

### 2.1. 标准化消息模型 (`adapter/sse_models.py`)

首先，定义一套用于 SSE 通信的 Pydantic 模型。这套模型是后端和前端之间的“语言”。

```python
# src/yai_nexus_agentkit/adapter/sse_models.py

import uuid
from enum import Enum
from typing import Any, Dict, List, Literal, Union
from pydantic import BaseModel, Field

class BlockType(str, Enum):
    """数据块类型枚举"""
    TEXT_STREAM = "text.stream"  # 文本流，打字机效果
    TOOL_CALL = "tool.call"      # 工具调用
    TOOL_OUTPUT = "tool.output"  # 工具输出
    ERROR = "error"              # 错误信息

class BaseBlock(BaseModel):
    """所有数据块的基类"""
    block_type: BlockType = Field(..., description="数据块类型")
    block_id: str = Field(default_factory=lambda: f"blk_{uuid.uuid4().hex[:8]}", description="唯一块ID")

class TextStreamBlock(BaseBlock):
    """文本流数据块"""
    block_type: Literal[BlockType.TEXT_STREAM] = BlockType.TEXT_STREAM
    delta: str = Field(..., description="本次增量文本内容")

class ErrorBlock(BaseBlock):
    """错误数据块"""
    block_type: Literal[BlockType.ERROR] = BlockType.ERROR
    message: str = Field(..., description="错误信息")
    code: str = Field("INTERNAL_SERVER_ERROR", description="错误码")

# ... 可以定义更多如 ToolCallBlock, ToolOutputBlock 等

class SSEEvent(BaseModel):
    """SSE 事件的统一格式"""
    event: Literal["message", "finish", "error"] = Field(..., description="事件类型")
    data: Union[BaseBlock, None] = Field(..., description="事件携带的数据")
    conversation_id: str = Field(..., description="当前会话ID")

```

### 2.2. SSE 适配器 (`adapter/sse_adapter.py`)

`SSEAdapter` 是核心组件，它将业务逻辑的输出流适配为 Web 框架可以理解的 SSE 响应流。

```python
# src/yai_nexus_agentkit/adapter/sse_adapter.py

import json
from typing import AsyncIterator, Any
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from .sse_models import TextStreamBlock, ErrorBlock, SSEEvent

class SSEAdapter:
    """
    将任意异步数据流适配为 SSE (Server-Sent Events) 响应。
    """

    def __init__(
        self,
        content_stream: AsyncIterator[Any],
        conversation_id: str,
    ):
        """
        Args:
            content_stream: 从业务逻辑（如LLM客户端）产生的数据流。
                            期望流中的每个项目都是一个简单的字符串 (str)。
            conversation_id: 当前会话的ID。
        """
        self._content_stream = content_stream
        self._conversation_id = conversation_id

    async def _stream_formatter(self) -> AsyncIterator[ServerSentEvent]:
        """内部生成器，将内容流格式化为 SSE 事件。"""
        try:
            # 迭代来自业务逻辑的内容流
            async for chunk in self._content_stream:
                if isinstance(chunk, str):
                    # 将字符串块包装成标准格式
                    block = TextStreamBlock(delta=chunk)
                    event = SSEEvent(
                        event="message",
                        data=block,
                        conversation_id=self._conversation_id
                    )
                    yield ServerSentEvent(
                        event="message",
                        data=event.model_dump_json()
                    )
                # 在这里可以添加对其他类型 chunk 的处理
                # else if isinstance(chunk, ToolCall): ...
            
            # 发送结束信号
            finish_event = SSEEvent(
                event="finish",
                data=None,
                conversation_id=self._conversation_id
            )
            yield ServerSentEvent(
                event="finish",
                data=finish_event.model_dump_json()
            )

        except Exception as e:
            # 格式化并发送错误信号
            error_block = ErrorBlock(message=str(e))
            error_event = SSEEvent(
                event="error",
                data=error_block,
                conversation_id=self._conversation_id
            )
            yield ServerSentEvent(
                event="error",
                data=error_event.model_dump_json()
            )

    def as_event_source_response(self) -> EventSourceResponse:
        """
        将适配器转换为 FastAPI/Starlette 兼容的 EventSourceResponse。
        """
        return EventSourceResponse(
            content=self._stream_formatter(),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )
```

## 3. 目录结构

```
src/yai_nexus_agentkit/
└── adapter/
    ├── __init__.py
    ├── sse_adapter.py     # SSE 适配器核心逻辑
    └── sse_models.py      # SSE 标准消息模型
```

## 4. 使用示例

在 FastAPI 的路由处理函数中，使用 `SSEAdapter` 非常简洁。

```python
# examples/fast_api_app/api/chat.py

from fastapi import APIRouter
from pydantic import BaseModel
from yai_nexus_agentkit.adapter.sse_adapter import SSEAdapter
from yai_nexus_agentkit.core.llm import BaseLLM
# ... 其他依赖

router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str
    conversation_id: str

@router.post("/chat/stream")
async def stream_chat(request: ChatRequest, llm: BaseLLM = Depends(get_llm_client)):
    """
    处理流式聊天请求。
    """
    # 1. 从业务逻辑层获取原始的内容流 (AsyncIterator[str])
    content_stream = llm.astream(
        prompt=request.prompt,
        model="gpt-4o"
    )

    # 2. 使用适配器将其转换为 SSE 响应
    adapter = SSEAdapter(
        content_stream=content_stream,
        conversation_id=request.conversation_id
    )
    
    return adapter.as_event_source_response()
```

## 5. 实施计划

1.  在 `src/yai_nexus_agentkit/adapter/` 目录下创建 `sse_models.py` 并定义消息模型。
2.  创建 `sse_adapter.py` 并实现 `SSEAdapter` 类。
3.  在 `examples/fast_api_app` 中添加一个新的流式API端点 (`/chat/stream`) 来演示其用法。
4.  确保 `SSEAdapter` 的错误处理和流结束逻辑健壮可靠。
5.  编写前端示例代码（或文档）来解释如何消费这种标准的 SSE 流。 