# -*- coding: utf-8 -*-
"""LLM 模块定义了语言模型客户端的核心接口。"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseLLM(ABC):
    """语言模型客户端的抽象基类 (ABC)。"""

    @abstractmethod
    async def ask(self, prompt: str, model: Optional[str] = None) -> str:
        """
        向语言模型发送一个提示并获取回复。

        Args:
            prompt: 发送给语言模型的提示字符串。
            model: (可选) 要使用的具体模型名称。

        Returns:
            来自语言模型的回复字符串。
        """
        raise NotImplementedError 