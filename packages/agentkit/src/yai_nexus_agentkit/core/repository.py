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
    async def list(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        获取实体列表，支持分页。

        Args:
            limit: 返回的最大记录数，默认100
            offset: 跳过的记录数，默认0

        Returns:
            一个包含实体的列表。
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
    async def delete(self, id: Any) -> bool:
        """
        根据 ID 删除一个实体。

        Args:
            id: 要删除的实体的唯一标识符。

        Returns:
            删除成功返回 True，否则返回 False。
        """
        raise NotImplementedError

    @abstractmethod
    async def filter(self, **kwargs) -> List[T]:
        """
        根据条件过滤实体。

        Args:
            **kwargs: 过滤条件

        Returns:
            符合条件的实体列表。
        """
        raise NotImplementedError

    @abstractmethod
    async def exists(self, id: Any) -> bool:
        """
        检查实体是否存在。

        Args:
            id: 实体的唯一标识符。

        Returns:
            存在返回 True，否则返回 False。
        """
        raise NotImplementedError

    @abstractmethod
    async def count(self, **kwargs) -> int:
        """
        计数实体数量。

        Args:
            **kwargs: 过滤条件

        Returns:
            符合条件的实体数量。
        """
        raise NotImplementedError

    @abstractmethod
    async def bulk_create(self, entities: List[T]) -> List[T]:
        """
        批量创建实体。

        Args:
            entities: 要创建的实体列表

        Returns:
            已创建的实体列表。
        """
        raise NotImplementedError
