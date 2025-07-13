# 方案：使用 `AGUIAdapter` 重构 Python 后端（增强版）

## 1. 目标

本文档旨在指导开发者将 `examples/python-backend/main.py` 中的 FastAPI 后端进行重构。我们将使用 `yai_nexus_agentkit` 包中的 `AGUIAdapter`，以一种更健壮、更现代的方式来提供 Agent 服务，完全替代现有的手动 SSE 事件流生成逻辑。

## 2. 背景与收益

当前的 `main.py` 中的 `/invoke` 端点通过辅助函数手动构建 SSE 事件流。这种方式虽然能工作，但存在以下缺点：

- **代码冗余**: 需要手动创建、序列化和发送每一个事件。
- **维护困难**: 当 AG-UI 协议更新或需要支持更多事件类型时，需要修改大量代码。
- **功能受限**: 无法简单地对接 `langgraph` 等高级 Agent 框架的复杂事件流。

`AGUIAdapter` 是一个高级适配器，它能够自动将 `langgraph` 的事件流转换为完全符合 AG-UI 协议的 SSE 事件流。

**重构后的收益**:

- **简化代码**: 只需关注 Agent 的核心逻辑，事件转换完全自动化。
- **提升可维护性**: `AGUIAdapter` 内部处理了所有事件转换细节。
- **无缝集成 LangGraph**: 轻松利用 `langgraph` 的强大功能，如工具调用、状态管理等。
- **增强健壮性**: 内置统一的错误处理机制，自动上报 `RunErrorEvent`。
- **协议一致性**: 确保与 AG-UI 前端协议的完全兼容。

## 3. 重构步骤

### 步骤 1: 更新依赖

为了使用最新版的 `AGUIAdapter` 并创建一个能调用 LLM 的 Agent，我们需要更新并添加 `langgraph` 和相关的 `langchain` 库。

**文件**: `examples/python-backend/requirements.txt`

```diff
 fastapi==0.111.0
 uvicorn[standard]==0.34.1
 pydantic>=2.11.2
 python-multipart==0.0.20
 ag-ui-protocol
 python-dotenv>=1.0.0
 -e ../../packages/agentkit
 -e ../../packages/agentkit
 langgraph>=0.5.2
 langchain-core>=0.3.68
 langchain-openai>=0.3.27
 sse-starlette>=2.1.0

```
*注意：我们添加了 `sse-starlette` 到依赖中，以确保其可用性。*

### 步骤 2: 在 `main.py` 中添加 Agent 和 Adapter

我们将重构 `main.py`，引入一个真正调用 LLM 的 Agent，并通过 `AGUIAdapter` 将其集成到 FastAPI 中。

**文件**: `examples/python-backend/main.py`

**A. 整理并添加导入语句**

在文件顶部，清理旧的导入并添加新模块。这有助于保持代码整洁和遵循规范。

```python
#!/usr/bin/env python3
"""
Python backend example for yai-nexus-fekit, using AGUIAdapter.
"""
import os
import uuid
from typing import TypedDict, Annotated, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

# 核心依赖
from ag_ui.core import RunAgentInput
from yai_nexus_agentkit.adapter.sse_advanced import AGUIAdapter, Task
from yai_nexus_agentkit.core.logger_config import LoggerConfigurator, get_logger
from logging_strategies import HourlyDirectoryStrategy
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
```

**B. 增加启动时环境变量检查**

为了确保服务能正常运行，我们在启动时检查 `OPENAI_API_KEY` 是否已设置。

在 `setup_logging` 函数下方添加：

```python
def check_environment_variables():
    """检查必要的环境变量是否已设置"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        module_logger.error("FATAL: OPENAI_API_KEY environment variable is not set.")
        raise ValueError("OPENAI_API_KEY is required to run the application.")
    module_logger.info("OPENAI_API_KEY is configured.")

# 初始化日志系统和环境检查
module_logger = setup_logging()
check_environment_variables()
```

**C. 定义一个真正的 LLM Agent**

我们将创建一个调用 `ChatOpenAI` 的 Agent，而不仅仅是 Echo。

```python
# --- LangGraph Agent Definition ---

class AgentState(TypedDict):
    """定义 Agent 的状态，包含消息列表"""
    messages: Annotated[List[BaseMessage], add_messages]

# 创建 LangChain LLM 实例
llm = ChatOpenAI(model="gpt-4o")

# 定义 Agent 节点，该节点将调用 LLM
def llm_agent_node(state: AgentState) -> dict:
    """调用 LLM 并返回其响应"""
    module_logger.info("LLM Agent node is processing the state.")
    return {"messages": [llm.invoke(state["messages"])]}

# 创建 Agent 的图 (Graph)
graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", llm_agent_node)
graph_builder.set_entry_point("agent")
graph_builder.set_finish_point("agent")

# 编译图，得到可运行的 Agent
agent = graph_builder.compile()

# --- AGUIAdapter Instantiation ---
# 使用编译好的 Agent 实例化适配器
agui_adapter = AGUIAdapter(agent=agent)
```

### 步骤 3: 重构 API 端点

现在，我们将彻底重构 `/invoke` 端点，并移除不再需要的旧代码。

**A. 删除不再需要的代码**

- 删除整个 `generate_streaming_response` 函数。
- 删除 `/test` 端点及其相关的 `MessageRequest` 模型，因为它们不再需要。

**B. 重构 `/invoke` 端点**

用 `AGUIAdapter` 的能力重写 `invoke_agent` 函数。

```python
@app.post("/invoke")
async def invoke_agent(request_data: RunAgentInput, request: Request):
    """
    接收 AG-UI 标准输入，并使用 AGUIAdapter 返回流式响应。
    """
    req_logger = request.state.logger.bind(
        run_id=request_data.run_id,
        thread_id=request_data.thread_id,
        endpoint="/invoke"
    )

    try:
        req_logger.info("Received agent invoke request",
                       message_count=len(request_data.messages))

        if not request_data.messages:
            raise HTTPException(status_code=400, detail="Request body must contain 'messages' array.")

        last_message = request_data.messages[-1]
        if not last_message.content.strip():
            raise HTTPException(status_code=400, detail="The last message must have non-empty 'content'.")

        # 创建 Adapter 需要的 Task 对象
        task = Task(
            id=request_data.run_id or f"run_{uuid.uuid4().hex}",
            query=last_message.content,
            thread_id=request_data.thread_id or f"thread_{uuid.uuid4().hex}"
        )

        req_logger.info("Forwarding task to AGUIAdapter", task_id=task.id, thread_id=task.thread_id)

        # AGUIAdapter 会自动处理事件流生成和错误捕获
        return EventSourceResponse(
            agui_adapter.event_stream_adapter(task),
            ping=15,
            media_type="text/event-stream"
        )

    except HTTPException as http_exc:
        # 重新抛出 HTTP 异常，让 FastAPI 处理
        raise http_exc
    except Exception as e:
        # 对于其他所有异常，记录并返回一个标准的 500 错误
        req_logger.exception(
            "An unexpected error occurred in /invoke endpoint",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

```

## 4. 验证

1.  **安装依赖**: 在 `examples/python-backend` 目录下运行 `pip install -r requirements.txt --upgrade`。
2.  **设置环境变量**:
    - 在 `.env` 文件或系统环境中设置有效的 `OPENAI_API_KEY`。
3.  **启动后端**: 运行 `python examples/python-backend/main.py`。
4.  **启动前端**: 在项目根目录运行 `pnpm dev:example:next`。
5.  **测试场景**:
    - **成功场景**:
        - 打开 `http://localhost:3000`，在聊天框中输入 "你好"。
        - **预期行为**: 聊天机器人应返回由 GPT-4o 生成的回复，内容流畅且相关。
        - **日志检查**: 后端控制台应显示 `LLM Agent node is processing the state` 和 `Forwarding task to AGUIAdapter` 等日志。
    - **错误场景 (API Key 未设置)**:
        - 停止后端，取消设置 `OPENAI_API_KEY`。
        - 重新启动后端。
        - **预期行为**: 服务启动失败，控制台会打印 `FATAL: OPENAI_API_KEY environment variable is not set.` 并抛出异常。
    - **错误场景 (LLM 调用失败)**:
        - (模拟) 如果 LLM 服务暂时不可用或返回错误。
        - **预期行为**: 前端聊天界面应能优雅地展示错误信息。`AGUIAdapter` 会自动发送一个 `RunErrorEvent`，前端 `fekit` 能够捕获并显示它。后端日志会记录下详细的异常信息。

## 5. 总结

通过以上步骤，我们不仅用 `AGUIAdapter` 替换了手动的 SSE 实现，还显著提升了示例应用的健壮性、可维护性和功能完整性。这为后续开发更复杂的 Agent 应用打下了坚实的基础。