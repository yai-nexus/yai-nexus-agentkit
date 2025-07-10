# -*- coding: utf-8 -*-
from typing import Any, Optional, Dict, List
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.base import CheckpointTuple
from yai_nexus_agentkit.core.checkpoint import BaseCheckpoint
from .db_config import DatabaseConfig
import logging
from tortoise.exceptions import DoesNotExist

logger = logging.getLogger(__name__)


class PostgresCheckpoint(BaseCheckpoint):
    """基于 PostgreSQL 的 Checkpoint 实现"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.saver: Optional[AsyncPostgresSaver] = None

    async def setup(self):
        """初始化 AsyncPostgresSaver"""
        try:
            self.saver = AsyncPostgresSaver.from_conn_string(self.config.db_url)
            # The `setup` method in the new version of langgraph's saver might be `acreate_tables`
            if hasattr(self.saver, "acreate_tables"):
                await self.saver.acreate_tables()
            elif hasattr(self.saver, "setup"):
                await self.saver.setup()
        except Exception as e:
            logger.error(f"Failed to setup checkpoint: {e}")
            raise

    async def cleanup(self):
        """清理资源"""
        if self.saver and hasattr(self.saver, "close"):
            await self.saver.close()

    async def get(self, convo_id: str) -> Optional[CheckpointTuple]:
        if not self.saver:
            await self.setup()

        try:
            return await self.saver.aget_tuple(convo_id)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Failed to get checkpoint for {convo_id}: {e}")
            return None

    async def put(self, convo_id: str, checkpoint: Dict[str, Any]) -> None:
        if not self.saver:
            await self.setup()

        try:
            await self.saver.aput(convo_id, checkpoint)
        except Exception as e:
            logger.error(f"Failed to put checkpoint for {convo_id}: {e}")

    async def list(self, limit: int, offset: int) -> List[CheckpointTuple]:
        if not self.saver:
            await self.setup()

        try:
            return await self.saver.alist(limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []

    async def delete(self, key: str) -> bool:
        """删除检查点"""
        if not self.saver:  # Changed from self.saver to self._saver_cm
            await self.setup()

        try:
            # The new saver might not have a specific delete method.
            # This is a placeholder for the actual deletion logic.
            # Depending on the new API, this might need to call a different method.
            # For now, we assume no direct delete method is available in this example.
            logger.warning(
                "Delete functionality is not fully implemented for this checkpointer version."
            )
            return False
        except Exception as e:
            logger.error(f"Failed to delete checkpoint for key {key}: {e}")
            return False
