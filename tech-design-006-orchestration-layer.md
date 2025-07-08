
# 技术设计方案: 006-编排层

## 1. 背景

编排层是 Agent 的核心，它负责决策循环：理解用户意图、调用 LLM 思考、使用工具与外部交互、管理状态，并最终给出答案。这是将所有独立组件（LLM、工具、持久化）融合成一个智能实体的“大脑”。

旧代码库 (`old/lucas_ai_core/orchestration/`) 尝试通过 `AgentOrchestrator` 和 `WorkflowManager` 来构建这一层，但这些是自定义的、相对初级的实现。同时，代码中也出现了 `LangGraphSSEHandler`，表明项目已经认识到 `langgraph` 的潜力。

此方案将不再延续旧的编排思路，而是全面拥抱 `langgraph` 作为编排层的核心引擎。`langgraph` 提供了构建有状态、可回溯、可中断的 Agent 所需的全部功能。我们的任务不是重新发明轮子，而是优雅地将其集成到我们的框架中。

设计目标：
- **LangGraph 优先**: 将 `langgraph` 作为构建 Agent 的标准方式。
- **标准化 Agent 结构**: 定义一套构建 Agent 的标准模式和组件，使用户可以轻松构建自己的 Agent。
- **无缝集成**: 将我们已设计的 `LLMFactory`, `ToolExecutor`, `PostgresCheckpoint` 等模块无缝地集成到 `langgraph` 的工作流中。
- **状态与持久化**: 利用 `langgraph` 的检查点 (Checkpoint) 机制，并与我们的 `PostgresCheckpoint` 实现相结合，实现 Agent 状态的自动持久化。

## 2. 核心设计

我们将围绕 `langgraph` 的核心概念（State, Graph, Nodes, Edges）来组织我们的编排层，并将其封装在 `src/yai_nexus_agentkit/orchestration/` 目录下。

### 2.1. Agent 状态 (`orchestration/agent_state.py`)

定义一个标准的 Agent 状态模型。所有在该框架内构建的 Agent 都应使用（或继承）这个状态，以保证互操作性。

```python
# src/yai_nexus_agentkit/orchestration/agent_state.py

from typing import List, TypedDict, Annotated
from langchain_core.messages import BaseMessage
import operator

# `operator.add` 用于让 langgraph 知道如何合并新消息（追加到列表）
class AgentState(TypedDict):
    """Agent 的核心状态"""
    messages: Annotated[List[BaseMessage], operator.add]
    
    # 可以在此扩展更多状态，例如：
    # scratchpad: Any # 用于存储中间思考过程
    # tool_calls: List[dict] # 存储当前的工具调用请求
```

### 2.2. 标准节点 (`orchestration/nodes.py`)

定义一组可复用的、标准的 `langgraph` 节点。这些节点是构成 Agent 思维循环的基本功能单元。

```python
# src/yai_nexus_agentkit/orchestration/nodes.py

from yai_nexus_agentkit.core.llm import BaseLLM
from yai_nexus_agentkit.utilities.tool_executor import ToolExecutor
from .agent_state import AgentState

class StandardNodes:
    """一组标准的、可复用的 langgraph 节点"""

    def __init__(self, llm: BaseLLM, tool_executor: ToolExecutor):
        self._llm = llm
        self._tool_executor = tool_executor

    def call_llm(self, state: AgentState):
        """调用 LLM 进行下一步思考或响应"""
        # 此处简化：实际应将 state.messages 转换为 prompt
        prompt = state["messages"][-1].content
        # 使用绑定的工具 schema 调用 LLM，使其能够决策是否调用工具
        response = self._llm.ainvoke(prompt, tools=self._tool_executor.get_tool_schemas())
        # ... 处理 response，可能包含 tool_calls
        # ... 更新 state['messages']
        return {"messages": [response]}

    async def call_tool(self, state: AgentState):
        """执行工具调用"""
        tool_calls = state["messages"][-1].tool_calls
        tool_outputs = []
        for tool_call in tool_calls:
            output = await self._tool_executor.execute(
                tool_name=tool_call["name"],
                **tool_call["args"]
            )
            tool_outputs.append(output)
        # ... 将 tool_outputs 转换为标准消息格式
        # ... 更新 state['messages']
        return {"messages": tool_outputs}
```

### 2.3. 条件边 (`orchestration/edges.py`)

定义用于路由的条件函数。这些函数根据 LLM 的输出决定工作流的下一站是哪里（例如，是调用工具、还是直接响应用户）。

```python
# src/yai_nexus_agentkit/orchestration/edges.py

from .agent_state import AgentState

def should_continue(state: AgentState) -> str:
    """根据最新消息决定下一步走向"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue_tool"  # 有工具调用，走向工具节点
    else:
        return "end" # 没有工具调用，结束循环
```

### 2.4. Agent 图构建器 (`orchestration/graph_builder.py`)

创建一个构建器，将节点和边组装成一个可执行的 `langgraph` 图。这是对 `langgraph` `StateGraph` 的一层薄封装，提供了构建标准 Agent 的便捷方法。

```python
# src/yai_nexus_agentkit/orchestration/graph_builder.py

from langgraph.graph import StateGraph, END
from .agent_state import AgentState
from .nodes import StandardNodes
from .edges import should_continue

def build_standard_agent_graph(nodes: StandardNodes) -> StateGraph:
    """构建一个标准的 ReAct 风格的 Agent 图"""
    
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("call_llm", nodes.call_llm)
    graph.add_node("call_tool", nodes.call_tool)

    # 定义边的连接关系
    graph.set_entry_point("call_llm")
    
    graph.add_conditional_edges(
        "call_llm",
        should_continue,
        {
            "continue_tool": "call_tool",
            "end": END,
        },
    )
    
    graph.add_edge("call_tool", "call_llm")

    return graph.compile()
```

## 3. 目录结构

```
src/yai_nexus_agentkit/
└── orchestration/
    ├── __init__.py
    ├── agent_state.py      # 标准 Agent 状态定义
    ├── nodes.py            # 标准图节点
    ├── edges.py            # 标准图条件边
    └── graph_builder.py    # Agent 图构建器
```

## 4. 使用示例

将所有组件组装起来，创建一个可运行的 Agent 服务。

```python
# examples/fast_api_app/core/services.py

from yai_nexus_agentkit.core.llm import BaseLLM
from yai_nexus_agentkit.core.checkpoint import BaseCheckpoint
from yai_nexus_agentkit.utilities.tool_executor import ToolExecutor
from yai_nexus_agentkit.orchestration.nodes import StandardNodes
from yai_nexus_agentkit.orchestration.graph_builder import build_standard_agent_graph

# 1. 准备好所有依赖组件 (通过依赖注入)
llm: BaseLLM = ...
tool_executor: ToolExecutor = ...
checkpoint: BaseCheckpoint = ... # 我们的 PostgresCheckpoint 实例

# 2. 注册工具
tool_executor.register_tool(get_current_weather)

# 3. 创建标准节点
nodes = StandardNodes(llm=llm, tool_executor=tool_executor)

# 4. 构建可执行的 Agent 图
#    并将我们的 checkpoint 实现传入
agent_executor = build_standard_agent_graph(nodes).with_checkpoints(checkpoint.saver)

# 5. 在 API 中调用 Agent
# examples/fast_api_app/api/chat.py
@router.post("/agent/invoke")
async def agent_invoke(request: AgentRequest):
    thread_id = request.conversation_id
    inputs = {"messages": [("user", request.prompt)]}
    
    # 配置线程ID，langgraph 会自动处理状态的加载和保存
    config = {"configurable": {"thread_id": thread_id}}
    
    async for event in agent_executor.astream(inputs, config=config):
        # ... 处理流式输出 (可与 SSEAdapter 结合)
        # event 中包含了每个节点的输出
        ...
```

## 5. 实施计划

1.  在 `src/yai_nexus_agentkit/orchestration/` 目录下创建 `agent_state.py`, `nodes.py`, `edges.py`, 和 `graph_builder.py`。
2.  在 `nodes.py` 中，确保与 `LLMFactory` 和 `ToolExecutor` 正确集成。
3.  在 `graph_builder.py` 中，实现一个或多个标准的 Agent 构建函数（如 ReAct Agent, Chat Agent）。
4.  在 `examples/fast_api_app` 中，创建一个新的 `/agent/invoke` 端点，演示如何：
    a.  初始化所有依赖（LLM, Tools, Checkpoint）。
    b.  构建 Agent 执行器。
    c.  使用 `with_checkpoints` 附加持久化能力。
    d.  在 API 调用中传入 `thread_id` 来管理多用户的会话状态。
5.  确保编排层的流式输出可以被 `SSEAdapter` 顺利消费。 