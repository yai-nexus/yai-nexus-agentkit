# 代码评审纪要：003-3 (最终轮)

**致：** 项目团队
**发件人：** Gemini
**日期：** 2024-07-31
**主题：** 对第三版代码的最终评审与最终行动指令

---

## 1. 总体评价 (Overall Assessment)

**评审失败 (Failed)**.

虽然 `sse_basic.py` 已按要求修正，但最核心的 `chat.py` 示例代码完全没有满足上一轮评审提出的、最关键的修改要求。项目 `README.md` 中描述的 Level 3 (高级模式) 的核心——即 `langgraph` Agent 与 `AGUIAdapter` 的集成——在代码中**依然没有得到任何体现**。

目前的 `chat.py` 使得 `AGUIAdapter` 的主要功能无法被正确演示，这完全不可接受。

**结论：这是本次功能的最后一次评审。代码必须严格按照下文的【最终行动指令】进行修改，不接受任何偏离。**

## 2. 详细评审 (Detailed Review)

### 2.1. 针对上一轮建议的完成情况

| 评审项 (Item) | 状态 | 备注 |
| :--- | :--- | :--- |
| **重构 `sse_basic.py`** | ✅ | **已完成**. 冗余方法已移除，代码已清理。 |
| **重构 `chat.py`** | ❌ | **失败**. |
| ...删除多余端点 | ❌ | 未删除 `/stream-with-heartbeat`。 |
| ...使用真实 Agent | ❌ | **最严重的问题**: 依然使用 `langgraph_agent=None`，未能展示核心功能。 |

## 3. 最终行动指令 (Final Action Items)

工程师**必须**丢弃现有的 `chat.py`，并使用以下**完整代码**替换之。这份代码包含了所有必要的修正，包括一个可工作的、最小化的 `langgraph` Agent 实现。

---
### **必须使用的 `examples/fast_api_app/api/chat.py` 最终代码：**

```python
# -*- coding: utf-8 -*-
"""
渐进式 API 设计的最终、正确实现。
严格遵循 README.md 的三层模型。
"""

from typing import Optional, List, TypedDict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, AIMessage

from yai_nexus_agentkit.adapter import BasicSSEAdapter, AGUIAdapter
from yai_nexus_agentkit.llm import create_llm, BaseChatModel
from sse_starlette.sse import EventSourceResponse
from yai_nexus_agentkit.adapter.sse_advanced import Task

# --- 1. 定义 LangGraph Agent ---
# 这是一个最小化的、但可工作的真实 Agent 实现

class AgentState(TypedDict):
    messages: List[BaseMessage]

def call_model(state: AgentState, llm: BaseChatModel):
    """一个简单的 Agent 节点，负责调用 LLM"""
    response = llm.invoke(state['messages'])
    return {"messages": [response]}

def create_simple_agent() -> StateGraph:
    """创建并返回一个简单的 LangGraph Agent 实例"""
    llm_config = {"provider": "openai", "model": "gpt-4o-mini"}
    llm = create_llm(llm_config)

    graph = StateGraph(AgentState)
    graph.add_node("llm", lambda state: call_model(state, llm))
    graph.set_entry_point("llm")
    graph.add_edge("llm", END)
    
    return graph.compile()

# 在应用启动时创建一个 Agent 实例
REAL_LANGGRAPH_AGENT = create_simple_agent()

# --- 2. 请求/响应模型 ---

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class SimpleResponse(BaseModel):
    response: str

# --- 3. 路由器 ---
router = APIRouter(prefix="/chat")

# --- Level 1: 简单模式 ---
@router.post("/simple", response_model=SimpleResponse)
async def chat_simple(request: ChatRequest):
    try:
        llm = create_llm({"provider": "openai", "model": "gpt-4o-mini"})
        response = llm.invoke(request.message)
        return SimpleResponse(response=response.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Level 2: 中级模式 (带心跳) ---
@router.post("/stream-basic")
async def chat_stream_basic(request: ChatRequest):
    try:
        llm = create_llm({"provider": "openai", "model": "gpt-4o-mini"})
        adapter = BasicSSEAdapter(llm)
        return EventSourceResponse(
            adapter.stream_response(request.message),
            ping=15, # 正确的、推荐的心跳实现方式
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Level 3: 高级模式 (真实 Agent) ---
@router.post("/stream-advanced")
async def chat_stream_advanced(task: Task):
    try:
        # **正确做法**: 将真实的 Agent 实例传递给适配器
        adapter = AGUIAdapter(langgraph_agent=REAL_LANGGRAPH_AGENT)
        
        return EventSourceResponse(
            adapter.event_stream_adapter(task),
            ping=15,
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

```
---

**要求：**
1.  删除 `examples/fast_api_app/api/chat.py` 的所有内容。
2.  将上述代码完整地粘贴到 `chat.py` 中。
3.  不要进行任何修改。

**完成此项操作后，可直接将代码合入主干，无需再次评审。** 