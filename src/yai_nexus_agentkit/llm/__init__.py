# -*- coding: utf-8 -*-
"""
该模块提供了基于 LangChain 的 LLM（大型语言模型）客户端的创建和管理功能。

核心功能是 `create_llm` 工厂函数，它能够根据提供的配置动态地实例化
不同提供商的 LLM 客户端，如 OpenAI, ZhipuAI 等。
"""

from enum import Enum
from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """支持的 LLM 提供商枚举。"""

    OPENAI = "openai"
    ZHIPU = "zhipu"
    ANTHROPIC = "anthropic"


class LLMConfig(BaseModel):
    """
    LLM 配置的基础模型。

    所有特定提供商的配置模型都应继承自此模型。
    """

    provider: LLMProvider = Field(..., description="LLM 提供商的名称。")
    model: str = Field(..., description="要使用的具体模型名称。")

    class Config:
        extra = "allow"  # 允许未在模型中定义的额外字段


def create_llm(config: Dict[str, Any]) -> BaseChatModel:
    """
    根据给定的配置字典创建并返回一个 LangChain 的 BaseChatModel 实例。

    该工厂函数根据配置中的 'provider' 字段来决定实例化哪个 LLM 客户端。
    它会自动处理不同客户端的导入和初始化。

    Args:
        config: 包含 LLM 客户端配置的字典。必须包含 'provider' 和 'model' 键。
                其他键值对将作为关键字参数传递给客户端的构造函数。

    Returns:
        一个配置好的、继承自 BaseChatModel 的 LLM 客户端实例。

    Raises:
        ImportError: 如果请求的提供商需要一个未安装的包。
        ValueError: 如果 'provider' 字段无效或不受支持。
    """
    config_copy = config.copy()
    provider_str = config_copy.pop("provider", None)

    if not provider_str:
        raise ValueError("配置字典中必须包含 'provider' 字段。")

    try:
        provider = LLMProvider(provider_str)
    except ValueError:
        raise ValueError(f"不支持的 LLM 提供商: '{provider_str}'")

    if provider == LLMProvider.OPENAI:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "使用 OpenAI 需要安装 langchain-openai 包。"
                "请运行: pip install langchain-openai"
            )
        return ChatOpenAI(**config_copy)

    elif provider == LLMProvider.ZHIPU:
        try:
            from langchain_community.chat_models import ChatZhipuAI
        except ImportError:
            raise ImportError(
                "使用 ZhipuAI 需要安装 langchain-community 和 zhipuai 包。"
                "请运行: pip install langchain-community zhipuai"
            )
        return ChatZhipuAI(**config_copy)

    elif provider == LLMProvider.ANTHROPIC:
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "使用 Anthropic 需要安装 langchain-anthropic 包。"
                "请运行: pip install langchain-anthropic"
            )
        return ChatAnthropic(**config_copy)

    else:
        # 这个分支理论上不会被达到，因为枚举已经做了检查
        raise ValueError(f"提供商 '{provider.value}' 的实现尚未添加。")


__all__ = ["create_llm", "LLMProvider", "LLMConfig", "BaseChatModel"]
