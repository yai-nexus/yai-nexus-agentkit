from typing import Optional

from lucas_common_components.nacos.annotate.config_annotate import nacos_config
from lucas_common_components.nacos.model.base_config import LucasBaseConfig
from pydantic import BaseModel


class PostgresqlConfig(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    pool_size: Optional[int] = None
    connection_timeout: Optional[int] = None


@nacos_config(data_id="ai-core")
class AICoreAppConfig(LucasBaseConfig):
    postgresql: Optional[PostgresqlConfig] = None
