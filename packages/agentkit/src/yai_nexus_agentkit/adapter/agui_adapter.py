# -*- coding: utf-8 -*-
"""
AG-UI 协议适配器
将任何 LangChain Runnable 的事件流转换为 AG-UI 标准事件流
"""

import json
import logging
from typing import AsyncGenerator

# 核心依赖 - 直接导入
from ag_ui.core.events import (
    BaseEvent,
    EventType,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
)
from ag_ui.encoder import EventEncoder
from langchain_core.runnables import Runnable

from .errors import EventTranslationError
from .event_translator import EventTranslator
from .models import Task

# 设置日志
logger = logging.getLogger(__name__)

# 配置常量
SSE_PING_INTERVAL = 15  # SSE心跳间隔（秒）


class AGUIAdapter:
    """
    AG-UI 协议适配器
    将任何 LangChain Runnable 的事件流转换为 AG-UI 标准事件流

    支持的 Runnable 类型:
    - LangGraph CompiledStateGraph (复杂的多步骤 Agent)
    - BaseLanguageModel (简单的 LLM 客户端)
    - 任何其他 LangChain Runnable

    统一使用 astream_events 接口，自动适配不同的输入格式。
    """

    def __init__(self, agent: Runnable):
        self.agent = agent

    async def stream_events(self, task: Task) -> AsyncGenerator[BaseEvent, None]:
        """
        核心事件流适配器
        将 langgraph Agent 事件流转换为 AG-UI 事件对象

        Args:
            task: AG-UI 任务对象

        Yields:
            AG-UI 事件 Pydantic 对象
        """
        # 初始化事件翻译器（带独立状态）
        event_translator = EventTranslator()

        try:
            # 步骤 1: 正确处理thread_id和run_id的关系
            # 如果客户端提供了thread_id，使用它；否则创建新的对话线程
            effective_thread_id = task.thread_id if task.thread_id else task.id

            logger.info(
                "Starting event stream for task",
                task_id=task.id,
                query=task.query,
                thread_id=task.thread_id,
                effective_thread_id=effective_thread_id,
                agent_type=type(self.agent).__name__,
            )

            # 步骤 2: 产生 AG-UI 的 "开始" 事件
            run_started = RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=effective_thread_id,  # 正确的对话线程ID
                run_id=task.id,  # 每次运行的唯一标识
            )
            logger.info(
                "Sending event",
                event_type=run_started.type,
                event_data=run_started.model_dump(),
            )
            yield run_started

            # 统一使用 astream_events，直接传字符串即可
            logger.info("Using unified astream_events interface")

            async for event in self.agent.astream_events(task.query, version="v2"):
                try:
                    async for ag_ui_event in event_translator.translate_event(event):
                        logger.info(
                            "Sending event",
                            event_type=ag_ui_event.type,
                            event_data=ag_ui_event.model_dump(),
                        )
                        yield ag_ui_event
                except EventTranslationError as e:
                    logger.warning(f"Failed to translate event: {e}")
                    continue
                except Exception as e:
                    logger.exception(
                        "Unexpected error translating event",
                        error_type=type(e).__name__,
                        error_message=str(e),
                    )
                    continue

            # 步骤 4: 产生 AG-UI 的 "完成" 事件
            run_finished = RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=effective_thread_id,  # 使用相同的线程ID
                run_id=task.id,  # 使用正确的运行ID
            )
            logger.info(
                "Sending event",
                event_type=run_finished.type,
                event_data=run_finished.model_dump(),
            )
            yield run_finished

            logger.info(
                "AG-UI streaming completed successfully",
                task_id=task.id,
                thread_id=effective_thread_id,
            )

        except Exception as e:
            logger.exception(
                "AGUIAdapter error",
                task_id=task.id,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            # 步骤 5: 错误处理
            run_error = RunErrorEvent(type=EventType.RUN_ERROR, message=str(e))
            logger.info(
                "Sending event",
                event_type=run_error.type,
                event_data=run_error.model_dump(),
            )
            yield run_error

    async def create_official_stream(self, task: Task, accept_header: str = None):
        """
        创建官方 AG-UI 格式的事件流
        内部处理 EventEncoder，返回编码后的 SSE 数据

        Args:
            task: AG-UI 任务对象
            accept_header: HTTP Accept 头，用于 EventEncoder

        Yields:
            编码后的 SSE 事件数据
        """
        # 创建 AG-UI 官方的事件编码器
        encoder = EventEncoder(accept=accept_header)

        logger.info(
            "Creating official AG-UI stream",
            task_id=task.id,
            thread_id=task.thread_id,
            accept_header=accept_header,
        )

        try:
            # 使用核心的 stream_events 方法获取事件对象
            async for event_obj in self.stream_events(task):
                # 使用官方编码器编码事件，自动处理格式兼容性
                yield encoder.encode(event_obj)

        except Exception as e:
            logger.exception(
                "Error in official stream creation",
                task_id=task.id,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            # 发送错误事件，使用官方编码器
            error_event = RunErrorEvent(type="RUN_ERROR", message=str(e))
            yield encoder.encode(error_event)

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

            async def json_stream():
                async for event_obj in self.stream_events(task):
                    yield json.dumps(event_obj.model_dump())

            return EventSourceResponse(
                json_stream(),
                ping=SSE_PING_INTERVAL,  # 心跳间隔
                media_type="text/event-stream",
            )

        return chat_stream_endpoint
