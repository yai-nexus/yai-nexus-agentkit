# -*- coding: utf-8 -*-
"""LLM 客户端创建函数实现。"""

from typing import Any, Dict

from langchain_core.language_models import BaseChatModel


def create_openai_client(config: Dict[str, Any]) -> BaseChatModel:
    """
    创建 OpenAI 客户端。

    Args:
        config: 不包含 provider 字段的配置字典

    Returns:
        ChatOpenAI 实例
    
    Note:
        需要设置 OPENAI_API_KEY 环境变量
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "使用 OpenAI 需要安装 langchain-openai 包。"
            "请运行: pip install langchain-openai"
        )
    return ChatOpenAI(**config)


def create_zhipu_client(config: Dict[str, Any]) -> BaseChatModel:
    """
    创建 ZhipuAI 客户端。

    Args:
        config: 不包含 provider 字段的配置字典

    Returns:
        ChatZhipuAI 实例
    
    Note:
        需要设置 ZHIPU_API_KEY 环境变量
    """
    try:
        from langchain_community.chat_models import ChatZhipuAI
    except ImportError:
        raise ImportError(
            "使用 ZhipuAI 需要安装 langchain-community 和 zhipuai 包。"
            "请运行: pip install langchain-community zhipuai"
        )
    return ChatZhipuAI(**config)


def create_anthropic_client(config: Dict[str, Any]) -> BaseChatModel:
    """
    创建 Anthropic 客户端。

    Args:
        config: 不包含 provider 字段的配置字典

    Returns:
        ChatAnthropic 实例
    
    Note:
        需要设置 ANTHROPIC_API_KEY 环境变量
    """
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "使用 Anthropic 需要安装 langchain-anthropic 包。"
            "请运行: pip install langchain-anthropic"
        )
    return ChatAnthropic(**config)


def create_openrouter_client(config: Dict[str, Any]) -> BaseChatModel:
    """
    创建 OpenRouter 客户端。

    Args:
        config: 不包含 provider 字段的配置字典

    Returns:
        ChatOpenAI 实例（使用 OpenRouter API）
    
    Note:
        需要设置 OPENROUTER_API_KEY 环境变量
        config 中应包含 base_url="https://openrouter.ai/api/v1"
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "使用 OpenRouter (通过 OpenAI 兼容层) 需要安装 langchain-openai 包。"
            "请运行: pip install langchain-openai"
        )

    # OpenRouter 使用 OpenAI 兼容的 API，因此我们可以复用 ChatOpenAI
    # LangChain 会自动从环境变量中读取 OPENROUTER_API_KEY
    return ChatOpenAI(**config)


def create_tongyi_client(config: Dict[str, Any]) -> BaseChatModel:
    """
    创建通义千问客户端。

    Args:
        config: 不包含 provider 字段的配置字典

    Returns:
        ChatTongyi 实例
    
    Note:
        需要设置 DASHSCOPE_API_KEY 环境变量
    """
    try:
        from langchain_community.chat_models import ChatTongyi
    except ImportError:
        raise ImportError(
            "使用通义千问需要安装 langchain-community 和 dashscope 包。"
            "请运行: pip install langchain-community dashscope"
        )
    return ChatTongyi(**config)