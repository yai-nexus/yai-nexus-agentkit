# -*- coding: utf-8 -*-
"""Embedding 模块定义了向量化模型客户端的核心接口。"""
from abc import ABC, abstractmethod
from typing import List


class BaseEmbedding(ABC):
    """向量化模型客户端的抽象基类 (ABC)。"""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        将文本转换为向量嵌入。

        Args:
            text: 需要进行向量化的文本字符串。

        Returns:
            一个表示文本向量的浮点数列表。
        """
        raise NotImplementedError
