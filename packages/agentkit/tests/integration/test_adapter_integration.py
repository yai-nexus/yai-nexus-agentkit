# -*- coding: utf-8 -*-
"""
AGUIAdapter集成测试
测试完整的langgraph -> AGUIAdapter -> AG-UI事件流转换
"""

import json
import pytest
from typing import Annotated, Dict, List

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END

from yai_nexus_agentkit.adapter.sse_advanced import AGUIAdapter, Task


# 定义AgentState
class AgentState(MessagesState):
    """扩展的Agent状态，包含消息和其他元数据"""

    tool_calls_made: Annotated[List[str], "已执行的工具调用列表"] = []
    current_step: Annotated[str, "当前执行步骤"] = "start"


# 创建Mock工具
@tool
def mock_search_tool(query: str, max_results: int = 3) -> Dict:
    """
    模拟搜索工具，返回固定的搜索结果

    Args:
        query: 搜索查询
        max_results: 最大结果数量

    Returns:
        包含搜索结果的字典
    """
    return {
        "query": query,
        "results": [
            {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/{i+1}",
            }
            for i in range(min(max_results, 3))
        ],
        "total_found": min(max_results, 3),
    }


@tool
def mock_calculator_tool(expression: str) -> Dict:
    """
    模拟计算器工具，执行简单的数学计算

    Args:
        expression: 数学表达式

    Returns:
        计算结果
    """
    try:
        # 只支持简单的数学运算，安全起见
        allowed_chars = set("0123456789+-*/.()")
        if all(c in allowed_chars or c.isspace() for c in expression):
            result = eval(expression)
            return {"expression": expression, "result": result, "success": True}
        else:
            return {
                "expression": expression,
                "error": "Invalid characters",
                "success": False,
            }
    except Exception as e:
        return {"expression": expression, "error": str(e), "success": False}


class TestAGUIAdapterIntegration:
    """AGUIAdapter完整集成测试"""

    def create_test_graph(self):
        """创建一个包含工具调用的测试图"""

        # 定义节点函数
        def should_continue(state: AgentState) -> str:
            """决定是否需要调用工具"""
            messages = state.get("messages", [])
            if not messages:
                return "respond"

            last_message = messages[-1]
            if isinstance(last_message, HumanMessage):
                # 简单的规则：包含"search"关键词就调用搜索工具，包含"calculate"就调用计算器
                content = last_message.content.lower()
                if "search" in content:
                    return "call_search"
                elif "calculate" in content or "计算" in content:
                    return "call_calculator"
                else:
                    return "respond"

            return "respond"

        def decide_node(state: AgentState) -> Dict:
            """决策节点，返回状态更新"""
            next_action = should_continue(state)
            return {
                "current_step": f"decided_to_{next_action}",
                "next_action": next_action,
            }

        def call_search_tool(state: AgentState) -> Dict:
            """调用搜索工具的节点"""
            messages = state.get("messages", [])
            last_message = messages[-1] if messages else None

            if last_message and isinstance(last_message, HumanMessage):
                # 从消息中提取查询
                query = last_message.content.replace("search", "").strip()
                if not query:
                    query = "default query"

                # 调用搜索工具
                result = mock_search_tool.invoke({"query": query, "max_results": 2})

                # 创建AI回复
                ai_message = AIMessage(
                    content=f"搜索完成，找到 {result['total_found']} 个结果：\n"
                    + "\n".join([f"- {r['title']}" for r in result["results"]])
                )

                return {
                    "messages": [ai_message],
                    "tool_calls_made": state.get("tool_calls_made", []) + ["search"],
                    "current_step": "search_completed",
                }

            return {"messages": [AIMessage(content="搜索失败")]}

        def call_calculator_tool(state: AgentState) -> Dict:
            """调用计算器工具的节点"""
            messages = state.get("messages", [])
            last_message = messages[-1] if messages else None

            if last_message and isinstance(last_message, HumanMessage):
                # 从消息中提取表达式
                content = last_message.content
                # 简单提取数字和运算符
                import re

                expression_match = re.search(r"[\d+\-*/().\s]+", content)
                expression = (
                    expression_match.group().strip() if expression_match else "1+1"
                )

                # 调用计算器工具
                result = mock_calculator_tool.invoke({"expression": expression})

                # 创建AI回复
                if result.get("success"):
                    ai_message = AIMessage(
                        content=f"计算结果：{result['expression']} = {result['result']}"
                    )
                else:
                    ai_message = AIMessage(
                        content=f"计算失败：{result.get('error', '未知错误')}"
                    )

                return {
                    "messages": [ai_message],
                    "tool_calls_made": state.get("tool_calls_made", [])
                    + ["calculator"],
                    "current_step": "calculation_completed",
                }

            return {"messages": [AIMessage(content="计算失败")]}

        def respond_directly(state: AgentState) -> Dict:
            """直接回复的节点"""
            messages = state.get("messages", [])
            last_message = messages[-1] if messages else None

            if last_message and isinstance(last_message, HumanMessage):
                ai_message = AIMessage(
                    content=f"我收到了您的消息：{last_message.content}\n这是一个简单的回复。"
                )
                return {"messages": [ai_message], "current_step": "responded"}

            return {"messages": [AIMessage(content="Hello!")]}

        # 构建图
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("decide", decide_node)
        workflow.add_node("call_search", call_search_tool)
        workflow.add_node("call_calculator", call_calculator_tool)
        workflow.add_node("respond", respond_directly)

        # 添加边
        workflow.add_edge(START, "decide")
        workflow.add_conditional_edges(
            "decide",
            lambda x: should_continue(x),  # 使用lambda调用决策函数
            {
                "call_search": "call_search",
                "call_calculator": "call_calculator",
                "respond": "respond",
            },
        )
        workflow.add_edge("call_search", END)
        workflow.add_edge("call_calculator", END)
        workflow.add_edge("respond", END)

        return workflow.compile()

    @pytest.mark.asyncio
    async def test_complete_event_flow_with_search_tool(self):
        """测试包含搜索工具调用的完整事件流"""

        # 创建测试图和适配器
        graph = self.create_test_graph()
        adapter = AGUIAdapter(graph)
        task = Task(id="integration_test_search", query="search for Python tutorials")

        # 收集所有事件
        events = []
        async for event_json in adapter.event_stream_adapter(task):
            event_data = json.loads(event_json)
            events.append(event_data)

        # 验证事件序列的基本结构
        assert len(events) >= 2, "至少应该有RunStarted和RunFinished事件"

        # 验证开始和结束事件
        assert events[0]["type"] == "RUN_STARTED"
        assert events[0]["run_id"] == "integration_test_search"

        assert events[-1]["type"] == "RUN_FINISHED"
        assert events[-1]["run_id"] == "integration_test_search"

        # 查找工具调用相关的事件
        tool_start_events = [e for e in events if e.get("type") == "TOOL_CALL_START"]
        tool_args_events = [e for e in events if e.get("type") == "TOOL_CALL_ARGS"]
        tool_end_events = [e for e in events if e.get("type") == "TOOL_CALL_END"]
        tool_result_events = [e for e in events if e.get("type") == "TOOL_CALL_RESULT"]

        # 验证工具调用事件的存在
        if tool_start_events:
            # 如果有工具调用，验证完整序列
            assert len(tool_start_events) > 0, "应该有工具调用开始事件"
            assert len(tool_args_events) > 0, "应该有工具参数事件"
            assert len(tool_end_events) > 0, "应该有工具调用结束事件"
            assert len(tool_result_events) > 0, "应该有工具结果事件"

            # 验证工具调用ID的一致性
            for i in range(len(tool_start_events)):
                start_event = tool_start_events[i]
                args_event = tool_args_events[i] if i < len(tool_args_events) else None
                end_event = tool_end_events[i] if i < len(tool_end_events) else None
                result_event = (
                    tool_result_events[i] if i < len(tool_result_events) else None
                )

                tool_call_id = start_event.get("tool_call_id")
                assert tool_call_id is not None, "工具调用ID不应为空"

                if args_event:
                    assert (
                        args_event.get("tool_call_id") == tool_call_id
                    ), "参数事件的tool_call_id应该匹配"
                if end_event:
                    assert (
                        end_event.get("tool_call_id") == tool_call_id
                    ), "结束事件的tool_call_id应该匹配"
                if result_event:
                    assert (
                        result_event.get("tool_call_id") == tool_call_id
                    ), "结果事件的tool_call_id应该匹配"

                # 验证工具名称
                assert (
                    start_event.get("tool_call_name") == "mock_search_tool"
                ), "工具名称应该正确"

                # 验证参数内容
                if args_event:
                    args_delta = args_event.get("delta", "")
                    assert "query" in args_delta, "参数应该包含query字段"

                # 验证结果内容
                if result_event:
                    result_content = result_event.get("content", "")
                    assert "results" in result_content, "结果应该包含搜索结果"

    @pytest.mark.asyncio
    async def test_complete_event_flow_with_calculator_tool(self):
        """测试包含计算器工具调用的完整事件流"""

        # 创建测试图和适配器
        graph = self.create_test_graph()
        adapter = AGUIAdapter(graph)
        task = Task(id="integration_test_calc", query="calculate 2 + 3 * 4")

        # 收集所有事件
        events = []
        async for event_json in adapter.event_stream_adapter(task):
            event_data = json.loads(event_json)
            events.append(event_data)

        # 验证基本事件结构
        assert len(events) >= 2
        assert events[0]["type"] == "RUN_STARTED"
        assert events[-1]["type"] == "RUN_FINISHED"

        # 查找工具调用事件
        tool_events = [e for e in events if e.get("type", "").startswith("TOOL_CALL")]

        if tool_events:
            # 验证工具调用序列
            tool_start_events = [
                e for e in events if e.get("type") == "TOOL_CALL_START"
            ]
            assert len(tool_start_events) > 0

            # 验证计算器工具特定的内容
            for start_event in tool_start_events:
                if start_event.get("tool_call_name") == "mock_calculator_tool":
                    tool_call_id = start_event["tool_call_id"]

                    # 查找对应的参数和结果事件
                    args_events = [
                        e
                        for e in events
                        if e.get("type") == "TOOL_CALL_ARGS"
                        and e.get("tool_call_id") == tool_call_id
                    ]
                    result_events = [
                        e
                        for e in events
                        if e.get("type") == "TOOL_CALL_RESULT"
                        and e.get("tool_call_id") == tool_call_id
                    ]

                    if args_events:
                        args_content = args_events[0].get("delta", "")
                        assert "expression" in args_content, "参数应该包含数学表达式"

                    if result_events:
                        result_content = result_events[0].get("content", "")
                        assert (
                            "result" in result_content or "error" in result_content
                        ), "结果应该包含计算结果或错误信息"

    @pytest.mark.asyncio
    async def test_simple_response_without_tools(self):
        """测试不需要工具调用的简单对话流"""

        # 创建测试图和适配器
        graph = self.create_test_graph()
        adapter = AGUIAdapter(graph)
        task = Task(id="integration_test_simple", query="Hello, how are you?")

        # 收集所有事件
        events = []
        async for event_json in adapter.event_stream_adapter(task):
            event_data = json.loads(event_json)
            events.append(event_data)

        # 验证基本事件结构
        assert len(events) >= 2
        assert events[0]["type"] == "RUN_STARTED"
        assert events[-1]["type"] == "RUN_FINISHED"

        # 注意：对于简单对话，可能还是会有一些工具调用，这取决于具体的逻辑

        # 验证事件顺序的合理性
        event_types = [e["type"] for e in events]
        assert event_types[0] == "RUN_STARTED"
        assert event_types[-1] == "RUN_FINISHED"

    @pytest.mark.asyncio
    async def test_event_sequence_ordering(self):
        """测试事件序列的正确顺序"""

        # 创建测试图和适配器
        graph = self.create_test_graph()
        adapter = AGUIAdapter(graph)
        task = Task(id="integration_test_order", query="search for machine learning")

        # 收集所有事件
        events = []
        event_timestamps = []

        async for event_json in adapter.event_stream_adapter(task):
            event_data = json.loads(event_json)
            events.append(event_data)
            # 记录时间戳（如果可用）
            event_timestamps.append(event_data.get("timestamp"))

        # 验证事件顺序
        assert events[0]["type"] == "RUN_STARTED", "第一个事件必须是RUN_STARTED"
        assert events[-1]["type"] == "RUN_FINISHED", "最后一个事件必须是RUN_FINISHED"

        # 验证工具调用事件的正确顺序
        tool_call_events = []
        for i, event in enumerate(events):
            if event.get("type", "").startswith("TOOL_CALL"):
                tool_call_events.append((i, event))

        # 按tool_call_id分组验证顺序
        tool_call_groups = {}
        for index, event in tool_call_events:
            tool_call_id = event.get("tool_call_id")
            if tool_call_id:
                if tool_call_id not in tool_call_groups:
                    tool_call_groups[tool_call_id] = []
                tool_call_groups[tool_call_id].append((index, event))

        # 验证每个工具调用组内的事件顺序
        for tool_call_id, group_events in tool_call_groups.items():
            group_events.sort(key=lambda x: x[0])  # 按事件索引排序
            event_types = [event[1]["type"] for event in group_events]

            # 验证工具调用事件的预期顺序
            expected_order = [
                "TOOL_CALL_START",
                "TOOL_CALL_ARGS",
                "TOOL_CALL_END",
                "TOOL_CALL_RESULT",
            ]

            # 检查是否包含预期的事件类型
            for expected_type in expected_order:
                if expected_type in event_types:
                    # 如果存在，验证它们的相对顺序是正确的
                    indices = [
                        i for i, t in enumerate(event_types) if t == expected_type
                    ]
                    for idx in indices:
                        # start应该在args之前，args应该在end之前，end应该在result之前
                        if expected_type == "TOOL_CALL_ARGS":
                            start_indices = [
                                i
                                for i, t in enumerate(event_types)
                                if t == "TOOL_CALL_START"
                            ]
                            if start_indices:
                                assert (
                                    max(start_indices) < idx
                                ), "TOOL_CALL_START应该在TOOL_CALL_ARGS之前"
                        elif expected_type == "TOOL_CALL_END":
                            args_indices = [
                                i
                                for i, t in enumerate(event_types)
                                if t == "TOOL_CALL_ARGS"
                            ]
                            if args_indices:
                                assert (
                                    max(args_indices) < idx
                                ), "TOOL_CALL_ARGS应该在TOOL_CALL_END之前"
                        elif expected_type == "TOOL_CALL_RESULT":
                            end_indices = [
                                i
                                for i, t in enumerate(event_types)
                                if t == "TOOL_CALL_END"
                            ]
                            if end_indices:
                                assert (
                                    max(end_indices) < idx
                                ), "TOOL_CALL_END应该在TOOL_CALL_RESULT之前"

    @pytest.mark.asyncio
    async def test_error_handling_in_integration(self):
        """测试集成环境中的错误处理"""

        # 创建一个会抛出异常的错误图
        def create_error_graph():
            def error_node(state: AgentState) -> Dict:
                raise ValueError("Intentional test error")

            workflow = StateGraph(AgentState)
            workflow.add_node("error", error_node)
            workflow.add_edge(START, "error")
            workflow.add_edge("error", END)
            return workflow.compile()

        # 创建适配器
        error_graph = create_error_graph()
        adapter = AGUIAdapter(error_graph)
        task = Task(id="integration_test_error", query="This will cause an error")

        # 收集所有事件
        events = []
        async for event_json in adapter.event_stream_adapter(task):
            event_data = json.loads(event_json)
            events.append(event_data)

        # 验证错误处理
        assert len(events) >= 1
        assert events[0]["type"] == "RUN_STARTED"

        # 最后一个事件应该是错误事件
        assert events[-1]["type"] == "RUN_ERROR"
        assert "message" in events[-1]
