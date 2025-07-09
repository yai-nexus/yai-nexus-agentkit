# -*- coding: utf-8 -*-
"""
中级模式：基础 SSE 支持
提供简单的 Server-Sent Events 流式响应，不依赖复杂的协议
"""

import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from pydantic import BaseModel


class SSEEvent(BaseModel):
    """基础 SSE 事件模型"""
    event: str
    data: Dict[str, Any]
    id: Optional[str] = None


class BasicSSEAdapter:
    """
    基础 SSE 适配器
    将 LLM 流式响应转换为简单的 SSE 事件流
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def stream_response(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        将 LLM 响应转换为基础 SSE 事件流
        
        Args:
            message: 用户消息
            **kwargs: 其他参数
        
        Yields:
            SSE 格式的字符串事件
        """
        try:
            # 发送开始事件
            start_event = SSEEvent(
                event="start",
                data={"status": "processing", "message": "正在处理..."}
            )
            yield f"event: {start_event.event}\ndata: {start_event.model_dump_json()}\n\n"
            
            # 处理 LLM 流式响应
            full_response = ""
            async for chunk in self.llm_client.astream(message):
                if chunk.content:
                    full_response += chunk.content
                    
                    # 发送内容事件
                    content_event = SSEEvent(
                        event="content",
                        data={"content": chunk.content, "delta": True}
                    )
                    yield f"event: {content_event.event}\ndata: {content_event.model_dump_json()}\n\n"
            
            # 发送完成事件
            complete_event = SSEEvent(
                event="complete",
                data={"status": "done", "full_response": full_response}
            )
            yield f"event: {complete_event.event}\ndata: {complete_event.model_dump_json()}\n\n"
            
        except Exception as e:
            # 发送错误事件
            error_event = SSEEvent(
                event="error",
                data={"error": str(e), "type": "processing_error"}
            )
            yield f"event: {error_event.event}\ndata: {error_event.model_dump_json()}\n\n"
    
    async def stream_with_heartbeat(self, message: str, heartbeat_interval: int = 30) -> AsyncGenerator[str, None]:
        """
        带心跳的流式响应
        
        Args:
            message: 用户消息
            heartbeat_interval: 心跳间隔（秒）
        """
        heartbeat_task = None
        
        try:
            # 启动心跳任务
            heartbeat_task = asyncio.create_task(self._heartbeat_loop(heartbeat_interval))
            
            # 创建响应流和心跳流的组合
            response_stream = self.stream_response(message)
            
            async for event in response_stream:
                yield event
                
        finally:
            # 清理心跳任务
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
    
    async def _heartbeat_loop(self, interval: int):
        """心跳循环"""
        while True:
            await asyncio.sleep(interval)
            heartbeat_event = SSEEvent(
                event="heartbeat",
                data={"timestamp": asyncio.get_event_loop().time()}
            )
            # 注意：这里需要与主流同步，实际实现中需要更复杂的协调机制