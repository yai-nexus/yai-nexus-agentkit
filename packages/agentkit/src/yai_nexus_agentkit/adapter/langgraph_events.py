# -*- coding: utf-8 -*-
"""
LangGraph事件类型枚举定义
用于消除魔术字符串，提供强类型支持
"""

from enum import Enum


class LangGraphEventType(str, Enum):
    """
    LangGraph流式事件类型枚举
    提供强类型支持，避免在适配器逻辑中使用魔术字符串
    """

    # 工具相关事件
    ON_TOOL_START = "on_tool_start"
    ON_TOOL_END = "on_tool_end"

    # 聊天模型事件
    ON_CHAT_MODEL_START = "on_chat_model_start"
    ON_CHAT_MODEL_STREAM = "on_chat_model_stream"
    ON_CHAT_MODEL_END = "on_chat_model_end"

    # 链执行事件
    ON_CHAIN_START = "on_chain_start"
    ON_CHAIN_STREAM = "on_chain_stream"
    ON_CHAIN_END = "on_chain_end"

    # 节点执行事件
    ON_NODE_START = "on_node_start"
    ON_NODE_END = "on_node_end"

    # 自定义事件
    ON_CUSTOM_EVENT = "on_custom_event"

    # LLM相关事件
    ON_LLM_START = "on_llm_start"
    ON_LLM_STREAM = "on_llm_stream"
    ON_LLM_END = "on_llm_end"

    # 检索器事件
    ON_RETRIEVER_START = "on_retriever_start"
    ON_RETRIEVER_END = "on_retriever_end"
