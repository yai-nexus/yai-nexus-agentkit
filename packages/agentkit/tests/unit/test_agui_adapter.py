# -*- coding: utf-8 -*-
"""
AGUIAdapter单元测试
测试事件翻译逻辑的正确性
"""

import pytest
import json
from unittest.mock import Mock
from yai_nexus_agentkit.adapter.sse_advanced import AGUIAdapter, ToolCallTracker, Task
from ag_ui.core.events import (
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ThinkingStartEvent,
    ThinkingEndEvent,
    TextMessageChunkEvent,
    CustomEvent,
)


class TestToolCallTracker:
    """工具调用跟踪器测试"""

    def test_start_call(self):
        tracker = ToolCallTracker()
        call_id = tracker.start_call("test_tool")

        assert call_id is not None
        assert len(call_id) == 32  # UUID hex length
        assert tracker.get_call_id("test_tool") == call_id

    def test_end_call(self):
        tracker = ToolCallTracker()
        call_id = tracker.start_call("test_tool")

        ended_call_id = tracker.end_call("test_tool")
        assert ended_call_id == call_id
        assert tracker.get_call_id("test_tool") is None

    def test_multiple_tools(self):
        tracker = ToolCallTracker()

        call_id1 = tracker.start_call("tool1")
        call_id2 = tracker.start_call("tool2")

        assert call_id1 != call_id2
        assert tracker.get_call_id("tool1") == call_id1
        assert tracker.get_call_id("tool2") == call_id2


class TestAGUIAdapterEventTranslation:
    """AGUIAdapter事件翻译测试"""

    @pytest.fixture
    def adapter(self):
        mock_agent = Mock()
        return AGUIAdapter(mock_agent)

    @pytest.fixture
    def tool_tracker(self):
        return ToolCallTracker()

    @pytest.mark.asyncio
    async def test_tool_start_event_translation(self, adapter, tool_tracker):
        """测试工具开始事件翻译"""
        # 构造mock的langgraph事件（与真实LangGraph事件结构一致）
        mock_event = {
            "event": "on_tool_start",
            "name": "search_tool",  # 工具名称在顶层
            "data": {
                "input": {"query": "test query", "max_results": 5},
            },
        }

        # 翻译事件
        events = []
        async for event in adapter._translate_event(mock_event, tool_tracker):
            events.append(event)

        # 验证生成了两个事件：ToolCallStart和ToolCallArgs
        assert len(events) == 2

        # 验证ToolCallStartEvent
        start_event = events[0]
        assert isinstance(start_event, ToolCallStartEvent)
        assert start_event.tool_call_name == "search_tool"
        assert start_event.tool_call_id is not None

        # 验证ToolCallArgsEvent
        args_event = events[1]
        assert isinstance(args_event, ToolCallArgsEvent)
        assert args_event.tool_call_id == start_event.tool_call_id
        expected_args = json.dumps(
            {"query": "test query", "max_results": 5}, ensure_ascii=False
        )
        assert args_event.delta == expected_args

    @pytest.mark.asyncio
    async def test_tool_end_event_translation(self, adapter, tool_tracker):
        """测试工具结束事件翻译"""
        # 先开始一个工具调用
        tool_tracker.start_call("search_tool")

        # 构造mock的langgraph事件（与真实LangGraph事件结构一致）
        mock_event = {
            "event": "on_tool_end",
            "name": "search_tool",  # 工具名称在顶层
            "data": {
                "output": {"results": ["result1", "result2"], "count": 2},
            },
        }

        # 翻译事件
        events = []
        async for event in adapter._translate_event(mock_event, tool_tracker):
            events.append(event)

        # 验证生成了两个事件：ToolCallEnd和ToolCallResult
        assert len(events) == 2

        # 验证ToolCallEndEvent
        end_event = events[0]
        assert isinstance(end_event, ToolCallEndEvent)
        assert end_event.tool_call_id is not None

        # 验证ToolCallResultEvent
        result_event = events[1]
        assert isinstance(result_event, ToolCallResultEvent)
        assert result_event.tool_call_id == end_event.tool_call_id
        expected_result = json.dumps(
            {"results": ["result1", "result2"], "count": 2}, ensure_ascii=False
        )
        assert result_event.content == expected_result

    @pytest.mark.asyncio
    async def test_chat_model_stream_translation(self, adapter, tool_tracker):
        """测试聊天模型流式事件翻译"""
        # 构造mock的chunk对象
        mock_chunk = Mock()
        mock_chunk.content = "Hello, world!"

        mock_event = {"event": "on_chat_model_stream", "data": {"chunk": mock_chunk}}

        # 翻译事件
        events = []
        async for event in adapter._translate_event(mock_event, tool_tracker):
            events.append(event)

        # 验证生成了一个TextMessageChunkEvent
        assert len(events) == 1

        chunk_event = events[0]
        assert isinstance(chunk_event, TextMessageChunkEvent)
        assert chunk_event.delta == "Hello, world!"

    @pytest.mark.asyncio
    async def test_thinking_events_translation(self, adapter, tool_tracker):
        """测试思考事件翻译"""
        # 测试思考开始事件（与真实LangGraph事件结构一致）
        start_event = {"event": "on_chain_start", "name": "reasoning_chain", "data": {}}

        events = []
        async for event in adapter._translate_event(start_event, tool_tracker):
            events.append(event)

        assert len(events) == 1
        thinking_start = events[0]
        assert isinstance(thinking_start, ThinkingStartEvent)
        assert thinking_start.title == "reasoning_chain"

        # 测试思考结束事件（与真实LangGraph事件结构一致）
        end_event = {"event": "on_chain_end", "name": "reasoning_chain", "data": {}}

        events = []
        async for event in adapter._translate_event(end_event, tool_tracker):
            events.append(event)

        assert len(events) == 1
        thinking_end = events[0]
        assert isinstance(thinking_end, ThinkingEndEvent)

    @pytest.mark.asyncio
    async def test_unknown_event_handling(self, adapter, tool_tracker):
        """测试未知事件类型的处理"""
        mock_event = {"event": "unknown_event_type", "data": {"some": "data"}}

        # 翻译事件
        events = []
        async for event in adapter._translate_event(mock_event, tool_tracker):
            events.append(event)

        # 未知事件应该被忽略，不产生任何AG-UI事件
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_custom_event_translation(self, adapter, tool_tracker):
        """测试自定义事件翻译"""
        from yai_nexus_agentkit.core.events import _INTERNAL_EVENT_MARKER

        mock_event = {
            "event": "on_custom_event",
            "name": _INTERNAL_EVENT_MARKER,
            "data": {
                "name": "chart_generated",
                "payload": {"type": "line", "data": [1, 2, 3]},
            },
        }

        # 翻译事件
        events = []
        async for event in adapter._translate_event(mock_event, tool_tracker):
            events.append(event)

        # 验证生成了一个CustomEvent
        assert len(events) == 1

        custom_event = events[0]
        assert isinstance(custom_event, CustomEvent)
        assert custom_event.name == "chart_generated"
        assert custom_event.value == {"type": "line", "data": [1, 2, 3]}


class TestAGUIAdapterIntegration:
    """AGUIAdapter集成测试"""

    @pytest.mark.asyncio
    async def test_event_stream_adapter_basic_flow(self):
        """测试基本的事件流适配器流程"""
        # 创建mock的CompiledStateGraph
        from langgraph.graph.state import CompiledStateGraph

        mock_agent = Mock(spec=CompiledStateGraph)

        # 模拟astream_events返回的事件流（与真实LangGraph事件结构一致）
        mock_events = [
            {"event": "on_chat_model_stream", "data": {"chunk": Mock(content="Hello")}},
            {
                "event": "on_tool_start",
                "name": "test_tool",  # 工具名称在顶层
                "data": {"input": {"param": "value"}},
            },
            {
                "event": "on_tool_end",
                "name": "test_tool",  # 工具名称在顶层
                "data": {"output": {"result": "success"}},
            },
        ]

        async def mock_astream_events(*args, **kwargs):
            for event in mock_events:
                yield event

        mock_agent.astream_events = mock_astream_events

        # 创建适配器和任务
        adapter = AGUIAdapter(mock_agent)
        task = Task(id="test_task", query="test query")

        # 收集所有产生的事件
        events = []
        async for event_json in adapter.event_stream_adapter(task):
            event_data = json.loads(event_json)
            events.append(event_data)

        # 验证事件序列
        # 应该包含: RunStarted, TextChunk, ToolCallStart, ToolCallArgs, ToolCallEnd, ToolCallResult, RunFinished
        assert len(events) >= 3  # 至少包含开始、一些业务事件、结束

        # 验证第一个事件是RunStarted
        assert events[0]["type"] == "RUN_STARTED"
        assert events[0]["run_id"] == "test_task"

        # 验证最后一个事件是RunFinished
        assert events[-1]["type"] == "RUN_FINISHED"
        assert events[-1]["run_id"] == "test_task"
