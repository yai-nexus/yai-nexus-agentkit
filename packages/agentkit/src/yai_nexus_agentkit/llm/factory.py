# -*- coding: utf-8 -*-
"""LLMFactory 定义，用于管理和提供 LLM 客户端实例。"""
import logging
import threading
from typing import Dict, Optional

from langchain_core.language_models import BaseChatModel

from .config import LLMConfig
from .internal.registry import create_langchain_llm


class LLMFactory:
    """
    LLM 客户端工厂，负责根据配置创建和缓存 LLM 客户端实例。
    这是一个单例类，确保在整个应用中只有一个实例。
    """

    _instance: Optional["LLMFactory"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._configs: Dict[str, LLMConfig] = {}
        self._clients: Dict[str, BaseChatModel] = {}
        self._initialized = True
        # 在这里可以添加从文件或环境变量加载配置的逻辑
        # self.load_configs_from_file(...)

    def register_config(self, model_id: str, config: LLMConfig):
        """
        注册一个模型配置。

        Args:
            model_id: 模型的唯一标识符。
            config: 模型的配置对象。
        """
        if model_id in self._configs:
            # 根据策略决定是忽略、警告还是抛出异常
            logging.warning(f"模型ID '{model_id}' 的配置已被覆盖。")
        self._configs[model_id] = config

    def get_model_config(self, model_id: str) -> LLMConfig:
        """
        获取指定模型的配置。

        Args:
            model_id: 模型的唯一标识符。

        Returns:
            模型的配置对象。

        Raises:
            ValueError: 如果模型ID未注册。
        """
        if model_id not in self._configs:
            raise ValueError(f"模型ID '{model_id}' 未注册。请先调用 register_config。")
        return self._configs[model_id]

    def get_llm_client(self, model_id: str) -> BaseChatModel:
        """
        获取一个 LLM 客户端实例。

        如果实例已缓存，则直接返回；否则，创建一个新实例并缓存。
        此方法是线程安全的。

        Args:
            model_id: 模型的唯一标识符。

        Returns:
            一个 BaseChatModel 的实例。
        """
        with self._lock:
            if model_id not in self._clients:
                # 客户端不存在，创建并缓存
                self._clients[model_id] = self._create_llm_instance(model_id)
            return self._clients[model_id]

    def _create_llm_instance(self, model_id: str) -> BaseChatModel:
        """
        内部方法：根据配置创建 LLM 实例。

        Args:
            model_id: 模型的唯一标识符。

        Returns:
            一个新的 BaseChatModel 实例。
        """
        # 1. 获取模型配置
        config_obj = self.get_model_config(model_id)

        # 2. 准备创建参数 (移除 provider，因为它不是 LangChain 构造函数的一部分)
        creation_params = config_obj.model_dump(exclude={"provider"})

        # 3. 委托给 registry 中的统一创建函数
        logging.info(
            f"正在为 '{model_id}' 创建新的 LLM 实例，提供商为：{config_obj.provider.value}"
        )
        return create_langchain_llm(
            provider=config_obj.provider, config=creation_params
        )


# 全局单例
llm_factory = LLMFactory()
