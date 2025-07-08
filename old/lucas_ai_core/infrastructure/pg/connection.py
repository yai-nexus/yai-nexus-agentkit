from typing import Dict

from lucas_common_components.nacos.core.nacos_manager import NacosConfigManager
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from ...config.config_model import AICoreAppConfig


async def init_db():
    """初始化数据库"""
    NacosConfigManager.get_instance().register_config(AICoreAppConfig)

    config = DatabaseConnection.get_tortoise_config()

    # 初始化 Tortoise
    await Tortoise.init(
        config=config, modules={"models": ["lucas_ai_core.infrastructure.pg.models"]}
    )


class DatabaseConnection:
    def __init__(self, config: Dict = None):
        """初始化数据库连接管理器

        Args:
            config: 数据库配置字典，如果为None则使用默认配置
        """
        self.config = (config or self.get_tortoise_config(),)

        # 验证配置格式
        if not isinstance(self.config, dict):
            raise ValueError("Config must be a dictionary")

        if "connections" not in self.config:
            raise ValueError("Config must contain 'connections' section")

        if "apps" not in self.config:
            raise ValueError("Config must contain 'apps' section")

    async def init(self):
        """初始化所有数据库连接"""
        await Tortoise.init(config=self.config)

    @staticmethod
    async def close():
        """关闭所有数据库连接"""
        await Tortoise.close_connections()

    @staticmethod
    def register_tortoise(cls, app, config: dict = None):
        """注册 Tortoise 到 FastAPI 应用

        Args:
            app: FastAPI 应用实例
            config: Tortoise ORM 配置，如果为None则使用默认配置
        """
        register_tortoise(
            app,
            config=config or cls.get_tortoise_config(),
            generate_schemas=True,
        )

    @staticmethod
    def get_tortoise_config() -> dict:
        """获取 Tortoise ORM 配置

        Returns:
            包含所有数据库配置的字典
        """

        db_config = AICoreAppConfig.get_instance().postgresql

        # 构建 Tortoise 配置
        config = {
            "connections": {
                "default": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": db_config.host,
                        "port": db_config.port,
                        "user": db_config.user,
                        "password": db_config.password,
                        "database": db_config.database,
                        "max_size": db_config.pool_size,
                        "command_timeout": db_config.connection_timeout,
                    },
                }
            },
            "apps": {
                "models": {  # 改回 default 应用
                    "models": [
                        "lucas_ai_core.infrastructure.pg.models.ai_conversation",
                        "lucas_ai_core.infrastructure.pg.models.ai_message",
                    ],
                    "default_connection": "default",
                }
            },
            "use_tz": False,
            "timezone": "Asia/Shanghai",
        }
        return config
