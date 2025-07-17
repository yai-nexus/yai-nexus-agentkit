"""
Agent 模块 - LangGraph Agent 定义和配置
"""
from typing import Annotated, Dict, List, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from loguru import logger
from yai_nexus_agentkit.adapter.agui_adapter import AGUIAdapter
from llm_setup import create_llm


class AgentState(TypedDict):
    """定义 Agent 的状态，包含消息列表"""
    messages: Annotated[List[BaseMessage], add_messages]


def llm_agent_node(state: AgentState) -> Dict[str, List[BaseMessage]]:
    """调用 LLM 并返回其响应"""
    logger.info("LLM Agent node is processing the state.")
    llm = create_llm()
    return {"messages": [llm.invoke(state["messages"])]}


def create_agent():
    """创建并编译 LangGraph Agent"""
    # 创建 Agent 的图 (Graph)
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("agent", llm_agent_node)
    graph_builder.set_entry_point("agent")
    graph_builder.set_finish_point("agent")

    # 编译图，得到可运行的 Agent
    agent = graph_builder.compile()
    logger.info("LangGraph Agent created successfully")
    
    return agent


def create_agui_adapter():
    """创建 AGUIAdapter 实例"""
    agent = create_agent()
    agui_adapter = AGUIAdapter(agent=agent)
    logger.info("AGUIAdapter created successfully")
    
    return agui_adapter