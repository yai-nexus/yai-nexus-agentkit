import asyncio
from typing import Optional

from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from lucas_common_components.logging import setup_logger
from urllib.parse import quote
from lucas_ai_core.config.config_model import AICoreAppConfig

logger = setup_logger(name=__name__, level="DEBUG")

# 全局连接池实例和锁
_PG_POOL: Optional[AsyncConnectionPool] = None
_PG_SAVER_INSTANCE: Optional[AsyncPostgresSaver] = None
_PG_LOCK = asyncio.Lock()


class PGCheckpointClient:
    """PostgreSQL Checkpoint 客户端，使用连接池管理连接"""

    @classmethod
    async def _create_pool(cls) -> AsyncConnectionPool:
        """创建 PostgreSQL 连接池"""
        config = AICoreAppConfig.get_instance().postgresql
        DB_URI = f"postgres://{quote(config.user)}:{quote(config.password)}@{quote(config.host)}:{config.port}/{quote(config.database)}?sslmode=disable"

        logger.info("创建 PostgreSQL 连接池")

        # 连接池配置
        pool_config = {
            "min_size": 2,  # 最小连接数
            "max_size": 10,  # 最大连接数
            "timeout": 30,  # 获取连接超时时间（秒）
            "max_idle": 300,  # 连接最大空闲时间（秒）
            "max_lifetime": 3600,  # 连接最大生存时间（秒）
            "open": False,  # 不立即打开，手动控制
        }

        # 连接参数，解决多进程环境下的状态同步问题
        connection_kwargs = {
            "autocommit": True,  # 启用自动提交，避免事务隔离问题
            "prepare_threshold": 0,  # 禁用 prepared statements，避免多进程冲突
        }

        try:
            pool = AsyncConnectionPool(
                conninfo=DB_URI, kwargs=connection_kwargs, **pool_config
            )

            # 手动打开连接池
            await pool.open(wait=True, timeout=30)
            logger.info(
                f"PostgreSQL 连接池创建成功，配置: min={pool_config['min_size']}, max={pool_config['max_size']}"
            )
            return pool

        except Exception as e:
            logger.error(f"创建 PostgreSQL 连接池失败: {e}")
            raise

    @classmethod
    async def _create_saver(cls, pool: AsyncConnectionPool) -> AsyncPostgresSaver:
        """使用连接池创建 PostgresSaver 实例"""
        logger.info("创建 PostgreSQL checkpoint saver")

        try:
            saver = AsyncPostgresSaver(conn=pool)
            await saver.setup()
            logger.info("PostgreSQL checkpoint saver 创建成功")
            return saver
        except Exception as e:
            logger.error(f"创建 PostgreSQL checkpoint saver 失败: {e}")
            raise

    @classmethod
    async def get_checkpoint(cls) -> AsyncPostgresSaver:
        """
        获取 PostgresSaver 实例（线程安全的单例模式，使用连接池）
        """
        global _PG_POOL, _PG_SAVER_INSTANCE

        # 双重检查锁定模式
        if _PG_SAVER_INSTANCE is None:
            async with _PG_LOCK:
                if _PG_SAVER_INSTANCE is None:
                    # 先创建连接池
                    if _PG_POOL is None:
                        _PG_POOL = await cls._create_pool()

                    # 再创建 saver
                    _PG_SAVER_INSTANCE = await cls._create_saver(_PG_POOL)

        return _PG_SAVER_INSTANCE

    @classmethod
    async def close_saver(cls):
        """关闭 saver 和连接池"""
        global _PG_POOL, _PG_SAVER_INSTANCE

        async with _PG_LOCK:
            if _PG_SAVER_INSTANCE is not None:
                try:
                    logger.info("关闭 PostgreSQL checkpoint saver")
                    _PG_SAVER_INSTANCE = None
                except Exception as e:
                    logger.error(f"关闭 PostgreSQL checkpoint saver 时出错: {e}")

            if _PG_POOL is not None:
                try:
                    logger.info("关闭 PostgreSQL 连接池")
                    await _PG_POOL.close()
                    _PG_POOL = None
                    logger.info("PostgreSQL 连接池已关闭")
                except Exception as e:
                    logger.error(f"关闭 PostgreSQL 连接池时出错: {e}")

    @classmethod
    async def reset_saver(cls):
        """重置 saver 实例和连接池（用于测试或重新初始化）"""
        await cls.close_saver()
        logger.info("PostgreSQL checkpoint client 已重置")

    @classmethod
    async def get_pool_stats(cls) -> dict:
        """获取连接池统计信息（用于监控）"""
        global _PG_POOL

        if _PG_POOL is None:
            return {"status": "not_initialized"}

        try:
            stats = {
                "status": "active",
                "size": _PG_POOL.get_stats().pool_size,
                "available": _PG_POOL.get_stats().pool_available,
                "waiting": _PG_POOL.get_stats().requests_waiting,
                "min_size": _PG_POOL.min_size,
                "max_size": _PG_POOL.max_size,
            }
            return stats
        except Exception as e:
            logger.error(f"获取连接池统计信息失败: {e}")
            return {"status": "error", "error": str(e)}
