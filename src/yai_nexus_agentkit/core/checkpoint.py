# -*- coding: utf-8 -*-
"""Checkpoint 模块定义了状态持久化存储的核心接口。"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseCheckpoint(ABC):
    """状态持久化存储的抽象基类 (ABC)。"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        根据键从持久化存储中检索状态。

        Args:
            key: 用于标识状态的唯一键。

        Returns:
            如果找到，则返回存储的状态；否则返回 None。
        """
        raise NotImplementedError

    @abstractmethod
    async def put(self, key: str, value: Any) -> None:
        """
        将状态存入持久化存储中。

        Args:
            key: 用于标识状态的唯一键。
            value: 需要存储的状态。
        """
        raise NotImplementedError 