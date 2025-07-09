# -*- coding: utf-8 -*-
"""
渐进式 API 设计示例
展示简单、中级、高级三个层次的流式响应 API
"""

import json
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from yai_nexus_agentkit.adapter import BasicSSEAdapter, AGUIAdapter, LanggraphAgentMock
from yai_nexus_agentkit.llm import create_llm

# 尝试导入可选依赖
try:
    from sse_starlette.sse import EventSourceResponse
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False

try:
    from ag_ui.core.events import Task
    AG_UI_AVAILABLE = True
except ImportError:
    AG_UI_AVAILABLE = False
    # 创建模拟的 Task 类型
    class Task(BaseModel):
        id: str
        query: str


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
        llm_config = {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "your-api-key"  # 实际使用时从环境变量获取
        }
        llm = create_llm(llm_config)
        
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
    if not SSE_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="SSE support not available. Install with: pip install sse-starlette"
        )
    
    try:
        # 创建 LLM 客户端
        llm_config = {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "your-api-key"
        }
        llm = create_llm(llm_config)
        
        # 创建基础 SSE 适配器
        adapter = BasicSSEAdapter(llm)
        
        # 返回 SSE 响应
        return EventSourceResponse(
            adapter.stream_response(request.message),
            media_type="text/event-stream"
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
    if not AG_UI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="AG-UI protocol not available. Install with: pip install ag-ui-protocol"
        )
    
    if not SSE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="SSE support not available. Install with: pip install sse-starlette"
        )
    
    try:
        # 创建模拟的 langgraph agent（实际使用时应该从依赖注入获取）
        mock_agent = LanggraphAgentMock()
        
        # 创建 AG-UI 适配器
        adapter = AGUIAdapter(mock_agent)
        
        # 返回 AG-UI 兼容的 SSE 响应
        return EventSourceResponse(
            adapter.event_stream_adapter(task),
            ping=15,  # 心跳间隔
            media_type="text/event-stream"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 4. 带心跳的中级模式 ---
@router.post("/stream-with-heartbeat")
async def chat_stream_with_heartbeat(request: ChatRequest):
    """
    带心跳的中级模式
    适合：需要长连接保持的场景
    """
    if not SSE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="SSE support not available. Install with: pip install sse-starlette"
        )
    
    try:
        llm_config = {
            "provider": "openai", 
            "model": "gpt-4o-mini",
            "api_key": "your-api-key"
        }
        llm = create_llm(llm_config)
        
        adapter = BasicSSEAdapter(llm)
        
        return EventSourceResponse(
            adapter.stream_with_heartbeat(request.message, heartbeat_interval=30),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 5. 功能检查端点 ---
@router.get("/capabilities")
async def get_capabilities():
    """
    返回当前 API 支持的功能
    """
    return {
        "simple_mode": True,
        "sse_basic": SSE_AVAILABLE,
        "ag_ui_protocol": AG_UI_AVAILABLE,
        "dependencies": {
            "sse_starlette": SSE_AVAILABLE,
            "ag_ui_protocol": AG_UI_AVAILABLE
        }
    }