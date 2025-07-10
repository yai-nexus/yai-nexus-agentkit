# -*- coding: utf-8 -*-
"""Checkpoint 模块定义了状态持久化存储的核心接口。"""
from abc import ABC, abstractmethod
from typing import Any, Optional, List


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

    @abstractmethod
    async def list(self, limit: int = 100) -> List[str]:
        """
        列出所有检查点键。

        Args:
            limit: 返回的最大记录数，默认100

        Returns:
            检查点键的列表。
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        删除检查点。

        Args:
            key: 要删除的检查点键。

        Returns:
            删除成功返回 True，否则返回 False。
        """
        raise NotImplementedError

    @abstractmethod
    async def setup(self) -> None:
        """
        初始化检查点存储。
        """
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """
        清理检查点存储资源。
        """
        raise NotImplementedError
