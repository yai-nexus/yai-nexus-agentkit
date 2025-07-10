# -*- coding: utf-8 -*-
"""
高级模式：完整三层架构（langgraph + AG-UI + sse-starlette）
按照设计文档实现标准的 AG-UI 协议适配器
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import AsyncGenerator, Union, Dict, Optional

from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables import Runnable
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

# 核心依赖 - 直接导入
from ag_ui.core.events import (
    TextMessageChunkEvent,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ThinkingStartEvent,
    ThinkingEndEvent,
    CustomEvent,
    StepStartedEvent,
    StepFinishedEvent,
)

# 导入新的强类型事件枚举和异常
from .langgraph_events import LangGraphEventType
from .errors import EventTranslationError
from ..core.events import _INTERNAL_EVENT_MARKER

# 设置日志
logger = logging.getLogger(__name__)


@dataclass
class ToolCallTracker:
    """
    工具调用状态跟踪器
    管理当前活跃的工具调用ID，用于在start、args、end、result事件之间建立关联
    """

    active_calls: Dict[str, str] = field(default_factory=dict)  # tool_name -> call_id

    def start_call(self, tool_name: str) -> str:
        """开始一次工具调用，返回生成的call_id"""
        call_id = uuid.uuid4().hex
        self.active_calls[tool_name] = call_id
        return call_id

    def end_call(self, tool_name: str) -> Optional[str]:
        """结束一次工具调用，返回并清理call_id"""
        return self.active_calls.pop(tool_name, None)

    def get_call_id(self, tool_name: str) -> Optional[str]:
        """获取当前工具的call_id"""
        return self.active_calls.get(tool_name)


class Task(BaseModel):
    """任务模型，用于定义Agent任务"""

    id: str
    query: str


class AGUIAdapter:
    """
    高级 AG-UI 协议适配器
    将 langgraph 事件流转换为 AG-UI 标准事件流
    """

    def __init__(self, agent: Union[CompiledStateGraph, BaseLanguageModel, Runnable]):
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
        # 初始化工具调用跟踪器
        tool_tracker = ToolCallTracker()

        try:
            # 步骤 1: 产生 AG-UI 的 "开始" 事件
            run_started = RunStartedEvent(run_id=task.id)
            yield json.dumps(run_started.model_dump())

            # 通过 isinstance 判断 agent 是否为 langgraph agent
            if isinstance(self.agent, CompiledStateGraph):
                # 步骤 2: 调用 langgraph Agent 的流式事件接口
                async for event in self.agent.astream_events(
                    {"messages": [("user", task.query)]}, version="v1"
                ):
                    # 使用强类型枚举处理事件
                    try:
                        async for ag_ui_event in self._translate_event(
                            event, tool_tracker
                        ):
                            yield json.dumps(ag_ui_event.model_dump())
                    except EventTranslationError as e:
                        logger.warning(f"Failed to translate event: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error translating event: {e}")
                        continue
            else:
                # 如果没有 astream_events，则作为普通 LLM 客户端处理
                async for event in self._simple_llm_stream(task):
                    yield event

            # 步骤 4: 产生 AG-UI 的 "完成" 事件
            run_finished = RunFinishedEvent(run_id=task.id)
            yield json.dumps(run_finished.model_dump())

        except Exception as e:
            logger.error(f"AGUIAdapter error: {e}")
            # 步骤 5: 错误处理
            run_error = RunErrorEvent(run_id=task.id, error=str(e))
            yield json.dumps(run_error.model_dump())

    async def _translate_event(
        self, event: dict, tool_tracker: ToolCallTracker
    ) -> AsyncGenerator[object, None]:
        """
        将单个langgraph事件翻译为AG-UI事件

        Args:
            event: langgraph事件字典
            tool_tracker: 工具调用跟踪器

        Yields:
            AG-UI事件对象
        """
        kind_str = event["event"]

        # 使用强类型枚举转换
        try:
            kind = LangGraphEventType(kind_str)
        except ValueError:
            # 宽容处理未知事件类型
            logger.warning(
                f"Unknown event type: {kind_str}, data: {event.get('data', {})[:100]}..."
            )
            return

        event_data = event.get("data", {})

        # 工具调用开始事件
        if kind is LangGraphEventType.ON_TOOL_START:
            tool_name = event_data.get("name", "unknown")
            tool_input = event_data.get("input", {})

            # 生成并保存call_id
            call_id = tool_tracker.start_call(tool_name)

            # 发送ToolCallStartEvent
            yield ToolCallStartEvent(tool_call_id=call_id, tool_call_name=tool_name)

            # 发送ToolCallArgsEvent
            yield ToolCallArgsEvent(
                tool_call_id=call_id, delta=json.dumps(tool_input, ensure_ascii=False)
            )

        # 工具调用结束事件
        elif kind is LangGraphEventType.ON_TOOL_END:
            tool_name = event_data.get("name", "unknown")
            tool_output = event_data.get("output")

            # 获取并清理call_id
            call_id = tool_tracker.end_call(tool_name)
            if not call_id:
                logger.warning(f"No active call found for tool: {tool_name}")
                return

            # 发送ToolCallEndEvent
            yield ToolCallEndEvent(tool_call_id=call_id)

            # 发送ToolCallResultEvent
            result_content = (
                json.dumps(tool_output, ensure_ascii=False)
                if tool_output is not None
                else ""
            )
            yield ToolCallResultEvent(tool_call_id=call_id, content=result_content)

        # LLM流式输出事件
        elif kind is LangGraphEventType.ON_CHAT_MODEL_STREAM:
            chunk = event_data.get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield TextMessageChunkEvent(
                    delta=chunk.content,
                    snapshot=chunk.content,  # 注意: 这里应该是累积的快照，但需要状态管理
                )

        # 思考开始事件
        elif kind is LangGraphEventType.ON_CHAIN_START:
            chain_name = event_data.get("name", "Unknown")
            yield ThinkingStartEvent(title=chain_name)

        # 思考结束事件
        elif kind is LangGraphEventType.ON_CHAIN_END:
            yield ThinkingEndEvent()

        # 步骤开始事件
        elif kind is LangGraphEventType.ON_NODE_START:
            node_name = event_data.get("name", "Unknown")
            yield StepStartedEvent(name=node_name)

        # 步骤结束事件
        elif kind is LangGraphEventType.ON_NODE_END:
            node_name = event_data.get("name", "Unknown")
            yield StepFinishedEvent(name=node_name)

        # 自定义事件处理
        elif kind is LangGraphEventType.ON_CUSTOM_EVENT:
            # 只处理我们约定的、由EventEmitter发出的内部标记事件
            if event.get("name") == _INTERNAL_EVENT_MARKER:
                custom_event_data = event_data
                ui_event_name = custom_event_data.get("name")
                ui_event_payload = custom_event_data.get("payload")

                # 翻译成AG-UI的CustomEvent
                yield CustomEvent(name=ui_event_name, value=ui_event_payload)

    async def _simple_llm_stream(self, task: Task) -> AsyncGenerator[str, None]:
        """
        简单的 LLM 流式响应（当没有 langgraph 时的后备方案）
        使用 LLM 客户端进行流式响应
        """
        try:
            # 使用 LLM 客户端的流式响应
            accumulated_response = ""
            async for chunk in self.agent.astream(task.query):
                if hasattr(chunk, "content") and chunk.content:
                    accumulated_response += chunk.content
                    text_chunk = TextMessageChunkEvent(
                        delta=chunk.content, snapshot=accumulated_response
                    )
                    yield json.dumps(text_chunk.model_dump())

        except Exception:
            # 如果流式响应失败，尝试异步调用
            try:
                response = await self.agent.ainvoke(task.query)
                content = (
                    response.content if hasattr(response, "content") else str(response)
                )

                text_chunk = TextMessageChunkEvent(delta=content, snapshot=content)
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
                media_type="text/event-stream",
            )

        return chat_stream_endpoint
