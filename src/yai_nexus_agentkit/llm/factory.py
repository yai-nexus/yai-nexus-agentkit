# -*- coding: utf-8 -*-
"""LLM 工厂函数实现。"""

from typing import Any, Dict

from langchain_core.language_models import BaseChatModel

from .providers import LLMProvider
from .internal.registry import PROVIDER_REGISTRY






class LLMFactory:
    """
    LLM 工厂类，统一管理 LLM 实例。

    支持懒加载和单个/批量配置，适合各种使用场景。
    """

    def __init__(self, configs: dict[str, dict[str, Any]] = None):
        """
        初始化工厂。

        Args:
            configs: 可选的配置字典，键为 provider 名称，值为配置字典
        """
        from langchain_core.language_models import BaseChatModel
        
        self._configs: dict[str, dict[str, Any]] = configs or {}
        self._clients: dict[str, BaseChatModel] = {}

    def add_config(self, provider: str, config: dict[str, Any]):
        """
        添加单个 LLM 配置。

        Args:
            provider: 提供商名称
            config: LLM 配置字典
        """
        self._configs[provider] = config
        # 如果已经创建了该提供商的客户端，需要清除缓存
        if provider in self._clients:
            del self._clients[provider]

    def _create_llm(self, config: Dict[str, Any]) -> BaseChatModel:
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

        # 从注册表中获取对应的创建函数
        creator_func = PROVIDER_REGISTRY.get(provider)
        if not creator_func:
            available_providers = [p.value for p in PROVIDER_REGISTRY.keys()]
            raise ValueError(
                f"提供商 '{provider.value}' 的实现尚未添加。"
                f"可用的提供商: {available_providers}"
            )

        # 调用对应的创建函数
        return creator_func(config_copy)

    def get_client(self, provider: LLMProvider) -> BaseChatModel:
        """
        获取指定提供商的 LLM 客户端（懒加载）。

        Args:
            provider: 提供商枚举

        Returns:
            对应的 LLM 客户端

        Raises:
            ValueError: 如果未找到指定提供商的配置
        """
        provider_name = provider.value
        
        # 懒加载：如果客户端不存在，则创建
        if provider_name not in self._clients:
            config = self._configs.get(provider_name)
            if not config:
                available = list(self._configs.keys())
                raise ValueError(
                    f"未找到提供商 '{provider_name}' 的配置。"
                    f"可用的提供商: {available}"
                )
            
            # 验证配置
            from .config import LLMConfig
            LLMConfig(**config)
            
            # 创建客户端
            self._clients[provider_name] = self._create_llm(config)
        
        return self._clients[provider_name]

    def list_providers(self) -> list[str]:
        """返回所有可用的提供商列表。"""
        return list(self._configs.keys())

    def get_client_by_name(self, provider_name: str) -> BaseChatModel:
        """
        通过提供商名称字符串获取客户端（懒加载）。

        Args:
            provider_name: 提供商名称字符串

        Returns:
            对应的 LLM 客户端

        Raises:
            ValueError: 如果提供商名称无效或未找到配置
        """
        try:
            provider = LLMProvider(provider_name)
            return self.get_client(provider)
        except ValueError:
            available = list(self._configs.keys())
            raise ValueError(
                f"不支持的提供商 '{provider_name}'。"
                f"可用的提供商: {available}"
            )
