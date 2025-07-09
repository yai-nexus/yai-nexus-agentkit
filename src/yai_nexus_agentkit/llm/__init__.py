# -*- coding: utf-8 -*-
"""
该模块提供了基于 LangChain 的 LLM（大型语言模型）客户端的创建和管理功能。

核心功能是 `LLMFactory` 类，它能够根据提供的配置动态地实例化和管理
不同提供商的 LLM 客户端，如 OpenAI, ZhipuAI 等。
"""

from langchain_core.language_models import BaseChatModel

from .config import LLMConfig
from .factory import LLMFactory, llm_factory
from .providers import LLMProvider
from .models import (
    OpenAIModel,
    AnthropicModel,
    ZhipuModel,
    TongyiModel,
    DoubaoModel,
    OpenRouterModel,
    get_model_enum,
    get_default_model,
)

__all__ = [
    # 核心工厂功能
    "LLMFactory",
    "llm_factory",  # 全局单例实例
    # 配置和枚举
    "LLMProvider",
    "LLMConfig",
    # 模型枚举
    "OpenAIModel",
    "AnthropicModel",
    "ZhipuModel",
    "TongyiModel",
    "DoubaoModel",
    "OpenRouterModel",
    # 工具函数
    "get_model_enum",
    "get_default_model",
    # LangChain 基础类
    "BaseChatModel",
]
