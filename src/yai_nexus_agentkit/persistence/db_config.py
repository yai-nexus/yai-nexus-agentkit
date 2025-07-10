from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """数据库连接配置"""

    db_url: str = Field(
        ...,
        description="数据库连接URL，例如: postgres://user:pass@host:port/db",
        examples=["postgres://postgres:mysecretpassword@localhost:5432/agent_db"],
    )
    generate_schemas: bool = Field(True, description="是否在启动时自动创建数据库表")
    max_connections: int = Field(20, description="最大连接数")
    min_connections: int = Field(1, description="最小连接数")
    connection_timeout: int = Field(30, description="连接超时时间（秒）")
    query_timeout: int = Field(30, description="查询超时时间（秒）")

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """从环境变量创建配置"""
        import os

        return cls(
            db_url=os.getenv(
                "DATABASE_URL", "postgres://postgres:password@localhost:5432/agent_db"
            ),
            generate_schemas=os.getenv("DB_GENERATE_SCHEMAS", "true").lower() == "true",
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "20")),
            min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "1")),
            connection_timeout=int(os.getenv("DB_CONNECTION_TIMEOUT", "30")),
            query_timeout=int(os.getenv("DB_QUERY_TIMEOUT", "30")),
        )


TORTOISE_ORM_CONFIG_TEMPLATE = {
    "connections": {"default": ""},  # 将被 db_url 填充
    "apps": {
        "models": {
            "models": ["yai_nexus_agentkit.persistence.models"],
            "default_connection": "default",
        }
    },
}
