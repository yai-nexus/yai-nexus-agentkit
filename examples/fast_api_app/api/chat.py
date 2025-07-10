# -*- coding: utf-8 -*-
"""
渐进式 API 设计示例
展示简单、中级、高级三个层次的流式响应 API
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from yai_nexus_agentkit.adapter import BasicSSEAdapter, AGUIAdapter
from yai_nexus_agentkit import LLMFactory, LLMProvider, LLMConfig

# 核心依赖 - 直接导入
from sse_starlette.sse import EventSourceResponse
from yai_nexus_agentkit.adapter.sse_advanced import Task

# Langgraph 依赖
from langgraph.prebuilt import create_react_agent


# --- 请求/响应模型 ---
class ChatRequest(BaseModel):
    """通用聊天请求模型"""

    message: str
    user_id: Optional[str] = None


class SimpleResponse(BaseModel):
    """简单模式响应"""

    response: str


# --- 路由器 ---
router = APIRouter(prefix="/chat")


# --- Langgraph Agent 工厂函数 ---
def create_langgraph_agent(llm_client):
    """
    创建 langgraph Agent 实例
    使用 create_react_agent 创建一个简单的反应式 Agent
    """
    try:
        # 创建一个简单的反应式 Agent
        # 暂时不添加工具，只使用基础的 LLM 功能
        tools = []  # 可以在这里添加工具

        # 使用 langgraph 的 create_react_agent 创建 Agent
        agent = create_react_agent(llm_client, tools)

        return agent

    except Exception as e:
        # 如果 langgraph Agent 创建失败，记录错误并重新抛出
        raise RuntimeError(f"Failed to create langgraph agent: {str(e)}")


# --- 1. 简单模式：直接 LLM 调用 ---
@router.post("/simple", response_model=SimpleResponse)
async def chat_simple(request: ChatRequest):
    """
    简单模式：直接返回 LLM 响应，无流式处理
    适合：基础聊天功能，简单集成
    """
    try:
        # 这里应该从依赖注入获取 LLM 客户端
        # 暂时使用硬编码配置做演示
        factory = LLMFactory()
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            api_key="your-api-key",  # 实际使用时从环境变量获取
        )
        factory.register_config("simple-chat", llm_config)
        llm = factory.get_llm_client("simple-chat")

        # 同步调用 LLM
        response = llm.invoke(request.message)
        return SimpleResponse(response=response.content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 2. 中级模式：基础 SSE 流式响应 ---
@router.post("/stream-basic")
async def chat_stream_basic(request: ChatRequest):
    """
    中级模式：基础 SSE 流式响应
    适合：需要流式体验但不需要复杂协议的场景
    """
    try:
        # 创建 LLM 客户端
        factory = LLMFactory()
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI, model="gpt-4o-mini", api_key="your-api-key"
        )
        factory.register_config("stream-basic", llm_config)
        llm = factory.get_llm_client("stream-basic")

        # 创建基础 SSE 适配器
        adapter = BasicSSEAdapter(llm)

        # 返回 SSE 响应
        return EventSourceResponse(
            adapter.stream_response(request.message), media_type="text/event-stream"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 3. 高级模式：完整 AG-UI 协议 ---
@router.post("/stream-advanced")
async def chat_stream_advanced(task: Task):
    """
    高级模式：完整的 AG-UI 协议支持
    适合：需要标准化事件模型和复杂交互的场景
    """
    try:
        # 创建 LLM 客户端
        factory = LLMFactory()
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI, model="gpt-4o-mini", api_key="your-api-key"
        )
        factory.register_config("stream-advanced", llm_config)
        llm_client = factory.get_llm_client("stream-advanced")

        # 创建真实的 langgraph Agent 实例
        try:
            langgraph_agent = create_langgraph_agent(llm_client)
        except RuntimeError as agent_error:
            # 如果 langgraph Agent 创建失败，降级到 LLM 后备方案
            langgraph_agent = None
            print(f"Warning: {agent_error}. Falling back to LLM client.")

        # 创建 AG-UI 适配器（使用真实的 langgraph Agent 或 LLM 后备）
        adapter = AGUIAdapter(langgraph_agent=langgraph_agent, llm_client=llm_client)

        # 返回 AG-UI 兼容的 SSE 响应
        return EventSourceResponse(
            adapter.event_stream_adapter(task),
            ping=15,  # 心跳间隔
            media_type="text/event-stream",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 4. 功能检查端点 ---
@router.get("/capabilities")
async def get_capabilities():
    """
    返回当前 API 支持的功能
    """
    return {
        "simple_mode": True,
        "sse_basic": True,
        "ag_ui_protocol": True,
        "dependencies": {"sse_starlette": True, "ag_ui_protocol": True},
    }
