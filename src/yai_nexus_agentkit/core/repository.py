# -*- coding: utf-8 -*-
"""Repository 模块定义了仓储模式的通用 CRUD 核心接口。"""
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """仓储模式的抽象基类 (ABC)，提供通用的 CRUD 操作。"""

    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """
        根据 ID 获取单个实体。

        Args:
            id: 实体的唯一标识符。

        Returns:
            如果找到，则返回实体对象；否则返回 None。
        """
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> List[T]:
        """
        获取所有实体的列表。

        Returns:
            一个包含所有实体的列表。
        """
        raise NotImplementedError

    @abstractmethod
    async def add(self, entity: T) -> T:
        """
        添加一个新的实体。

        Args:
            entity: 要添加的实体对象。

        Returns:
            已添加的实体对象。
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        更新一个已存在的实体。

        Args:
            entity: 要更新的实体对象。

        Returns:
            已更新的实体对象。
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: Any) -> None:
        """
        根据 ID 删除一个实体。

        Args:
            id: 要删除的实体的唯一标识符。
        """
        raise NotImplementedError 