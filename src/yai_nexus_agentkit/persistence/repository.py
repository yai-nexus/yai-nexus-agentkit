# -*- coding: utf-8 -*-
from typing import Generic, Type, TypeVar, Optional, List, Any
from tortoise.models import Model
from tortoise.transactions import in_transaction
from tortoise.exceptions import IntegrityError
from yai_nexus_agentkit.core.repository import BaseRepository
import logging
from .models import AgentConversation

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=Model)


class TortoiseRepository(BaseRepository[T], Generic[T]):
    """基于 Tortoise ORM 的通用仓储实现"""

    def __init__(self, model_cls: Type[T]):
        self._model_cls = model_cls

    async def get(self, id: Any) -> Optional[T]:
        try:
            return await self._model_cls.get_or_none(id=id)
        except Exception as e:
            logger.error(f"Failed to get {self._model_cls.__name__} with id {id}: {e}")
            return None

    async def list(self, limit: int = 100, offset: int = 0) -> List[T]:
        try:
            return await self._model_cls.all().limit(limit).offset(offset)
        except Exception as e:
            logger.error(f"Failed to list {self._model_cls.__name__}: {e}")
            return []

    async def filter(self, **kwargs) -> List[T]:
        try:
            return await self._model_cls.filter(**kwargs)
        except Exception as e:
            logger.error(f"Failed to filter {self._model_cls.__name__}: {e}")
            return []

    async def add(self, entity: T) -> T:
        try:
            await entity.save()
            return entity
        except IntegrityError as e:
            logger.error(
                f"Integrity error while adding {self._model_cls.__name__}: {e}"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to add {self._model_cls.__name__}: {e}")
            raise

    async def update(self, entity: T) -> T:
        await entity.save()
        return entity

    async def delete(self, id: Any) -> bool:
        try:
            entity = await self._model_cls.get(id=id)
            await entity.delete()
            return True
        except Exception:
            return False

    async def exists(self, id: Any) -> bool:
        return await self._model_cls.filter(id=id).exists()

    async def bulk_create(self, entities: List[T]) -> List[T]:
        """批量创建实体"""
        try:
            async with in_transaction():
                await self._model_cls.bulk_create(entities)
            return entities
        except Exception as e:
            logger.error(f"Failed to bulk create {self._model_cls.__name__}: {e}")
            raise

    async def count(self, **kwargs) -> int:
        """计数"""
        try:
            return await self._model_cls.filter(**kwargs).count()
        except Exception as e:
            logger.error(f"Failed to count {self._model_cls.__name__}: {e}")
            return 0


class ConversationRepository(TortoiseRepository[AgentConversation]):
    def __init__(
        self, db_config=None
    ):  # db_config is not used but kept for DI compatibility
        super().__init__(AgentConversation)
