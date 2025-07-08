
# 技术设计方案: 003-交互适配器

## 1. 背景与最终策略

### 1.1. 初始目标

现代 Agent 应用的核心体验之一是流式响应。Agent 在思考和生成内容时，应能实时地将中间结果和最终内容“打字机”般地输出到前端。Server-Sent Events (SSE) 是实现这一功能的理想技术。

此方案旨在为 `yai-nexus-agentkit` 定义一个标准的、健壮的、面向未来的交互层，用于连接 Agent 后端与前端用户界面。

### 1.2. 演进与最终决策：采纳 AG-UI 协议

在初步设计中，我们曾计划自研一个 `SSEAdapter` 来封装流式响应逻辑。然而，经过进一步的社区调研和评审，我们发现了一个更优越的策略：**直接集成 AG-UI (Agent-User Interaction) 协议**。

AG-UI 是一个旨在**标准化前端应用与 AI Agent 之间连接方式**的开放协议。它提供了一套丰富的、标准化的事件词汇表，用于描述 Agent 在执行任务时的各种状态（如思考、工具调用、生成文本等），并提供了官方的 Python SDK。

**最终决策：废弃自研适配器方案，全面采纳并集成官方 `ag-ui` Python SDK。**

这一决策的优势是压倒性的：
- **遵循开放标准**: 确保我们的实现与一个不断发展的社区标准完全兼容，具备强大的互操作性。
- **避免重复造轮子**: 直接利用官方 SDK 的健壮功能，包括事件模型、SSE 传输、框架集成等。
- **降低维护成本**: 协议的演进将由社区和 SDK 维护者负责，我们只需更新依赖即可。
- **赋能丰富的前端体验**: 标准化的事件流允许前端构建出信息更丰富、交互性更强的用户界面。

## 2. 核心设计：基于 AG-UI SDK

我们的交互层将不再包含自定义的适配器代码，而是完全基于 `ag-ui` 库。

### 2.1. 核心概念

- **AG-UI 服务器**: 我们将使用 `ag-ui` 提供的工具，在 FastAPI 应用中快速启动一个符合协议的服务器。
- **Agent 回调**: 我们需要实现一个核心的 Agent 函数（回调），它接收用户请求，并 `yield` 出符合 AG-UI 规范的事件对象。
- **标准事件模型**: 我们将直接使用 `ag-ui` SDK 中定义的 Pydantic 模型来表示各种事件，例如 `Message`, `Text`, `State`, `Tools`, `ToolOutput` 等。业务逻辑（如 `llm.astream`）的输出将被重构，以生成这些标准化的事件对象。

### 2.2. 依赖

需要在 `pyproject.toml` 中添加 `ag-ui` 作为核心依赖。

```toml
[project.dependencies]
# ... 其他依赖
ag-ui = "^0.1.0" # 版本号待定
```

## 3. 使用示例：在 FastAPI 中集成 AG-UI

集成过程非常简洁。我们不再需要手动管理 SSE 响应，`ag-ui` SDK 会处理所有底层细节。

```python
# examples/fast_api_app/api/chat.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import AsyncGenerator

# 从 AG-UI SDK 导入所需的组件
from ag_ui.server import run_in_thread, AgentUI
from ag_ui.models import Message, Text, State, Node, Edge, Task, Error
from yai_nexus_agentkit.core.llm import BaseLLM, get_llm_client # 假设的业务逻辑

# 1. 初始化 FastAPI 应用
app = FastAPI()

# 2. 定义 Agent 的核心处理逻辑
# 这个函数将作为 Agent 的回调，处理用户请求并产生事件流
async def my_agent_callback(task: Task, llm: BaseLLM) -> AsyncGenerator[Node, None]:
    """
    一个符合 AG-UI 规范的 Agent 回调函数。
    它接收一个任务对象，并异步地产生一系列事件节点。
    """
    try:
        # 产生一个 "正在执行" 的状态更新
        yield State(status="running")
        
        # 从业务逻辑层获取原始的内容流 (这里需要进行适配)
        # 假设 llm.astream 现在 yield str
        content_stream = llm.astream(
            prompt=task.query, # task.query 包含了用户的输入
            model="gpt-4o"
        )
        
        full_response = ""
        # 产生 "思考" 事件
        yield Text("正在思考...")

        # 将业务逻辑的输出流适配为 AG-UI 事件
        async for chunk in content_stream:
            if isinstance(chunk, str):
                full_response += chunk
                # 产生增量文本流事件
                yield Text(content=chunk)
        
        # 产生一个包含最终结果的消息事件
        yield Message(id=task.id, role="assistant", content=full_response)
        
        # 产生一个 "完成" 状态更新
        yield State(status="done")

    except Exception as e:
        # 产生错误事件
        yield Error(message=str(e), code="INTERNAL_SERVER_ERROR")
        # 确保流结束时状态为 "error"
        yield State(status="error")


# 3. 创建 AgentUI 实例并注册到 FastAPI
# a) 创建一个工厂函数来传递依赖（如 LLM客户端）
def agent_factory():
    llm_client = get_llm_client() # 获取 LLM 客户端实例
    
    # 偏函数，将 llm_client 注入到回调中
    from functools import partial
    return partial(my_agent_callback, llm=llm_client)

# b) 创建 AgentUI 实例
# 这里的 "my-agent" 是 agent_id，前端可以通过它来选择要连接的 Agent
agent_ui = AgentUI(agent_id="my-agent", agent_fn=agent_factory)

# c) 将 AgentUI 的路由挂载到 FastAPI 应用中
app.include_router(agent_ui.router)

# 4. (可选) 在后台线程中运行 AgentUI 的消息处理
# 这对于需要 Agent 主动向前端推送消息的场景很有用
run_in_thread(agent_ui)

```

## 4. 实施计划（已更新）

1.  **添加依赖**: 在 `pyproject.toml` 中添加 `ag-ui` 库。
2.  **移除旧代码**: 从项目中删除所有自研的 `sse_adapter.py` 和 `sse_models.py` 相关的代码和设计。
3.  **适配业务逻辑**:
    -   审查核心的流式产出模块（如 `llm.astream`）。
    -   将其返回值从简单的 `AsyncIterator[str]` 重构为 `AsyncIterator[Union[str, BaseBlock]]` 或直接输出 `ag_ui.models` 中的标准事件对象。这是为了能够生成更丰富的事件类型，如工具调用、状态变更等。
4.  **集成 AG-UI 路由**:
    -   在 `examples/fast_api_app` 中，按照上面的示例，创建并挂载 `AgentUI` 的路由。
    -   实现 `agent_factory` 来处理依赖注入。
5.  **前端对接**: 与前端开发人员同步，确保他们了解现在后端暴露的是一个标准的 AG-UI 端点，并可以利用其丰富的事件来进行 UI 开发。
6.  **编写测试**: 为新的 `my_agent_callback` 逻辑编写单元测试，并为 FastAPI 端点编写集成测试。

通过采纳 AG-UI SDK，我们不仅简化了实现，还站在了行业标准的前沿，为构建下一代 AI 应用打下了坚实的基础。 