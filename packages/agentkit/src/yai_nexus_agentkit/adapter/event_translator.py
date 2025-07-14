# -*- coding: utf-8 -*-
"""
事件翻译器
将 LangChain/LangGraph 事件转换为 AG-UI 标准事件
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any

from ag_ui.core.events import (
    BaseEvent,
    CustomEvent,
    EventType,
    StepFinishedEvent,
    StepStartedEvent,
    TextMessageChunkEvent,
    ThinkingTextMessageEndEvent,
    ThinkingTextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)

from ..core.events import _INTERNAL_EVENT_MARKER
from .errors import EventTranslationError
from .langgraph_events import LangGraphEventType
from .tool_call_tracker import ToolCallTracker

logger = logging.getLogger(__name__)


class EventTranslator:
    """
    事件翻译器
    将 LangChain/LangGraph 事件转换为 AG-UI 标准事件
    """

    def __init__(self):
        self.tool_tracker = ToolCallTracker()

    async def translate_event(self, event: Dict[str, Any]) -> AsyncGenerator[BaseEvent, None]:
        """
        翻译单个事件

        Args:
            event: LangChain/LangGraph 事件字典

        Yields:
            AG-UI 事件对象
        """
        kind_str = event["event"]

        # 使用强类型枚举转换
        try:
            kind = LangGraphEventType(kind_str)
        except ValueError:
            # 宽容处理未知事件类型
            event_data_str = str(event.get("data", {}))
            truncated_data = (
                event_data_str[:100] + "..."
                if len(event_data_str) > 100
                else event_data_str
            )
            logger.warning(f"Unknown event type: {kind_str}, data: {truncated_data}")
            return

        event_data = event.get("data", {})

        # 工具调用开始事件
        if kind is LangGraphEventType.ON_TOOL_START:
            async for ag_event in self._handle_tool_start(event, event_data):
                yield ag_event

        # 工具调用结束事件
        elif kind is LangGraphEventType.ON_TOOL_END:
            async for ag_event in self._handle_tool_end(event, event_data):
                yield ag_event

        # LLM流式输出事件
        elif kind is LangGraphEventType.ON_CHAT_MODEL_STREAM:
            async for ag_event in self._handle_chat_model_stream(event_data):
                yield ag_event

        # 思考开始事件
        elif kind is LangGraphEventType.ON_CHAIN_START:
            yield ThinkingTextMessageStartEvent(
                type=EventType.THINKING_TEXT_MESSAGE_START
            )

        # 思考结束事件
        elif kind is LangGraphEventType.ON_CHAIN_END:
            yield ThinkingTextMessageEndEvent(type=EventType.THINKING_TEXT_MESSAGE_END)

        # 步骤开始事件
        elif kind is LangGraphEventType.ON_NODE_START:
            node_name = event.get("name", "Unknown")
            yield StepStartedEvent(type=EventType.STEP_STARTED, name=node_name)

        # 步骤结束事件
        elif kind is LangGraphEventType.ON_NODE_END:
            node_name = event.get("name", "Unknown")
            yield StepFinishedEvent(type=EventType.STEP_FINISHED, name=node_name)

        # 自定义事件处理
        elif kind is LangGraphEventType.ON_CUSTOM_EVENT:
            async for ag_event in self._handle_custom_event(event, event_data):
                yield ag_event

    async def _handle_tool_start(
        self, event: Dict[str, Any], event_data: Dict[str, Any]
    ) -> AsyncGenerator[BaseEvent, None]:
        """处理工具调用开始事件"""
        # 工具名称在事件的顶层name字段中，不在data中
        tool_name = event.get("name", "unknown")
        tool_input = event_data.get("input", {})

        # 生成并保存call_id
        call_id = self.tool_tracker.start_call(tool_name)

        # 发送ToolCallStartEvent
        yield ToolCallStartEvent(
            type=EventType.TOOL_CALL_START,
            tool_call_id=call_id,
            tool_call_name=tool_name,
        )

        # 发送ToolCallArgsEvent
        yield ToolCallArgsEvent(
            type=EventType.TOOL_CALL_ARGS,
            tool_call_id=call_id,
            delta=json.dumps(tool_input, ensure_ascii=False),
        )

    async def _handle_tool_end(
        self, event: Dict[str, Any], event_data: Dict[str, Any]
    ) -> AsyncGenerator[BaseEvent, None]:
        """处理工具调用结束事件"""
        # 工具名称在事件的顶层name字段中，不在data中
        tool_name = event.get("name", "unknown")
        tool_output = event_data.get("output")

        # 获取并清理call_id
        call_id = self.tool_tracker.end_call(tool_name)
        if not call_id:
            logger.warning(f"No active call found for tool: {tool_name}")
            return

        # 发送ToolCallEndEvent
        yield ToolCallEndEvent(type=EventType.TOOL_CALL_END, tool_call_id=call_id)

        # 发送ToolCallResultEvent
        result_content = (
            json.dumps(tool_output, ensure_ascii=False)
            if tool_output is not None
            else ""
        )
        yield ToolCallResultEvent(
            type=EventType.TOOL_CALL_RESULT,
            message_id=call_id,  # 使用call_id作为message_id
            tool_call_id=call_id,
            content=result_content,
        )

    async def _handle_chat_model_stream(
        self, event_data: Dict[str, Any]
    ) -> AsyncGenerator[BaseEvent, None]:
        """处理聊天模型流式事件"""
        chunk = event_data.get("chunk")
        if chunk and hasattr(chunk, "content") and chunk.content:
            yield TextMessageChunkEvent(
                type=EventType.TEXT_MESSAGE_CHUNK,
                delta=chunk.content,
            )

    async def _handle_custom_event(
        self, event: Dict[str, Any], event_data: Dict[str, Any]
    ) -> AsyncGenerator[BaseEvent, None]:
        """处理自定义事件"""
        # 只处理我们约定的、由EventEmitter发出的内部标记事件
        if event.get("name") == _INTERNAL_EVENT_MARKER:
            custom_event_data = event_data
            ui_event_name = custom_event_data.get("name")
            ui_event_payload = custom_event_data.get("payload")

            # 翻译成AG-UI的CustomEvent
            yield CustomEvent(
                type=EventType.CUSTOM, name=ui_event_name, value=ui_event_payload
            )


# 默认翻译器实例（保持向后兼容）
default_translator = EventTranslator()