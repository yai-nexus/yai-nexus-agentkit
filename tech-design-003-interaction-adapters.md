
# 技术设计方案: 003-交互适配器

## 1. 背景与最终策略

### 1.1. 初始目标

现代 Agent 应用的核心体验之一是流式响应。Agent 在思考和生成内容时，应能实时地将中间结果和最终内容“打字机”般地输出到前端。Server-Sent Events (SSE) 是实现这一功能的理想技术。

此方案旨在为 `yai-nexus-agentkit` 定义一个标准的、健壮的、面向未来的交互层，用于连接 Agent 后端与前端用户界面。

### 1.2. 演进与最终决策：langgraph + AG-UI 协议 + sse-starlette

在方案探索过程中，我们明确了最佳的技术组合，它兼顾了强大的业务逻辑、标准的交互协议和稳健的传输实现：

- **业务编排层 (`langgraph`)**: 作为 Agent 的“大脑”，负责定义和执行所有复杂的业务逻辑，包括状态管理、工具调用和与 LLM 的多轮交互。
- **数据契约层 (`ag-ui-protocol`)**: 作为 Agent 与前端 UI 之间的“普通话”，提供了一套标准的、与具体实现无关的 Pydantic 事件模型。
- **传输层 (`sse-starlette`)**: 作为 FastAPI 与浏览器之间的“管道”，提供了稳定、高效的 SSE (Server-Sent Events) 连接实现，并内置心跳机制。

**最终决策：不采用任何大而全的 Agent 框架（如 `pydantic-ai`），而是通过上述三个库的组合，构建一个分层清晰、高度解耦的交互架构。**

这个决策的优势是：
- **关注点分离 (SoC)**: 每个库只做一件事，并做到最好，使得架构清晰、易于维护。
- **灵活性与可扩展性**: 我们可以完全掌控 Agent 的内部逻辑 (`langgraph`) 和 API 的行为，不受任何上层框架的限制。
- **遵循开放标准**: `ag-ui-protocol` 确保了与前端社区的互操作性。

## 2. 核心设计：三层协作模型

我们的交互层将由三个紧密协作的组件构成。

### 2.1. Langgraph Agent (业务逻辑核心)
- Agent 的所有业务逻辑，包括调用 LLM、使用工具、维护状态等，全部在 `langgraph` 中定义。
- 我们将主要使用 `langgraph` 的 `astream_events()` 方法，它会实时地、异步地产生 Agent 执行过程中的各种内部事件（如 `on_chat_model_stream`, `on_tool_start`, `on_tool_end` 等）。

### 2.2. AG-UI Protocol (标准化事件模型)
- 我们将使用 `ag-ui-protocol` 包中定义的 Pydantic 模型（如 `Text`, `Message`, `State`, `Task`）作为 API 的数据格式。
- 我们的核心任务是编写一个**适配器 (Adapter)**，将 `langgraph` 的内部事件流，实时翻译成 `ag-ui-protocol` 的标准事件流。

### 2.3. SSE-Starlette (SSE 传输实现)
- 在 FastAPI 中，我们将使用 `sse-starlette` 提供的 `EventSourceResponse`。
- `EventSourceResponse` 接收一个异步生成器（也就是我们的适配器），并自动处理 SSE 协议的所有细节，包括正确的MIME类型、事件格式化和连接保持（keep-alive）。

## 3. 依赖

需要在 `pyproject.toml` 的 `[project.optional-dependencies]` 中为 `fastapi` 分组添加以下依赖：

```toml
# Web Adapter Helpers
fastapi = [
    "fastapi", 
    "uvicorn", 
    "ag-ui-protocol", # AG-UI 标准事件模型
    "sse-starlette"   # FastAPI 的 SSE 传输支持
]
```

## 4. 使用示例：在 FastAPI 中集成

集成过程清晰明了，展示了各层如何协作。

```python
# examples/fast_api_app/api/chat.py

import json
from typing import AsyncGenerator

from fastapi import APIRouter
# 从 sse-starlette 导入 EventSourceResponse
from sse_starlette.sse import EventSourceResponse

# 从 ag-ui-protocol 导入事件模型
from ag_ui.core.events import Text, State, Task, Error

# 从项目中导入预先构建好的 langgraph agent (此处为示意)
# from yai_nexus_agentkit.orchestration import agent as langgraph_agent
from some_mock_agent import langgraph_agent # 使用一个模拟 agent 代替

router = APIRouter(prefix="/api")


# 核心：事件流适配器 (Async Generator)
async def event_stream_adapter(task: Task) -> AsyncGenerator[str, None]:
    """
    调用 langgraph Agent，监听其事件流，并将其适配为 AG-UI 格式的 SSE 事件。
    """
    try:
        # 步骤 1: 产生 AG-UI 的 "开始" 事件
        yield json.dumps(State(status="running").model_dump())

        # 步骤 2: 调用 langgraph Agent 的流式事件接口
        async for event in langgraph_agent.astream_events(
            {"messages": [("user", task.query)]}, 
            version="v1"  # 确保使用的是有状态的执行
        ):
            kind = event["event"]
            
            # 步骤 3: 将 langgraph 事件翻译为 AG-UI 事件
            if kind == "on_chat_model_stream":
                # 这是 LLM 的流式输出
                content = event["data"]["chunk"].content
                if content:
                    # 产生 AG-UI 的 "文本块" 事件
                    yield json.dumps(Text(content=content).model_dump())
            
            # TODO: 在此处可以添加对 on_tool_start, on_tool_end 等事件的适配
            # elif kind == "on_tool_start":
            #     yield json.dumps(ToolCall(...).model_dump())

        # 步骤 4: 产生 AG-UI 的 "完成" 事件
        yield json.dumps(State(status="done").model_dump())

    except Exception as e:
        # 步骤 5: 如果发生错误，产生 AG-UI 的 "错误" 事件
        error_payload = {"message": "An unexpected error occurred", "details": str(e)}
        yield json.dumps(Error(code="INTERNAL_SERVER_ERROR", **error_payload).model_dump())
        yield json.dumps(State(status="error").model_dump())


# API 端点
@router.post("/chat/stream")
async def chat_stream_endpoint(task: Task):
    """
    接收 AG-UI Task，返回一个标准的 SSE 流。
    """
    # 将适配器生成器传递给 EventSourceResponse，它会处理所有 SSE 细节
    return EventSourceResponse(
        event_stream_adapter(task),
        ping=15, # 每 15 秒发送一次心跳以保持连接
        media_type="text/event-stream"
    )

```

## 5. 实施计划（已更新）

1.  **更新依赖**:
    -   在 `pyproject.toml` 的 `fastapi` 可选依赖中，确认已添加 `ag-ui-protocol` 和 `sse-starlette`。
    -   移除 `pydantic-ai` 或其他不再需要的依赖。
    -   运行 `pip install -e ".[fastapi]"` 安装依赖。
2.  **实现 `langgraph` Agent**:
    -   在 `yai_nexus_agentkit` 中构建一个或多个 `langgraph` Agent，并能通过工厂或单例模式在 API 层访问到。
3.  **实现 API 端点与适配器**:
    -   在 `examples/fast_api_app/api/chat.py` 中，按照上面的示例创建 `chat_stream_endpoint` 路由。
    -   实现 `event_stream_adapter` 生成器函数，完成从 `langgraph` 事件到 `ag-ui-protocol` 事件的映射。
4.  **编写测试**:
    -   为 `event_stream_adapter` 编写单元测试，验证其事件转换逻辑的正确性。
    -   为 FastAPI 端点编写集成测试，确保 SSE 流能被正确消费。
5.  **前端对接**:
    -   与前端开发人员同步，提供此标准的 AG-UI 端点，以便他们可以使用任何兼容的客户端库进行对接。

通过这个分层、解耦的架构，我们为构建复杂、健壮且面向未来的 AI 应用打下了坚实的基础。 