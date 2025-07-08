# -*- coding: utf-8 -*-
"""LLM 工厂函数实现。"""

import os
from typing import Any, Dict

from langchain_core.language_models import BaseChatModel

from .providers import LLMProvider


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
            raise ImportError("使用 OpenAI 需要安装 langchain-openai 包。" "请运行: pip install langchain-openai")
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
                "使用 Anthropic 需要安装 langchain-anthropic 包。" "请运行: pip install langchain-anthropic"
            )
        return ChatAnthropic(**config_copy)

    elif provider == LLMProvider.OPENROUTER:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "使用 OpenRouter (通过 OpenAI 兼容层) 需要安装 langchain-openai 包。"
                "请运行: pip install langchain-openai"
            )
        # OpenRouter 使用 OpenAI 兼容的 API，因此我们可以复用 ChatOpenAI。
        # config_copy 中应包含 base_url="https://openrouter.ai/api/v1"

        # 确保使用 OPENROUTER_API_KEY 环境变量中的密钥
        # 这会覆盖配置文件中的占位符
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            config_copy["api_key"] = openrouter_key
        elif "api_key" not in config_copy:
            raise ValueError("未找到 OPENROUTER_API_KEY 环境变量，请确保已正确设置。")

        return ChatOpenAI(**config_copy)

    elif provider == LLMProvider.TONGYI:
        try:
            from langchain_community.chat_models import ChatTongyi
        except ImportError:
            raise ImportError(
                "使用通义千问需要安装 langchain-community 和 dashscope 包。"
                "请运行: pip install langchain-community dashscope"
            )
        # 密钥将通过 DASHSCOPE_API_KEY 环境变量自动加载
        return ChatTongyi(**config_copy)

    else:
        # 这个分支理论上不会被达到，因为枚举已经做了检查
        raise ValueError(f"提供商 '{provider.value}' 的实现尚未添加。")


class LLMFactory:
    """
    LLM 工厂类，管理多个 LLM 实例。

    这是一个可选的增强，适合需要同时使用多个 LLM 的场景。
    """

    def __init__(self, configs: list[dict[str, Any]]):
        """
        初始化工厂，从配置列表创建多个 LLM 实例。

        Args:
            configs: LLM 配置列表，每个配置必须包含 'provider' 字段
        """
        from langchain_core.language_models import BaseChatModel
        from .config import LLMConfig

        self._clients: dict[str, BaseChatModel] = {}

        for config_dict in configs:
            # 验证配置
            config = LLMConfig(**config_dict)

            # 创建 LLM 实例
            client = create_llm(config_dict)

            # 使用 provider 作为键存储
            self._clients[config.provider.value] = client

    def get_client(self, provider: LLMProvider) -> "BaseChatModel":
        """
        获取指定提供商的 LLM 客户端。

        Args:
            provider: 提供商枚举

        Returns:
            对应的 LLM 客户端

        Raises:
            ValueError: 如果未找到指定提供商的客户端
        """
        from langchain_core.language_models import BaseChatModel

        client = self._clients.get(provider.value)
        if not client:
            available = list(self._clients.keys())
            raise ValueError(f"未找到提供商 '{provider.value}' 的客户端。" f"可用的提供商: {available}")
        return client

    def list_providers(self) -> list[str]:
        """返回所有可用的提供商列表。"""
        return list(self._clients.keys())

    def get_client_by_name(self, provider_name: str) -> "BaseChatModel":
        """
        通过提供商名称字符串获取客户端。

        Args:
            provider_name: 提供商名称字符串

        Returns:
            对应的 LLM 客户端
        """
        from langchain_core.language_models import BaseChatModel

        client = self._clients.get(provider_name)
        if not client:
            available = list(self._clients.keys())
            raise ValueError(f"未找到提供商 '{provider_name}' 的客户端。" f"可用的提供商: {available}")
        return client
