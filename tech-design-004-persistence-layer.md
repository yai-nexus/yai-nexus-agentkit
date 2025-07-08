
# 技术设计方案: 004-持久化层

## 1. 背景

一个有状态的 Agent 必须能够记忆。无论是长期的对话历史，还是短暂的执行状态（检查点），都需要一个稳定可靠的持久化层。

`src/` 目录中已经定义了优雅的持久化接口：
- `core/repository.py`: `BaseRepository` 为领域对象的 CRUD 提供了通用接口。
- `core/checkpoint.py`: `BaseCheckpoint` 为 Agent 执行状态的存取提供了接口。

旧代码 (`old/lucas_ai_core/infrastructure/pg/`) 中有一套基于 Tortoise ORM 和 PostgreSQL 的完整实现，但其配置方式（依赖 Nacos）、模型定义和仓储实现都与具体业务逻辑紧密耦合。

此方案旨在设计并实现上述核心接口，构建一个与业务逻辑解耦、配置灵活、易于维护的持久化层。

设计目标：
- **实现核心接口**: 提供 `BaseRepository` 和 `BaseCheckpoint` 的具体实现。
- **技术栈选型**: 沿用 Tortoise ORM + PostgreSQL，这是一个成熟的异步 Python 技术栈。
- **配置驱动**: 数据库连接信息应通过环境变量或配置文件加载，而非硬编码或依赖外部服务。
- **模型标准化**: 定义通用的、与具体业务场景弱相关的数据库模型，如 `Conversation` 和 `Message`。
- **解耦与注入**: 业务代码应仅依赖于核心接口，具体实现通过依赖注入在应用启动时装配。

## 2. 核心设计

所有持久化相关的实现将位于 `src/yai_nexus_agentkit/persistence/` 目录下。

### 2.1. 配置 (`persistence/db_config.py`)

首先定义一个 Pydantic 模型来管理数据库连接配置。

```python
# src/yai_nexus_agentkit/persistence/db_config.py
from pydantic import BaseModel, Field

class DatabaseConfig(BaseModel):
    """数据库连接配置"""
    db_url: str = Field(
        ...,
        description="数据库连接URL，例如: postgres://user:pass@host:port/db",
        examples=["postgres://postgres:mysecretpassword@localhost:5432/agent_db"]
    )
    generate_schemas: bool = Field(True, description="是否在启动时自动创建数据库表")

TORTOISE_ORM_CONFIG_TEMPLATE = {
    "connections": {"default": ""}, # 将被 db_url 填充
    "apps": {
        "models": {
            "models": ["yai_nexus_agentkit.persistence.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}
```

### 2.2. 数据库模型 (`persistence/models/`)

定义核心的数据库实体模型。

```python
# src/yai_nexus_agentkit/persistence/models/conversation.py
from tortoise import fields
from tortoise.models import Model

class Conversation(Model):
    """会话模型"""
    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=255, null=True)
    metadata_ = fields.JSONField(null=True, description="元数据")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "agent_conversations"

# src/yai_nexus_agentkit/persistence/models/message.py
from tortoise import fields
from tortoise.models import Model

class Message(Model):
    """消息模型"""
    id = fields.UUIDField(pk=True)
    conversation: fields.ForeignKeyRelation["Conversation"] = fields.ForeignKeyField(
        "models.Conversation", related_name="messages", on_delete=fields.CASCADE
    )
    role = fields.CharField(max_length=50, description="角色 (e.g., 'user', 'assistant')")
    content = fields.TextField()
    metadata_ = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "agent_messages"
```

### 2.3. 通用仓储实现 (`persistence/repository.py`)

实现一个通用的、基于 Tortoise ORM 的 `BaseRepository`。

```python
# src/yai_nexus_agentkit/persistence/repository.py

from typing import Generic, Type, TypeVar, Optional, List, Any
from tortoise.models import Model
from yai_nexus_agentkit.core.repository import BaseRepository

T = TypeVar("T", bound=Model)

class TortoiseRepository(BaseRepository[T], Generic[T]):
    """基于 Tortoise ORM 的通用仓储实现"""

    def __init__(self, model_cls: Type[T]):
        self._model_cls = model_cls

    async def get(self, id: Any) -> Optional[T]:
        return await self._model_cls.get_or_none(id=id)

    async def list(self) -> List[T]:
        return await self._model_cls.all()

    async def add(self, entity: T) -> T:
        await entity.save()
        return entity
    
    # ... 其他方法的实现 (update, delete)
```

### 2.4. Checkpoint 实现 (`persistence/checkpoint.py`)

实现 `BaseCheckpoint`，内部封装 `langgraph` 的 `AsyncPostgresSaver`。

```python
# src/yai_nexus_agentkit/persistence/checkpoint.py

from typing import Any, Optional
from langgraph.checkpoint.postgres import AsyncPostgresSaver
from yai_nexus_agentkit.core.checkpoint import BaseCheckpoint
from .db_config import DatabaseConfig

class PostgresCheckpoint(BaseCheckpoint):
    """基于 PostgreSQL 的 Checkpoint 实现"""

    def __init__(self, config: DatabaseConfig):
        # AsyncPostgresSaver 需要一个连接池或 DSN
        self.saver = AsyncPostgresSaver.from_conn_string(config.db_url)

    async def get(self, key: str) -> Optional[Any]:
        # key 对应 langgraph 的 thread_id
        config = {"configurable": {"thread_id": key}}
        checkpoint = await self.saver.aget(config)
        return checkpoint

    async def put(self, key: str, value: Any) -> None:
        config = {"configurable": {"thread_id": key}}
        await self.saver.aput(config, value)
```

## 3. 目录结构

```
src/yai_nexus_agentkit/
├── core/
│   ├── repository.py       # BaseRepository 接口
│   └── checkpoint.py       # BaseCheckpoint 接口
└── persistence/
    ├── __init__.py
    ├── db_config.py        # 数据库配置模型
    ├── models/             # Tortoise ORM 模型
    │   ├── __init__.py
    │   ├── conversation.py
    │   └── message.py
    ├── repository.py       # TortoiseRepository 实现
    └── checkpoint.py       # PostgresCheckpoint 实现
```

## 4. 使用示例

在应用的启动和关闭生命周期中管理数据库连接。

```python
# examples/fast_api_app/main.py

from fastapi import FastAPI
from tortoise import Tortoise
from .core.services import Container

app = FastAPI()
container = Container()

@app.on_event("startup")
async def startup_event():
    db_config = container.db_config() # 从容器获取配置
    
    # 动态构建 Tortoise 配置
    tortoise_config = TORTOISE_ORM_CONFIG_TEMPLATE
    tortoise_config["connections"]["default"] = db_config.db_url
    
    await Tortoise.init(config=tortoise_config)
    if db_config.generate_schemas:
        await Tortoise.generate_schemas()

@app.on_event("shutdown")
async def shutdown_event():
    await Tortoise.close_connections()
```

在服务中通过依赖注入使用仓储。

```python
# examples/fast_api_app/core/services.py

from yai_nexus_agentkit.persistence.repository import TortoiseRepository
from yai_nexus_agentkit.persistence.models import Conversation

class ConversationService:
    def __init__(self, repo: BaseRepository[Conversation]):
        self._repo = repo

    async def get_conversation(self, convo_id: str):
        return await self._repo.get(convo_id)

# 在容器中装配
container.conversation_repository.override(
    TortoiseRepository(model_cls=Conversation)
)
```

## 5. 实施计划

1.  创建 `persistence/db_config.py` 定义数据库配置。
2.  创建 `persistence/models/` 目录及 `conversation.py`, `message.py` 模型文件。
3.  实现 `persistence/repository.py` 中的 `TortoiseRepository`。
4.  实现 `persistence/checkpoint.py` 中的 `PostgresCheckpoint`。
5.  更新 `examples/fast_api_app` 以集成新的持久化层，包括数据库连接的生命周期管理和依赖注入配置。
6.  考虑使用 `aerich` 进行数据库迁移管理，并将其集成到项目中。 