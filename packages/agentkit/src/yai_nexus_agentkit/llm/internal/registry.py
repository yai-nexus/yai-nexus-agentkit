# -*- coding: utf-8 -*-
"""提供商注册表实现，并提供统一的创建函数。"""

from typing import Any, Callable, Dict

from langchain_core.language_models import BaseChatModel

from ..providers import LLMProvider


# ------------------------------------------------------------------------------
#  私有创建函数 (Private Creator Functions)
#  这些函数是本模块的实现细节，不应被外部直接调用。
# ------------------------------------------------------------------------------


def _create_openai_client(config: Dict[str, Any]) -> BaseChatModel:
    """创建 OpenAI 客户端。"""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "使用 OpenAI 需要安装 langchain-openai 包。"
            "请运行: pip install langchain-openai"
        )
    return ChatOpenAI(**config)


def _create_zhipu_client(config: Dict[str, Any]) -> BaseChatModel:
    """创建 ZhipuAI 客户端。"""
    try:
        from langchain_community.chat_models import ChatZhipuAI
    except ImportError:
        raise ImportError(
            "使用 ZhipuAI 需要安装 langchain-community 和 zhipuai 包。"
            "请运行: pip install langchain-community zhipuai"
        )
    return ChatZhipuAI(**config)


def _create_anthropic_client(config: Dict[str, Any]) -> BaseChatModel:
    """创建 Anthropic 客户端。"""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "使用 Anthropic 需要安装 langchain-anthropic 包。"
            "请运行: pip install langchain-anthropic"
        )
    return ChatAnthropic(**config)


def _create_openrouter_client(config: Dict[str, Any]) -> BaseChatModel:
    """创建 OpenRouter 客户端。"""
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


def _create_tongyi_client(config: Dict[str, Any]) -> BaseChatModel:
    """创建通义千问客户端。"""
    try:
        from langchain_community.chat_models import ChatTongyi
    except ImportError:
        raise ImportError(
            "使用通义千问需要安装 langchain-community 和 dashscope 包。"
            "请运行: pip install langchain-community dashscope"
        )
    return ChatTongyi(**config)


def _create_doubao_client(config: Dict[str, Any]) -> BaseChatModel:
    """创建豆包客户端。"""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "使用豆包需要安装 langchain-openai 包。"
            "请运行: pip install langchain-openai"
        )
    # 豆包使用 OpenAI 兼容的 API
    return ChatOpenAI(**config)


# ------------------------------------------------------------------------------
#  提供商注册表 (Provider Registry)
#  将提供商枚举映射到其对应的私有创建函数。
# ------------------------------------------------------------------------------

_PROVIDER_REGISTRY: Dict[LLMProvider, Callable[[Dict[str, Any]], BaseChatModel]] = {
    LLMProvider.OPENAI: _create_openai_client,
    LLMProvider.ZHIPU: _create_zhipu_client,
    LLMProvider.ANTHROPIC: _create_anthropic_client,
    LLMProvider.OPENROUTER: _create_openrouter_client,
    LLMProvider.TONGYI: _create_tongyi_client,
    LLMProvider.DOUBAO: _create_doubao_client,
}


# ------------------------------------------------------------------------------
#  公共创建函数 (Public Creator Function)
#  这是从外部调用本模块的唯一入口。
# ------------------------------------------------------------------------------


def create_langchain_llm(
    provider: LLMProvider, config: Dict[str, Any]
) -> BaseChatModel:
    """
    根据提供商和配置创建 LangChain BaseChatModel 实例。

    这是 llm.internal 包对外的统一创建入口。它会查找注册表，
    并调用相应的私有创建函数。

    Args:
        provider: LLM 提供商枚举。
        config: 不包含 provider 字段的配置字典。

    Returns:
        一个 BaseChatModel 的实例。

    Raises:
        ValueError: 如果提供商不受支持。
    """
    creator_func = _PROVIDER_REGISTRY.get(provider)
    if not creator_func:
        raise ValueError(f"不支持的 LLM 提供商：{provider.value}")

    return creator_func(config)
