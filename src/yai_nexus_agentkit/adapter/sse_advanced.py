# -*- coding: utf-8 -*-
"""
高级模式：完整三层架构（langgraph + AG-UI + sse-starlette）
按照设计文档实现标准的 AG-UI 协议适配器
"""

import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional, Union
from pydantic import BaseModel

# 这些导入在安装 ag-ui-protocol 后会可用
try:
    from ag_ui.core.events import Text, Message, State, Task, Error
    AG_UI_AVAILABLE = True
except ImportError:
    AG_UI_AVAILABLE = False
    # 创建模拟的类型定义
    class Text(BaseModel):
        content: str
    
    class Message(BaseModel):
        id: str
        role: str
        content: str
    
    class State(BaseModel):
        status: str
    
    class Task(BaseModel):
        id: str
        query: str
    
    class Error(BaseModel):
        code: str
        message: str
        details: Optional[str] = None


class AGUIAdapter:
    """
    高级 AG-UI 协议适配器
    将 langgraph 事件流转换为 AG-UI 标准事件流
    """
    
    def __init__(self, langgraph_agent=None):
        self.langgraph_agent = langgraph_agent
        if not AG_UI_AVAILABLE:
            print("警告: ag-ui-protocol 未安装，使用模拟实现")
    
    async def event_stream_adapter(self, task: Task) -> AsyncGenerator[str, None]:
        """
        核心事件流适配器
        将 langgraph Agent 事件流转换为 AG-UI 格式的 SSE 事件
        
        Args:
            task: AG-UI 任务对象
            
        Yields:
            JSON 格式的 AG-UI 事件字符串
        """
        try:
            # 步骤 1: 产生 AG-UI 的 "开始" 事件
            yield json.dumps(State(status="running").model_dump())
            
            if self.langgraph_agent is None:
                # 如果没有 langgraph agent，使用简单的 LLM 流式响应
                yield from self._simple_llm_stream(task)
                return
            
            # 步骤 2: 调用 langgraph Agent 的流式事件接口
            async for event in self.langgraph_agent.astream_events(
                {"messages": [("user", task.query)]}, 
                version="v1"
            ):
                kind = event["event"]
                
                # 步骤 3: 将 langgraph 事件翻译为 AG-UI 事件
                if kind == "on_chat_model_stream":
                    # LLM 的流式输出
                    content = event["data"]["chunk"].content
                    if content:
                        yield json.dumps(Text(content=content).model_dump())
                
                elif kind == "on_tool_start":
                    # 工具开始调用
                    tool_name = event["data"].get("input", {}).get("tool", "unknown")
                    yield json.dumps(State(status="tool_calling", tool=tool_name).model_dump())
                
                elif kind == "on_tool_end":
                    # 工具调用完成
                    yield json.dumps(State(status="tool_completed").model_dump())
                
                # 可以添加更多事件类型的处理
                # elif kind == "on_chain_start":
                # elif kind == "on_chain_end":
            
            # 步骤 4: 产生 AG-UI 的 "完成" 事件
            yield json.dumps(State(status="done").model_dump())
            
        except Exception as e:
            # 步骤 5: 错误处理
            error_payload = {
                "message": "An unexpected error occurred", 
                "details": str(e)
            }
            yield json.dumps(Error(code="INTERNAL_SERVER_ERROR", **error_payload).model_dump())
            yield json.dumps(State(status="error").model_dump())
    
    async def _simple_llm_stream(self, task: Task) -> AsyncGenerator[str, None]:
        """
        简单的 LLM 流式响应（当没有 langgraph 时的后备方案）
        """
        # 这里需要访问 LLM 客户端，实际实现中需要通过依赖注入
        yield json.dumps(Text(content="正在处理您的请求...").model_dump())
        await asyncio.sleep(0.1)  # 模拟处理时间
        yield json.dumps(Text(content="处理完成")).model_dump())
    
    def create_fastapi_endpoint(self):
        """
        创建 FastAPI 端点的工厂方法
        返回一个可以直接用于 FastAPI 路由的函数
        """
        async def chat_stream_endpoint(task: Task):
            """
            FastAPI 端点函数
            接收 AG-UI Task，返回标准的 SSE 流
            """
            try:
                from sse_starlette.sse import EventSourceResponse
            except ImportError:
                raise ImportError("需要安装 sse-starlette: pip install sse-starlette")
            
            return EventSourceResponse(
                self.event_stream_adapter(task),
                ping=15,  # 每 15 秒发送一次心跳
                media_type="text/event-stream"
            )
        
        return chat_stream_endpoint


class LanggraphAgentMock:
    """
    模拟的 langgraph Agent，用于测试和开发
    """
    
    async def astream_events(self, input_data: Dict[str, Any], version: str = "v1"):
        """模拟 langgraph 的 astream_events 方法"""
        # 模拟开始事件
        yield {
            "event": "on_chain_start",
            "data": {"input": input_data}
        }
        
        # 模拟 LLM 流式响应
        response_parts = ["这是", "一个", "模拟的", "响应"]
        for part in response_parts:
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": type('obj', (object,), {'content': part})()}
            }
            await asyncio.sleep(0.1)  # 模拟延迟
        
        # 模拟结束事件
        yield {
            "event": "on_chain_end",
            "data": {"output": "响应完成"}
        }