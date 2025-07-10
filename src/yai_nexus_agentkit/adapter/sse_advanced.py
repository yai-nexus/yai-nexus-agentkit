# -*- coding: utf-8 -*-
"""
高级模式：完整三层架构（langgraph + AG-UI + sse-starlette）
按照设计文档实现标准的 AG-UI 协议适配器
"""

import json
from typing import AsyncGenerator, Union

from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables import Runnable
from langgraph.graph.state import CompiledGraph
from pydantic import BaseModel

# 核心依赖 - 直接导入
from ag_ui.core.events import (
    TextMessageChunkEvent,
    StateDeltaEvent,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent
)


class Task(BaseModel):
    """任务模型，用于定义Agent任务"""
    id: str
    query: str


class AGUIAdapter:
    """
    高级 AG-UI 协议适配器
    将 langgraph 事件流转换为 AG-UI 标准事件流
    """
    
    def __init__(self, agent: Union[CompiledGraph, BaseLanguageModel, Runnable]):
        self.agent = agent
    
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
            run_started = RunStartedEvent(run_id=task.id)
            yield json.dumps(run_started.model_dump())
            
            # 通过 isinstance 判断 agent 是否为 langgraph agent
            if isinstance(self.agent, CompiledGraph):
                # 步骤 2: 调用 langgraph Agent 的流式事件接口
                async for event in self.agent.astream_events(
                    {"messages": [("user", task.query)]},
                    version="v1"
                ):
                    kind = event["event"]
                    
                    # 步骤 3: 将 langgraph 事件翻译为 AG-UI 事件
                    if kind == "on_chat_model_stream":
                        # LLM 的流式输出
                        content = event["data"]["chunk"].content
                        if content:
                            text_chunk = TextMessageChunkEvent(
                                delta=content,
                                snapshot=content
                            )
                            yield json.dumps(text_chunk.model_dump())
                    
                    elif kind == "on_tool_start":
                        # 工具开始调用
                        tool_name = event["data"].get("input", {}).get("tool", "unknown")
                        state_delta = StateDeltaEvent(
                            key="tool_status",
                            value=f"calling_{tool_name}"
                        )
                        yield json.dumps(state_delta.model_dump())
                    
                    elif kind == "on_tool_end":
                        # 工具调用完成
                        state_delta = StateDeltaEvent(
                            key="tool_status",
                            value="completed"
                        )
                        yield json.dumps(state_delta.model_dump())
            else:
                # 如果没有 astream_events，则作为普通 LLM 客户端处理
                async for event in self._simple_llm_stream(task):
                    yield event
            
            # 步骤 4: 产生 AG-UI 的 "完成" 事件
            run_finished = RunFinishedEvent(run_id=task.id)
            yield json.dumps(run_finished.model_dump())
            
        except Exception as e:
            # 步骤 5: 错误处理
            run_error = RunErrorEvent(
                run_id=task.id,
                error=str(e)
            )
            yield json.dumps(run_error.model_dump())
    
    async def _simple_llm_stream(self, task: Task) -> AsyncGenerator[str, None]:
        """
        简单的 LLM 流式响应（当没有 langgraph 时的后备方案）
        使用 LLM 客户端进行流式响应
        """
        try:
            # 使用 LLM 客户端的流式响应
            accumulated_response = ""
            async for chunk in self.agent.astream(task.query):
                if hasattr(chunk, 'content') and chunk.content:
                    accumulated_response += chunk.content
                    text_chunk = TextMessageChunkEvent(
                        delta=chunk.content,
                        snapshot=accumulated_response
                    )
                    yield json.dumps(text_chunk.model_dump())
                    
        except Exception:
            # 如果流式响应失败，尝试异步调用
            try:
                response = await self.agent.ainvoke(task.query)
                content = response.content if hasattr(response, 'content') else str(response)
                
                text_chunk = TextMessageChunkEvent(
                    delta=content,
                    snapshot=content
                )
                yield json.dumps(text_chunk.model_dump())
                
            except Exception as fallback_e:
                # 如果异步调用也失败，则向上抛出异常
                # 让主流程统一处理错误，生成 RunErrorEvent
                raise fallback_e
    
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
            from sse_starlette.sse import EventSourceResponse
            
            return EventSourceResponse(
                self.event_stream_adapter(task),
                ping=15,  # 每 15 秒发送一次心跳
                media_type="text/event-stream"
            )
        
        return chat_stream_endpoint


