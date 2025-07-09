from typing import Any, Optional, Dict, List
from langgraph.checkpoint.postgres import AsyncPostgresSaver
from langgraph.checkpoint.base import CheckpointTuple
from yai_nexus_agentkit.core.checkpoint import BaseCheckpoint
from .db_config import DatabaseConfig
import logging

logger = logging.getLogger(__name__)

class PostgresCheckpoint(BaseCheckpoint):
    """基于 PostgreSQL 的 Checkpoint 实现"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.saver = None
    
    async def setup(self):
        """初始化 AsyncPostgresSaver"""
        try:
            self.saver = AsyncPostgresSaver.from_conn_string(self.config.db_url)
            await self.saver.setup()
        except Exception as e:
            logger.error(f"Failed to setup checkpoint: {e}")
            raise
    
    async def cleanup(self):
        """清理资源"""
        if self.saver:
            await self.saver.close()

    async def get(self, key: str) -> Optional[CheckpointTuple]:
        """获取检查点"""
        if not self.saver:
            await self.setup()
        
        try:
            config = {"configurable": {"thread_id": key}}
            checkpoint = await self.saver.aget(config)
            return checkpoint
        except Exception as e:
            logger.error(f"Failed to get checkpoint for key {key}: {e}")
            return None

    async def put(self, key: str, checkpoint: CheckpointTuple) -> None:
        """保存检查点"""
        if not self.saver:
            await self.setup()
        
        try:
            config = {"configurable": {"thread_id": key}}
            await self.saver.aput(config, checkpoint)
        except Exception as e:
            logger.error(f"Failed to put checkpoint for key {key}: {e}")
            raise
    
    async def list(self, limit: int = 100) -> List[str]:
        """列出所有检查点键"""
        if not self.saver:
            await self.setup()
        
        try:
            from tortoise import Tortoise
            
            # 使用 Tortoise ORM 直接查询数据库获取所有 thread_id
            connection = Tortoise.get_connection("default")
            result = await connection.execute_query('SELECT thread_id FROM "threads" LIMIT $1', [limit])
            
            # 提取 thread_id 列表
            thread_ids = [str(row[0]) for row in result[1]]
            return thread_ids
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []

    async def delete(self, key: str) -> bool:
        """删除检查点"""
        if not self.saver:
            await self.setup()
        
        try:
            config = {"configurable": {"thread_id": key}}
            # 使用 AsyncPostgresSaver 的 adelete_thread 方法删除线程的所有检查点
            await self.saver.adelete_thread(config)
            return True
        except Exception as e:
            logger.error(f"Failed to delete checkpoint for key {key}: {e}")
            return False