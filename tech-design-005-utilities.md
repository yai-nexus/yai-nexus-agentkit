
# 技术设计方案: 005-通用工具与组件

## 1. 背景

一个高质量的软件框架，除了核心功能外，还需要一套稳定、易用的通用工具（Utilities）来处理横切关注点，如配置管理、唯一ID生成、外部工具调用等。

旧代码库 (`old/lucas_ai_core/`) 中包含了这些功能的零散实现，例如：
- `config/`: 强依赖于 Nacos 的配置中心。
- `infrastructure/snow_flake.py`: 一个独立的雪花算法实现。
- `infrastructure/mcp_client.py`: 一个抽象但未具体实现的“模型控制平面”客户端。

此方案旨在将这些分散的功能进行整合、重构和现代化，形成一套内聚的、符合开源项目最佳实践的通用工具集。

设计目标：
- **统一配置**: 提供一个基于 `.env` 文件和 Pydantic 模型的、零依赖的配置加载方案。
- **标准化工具**: 设计清晰、独立的接口和实现，如 `IdGenerator` 和 `ToolExecutor`。
- **模块化管理**: 将所有通用工具统一放置在 `src/yai_nexus_agentkit/utilities/` 目录下，方便维护和复用。

## 2. 核心设计

### 2.1. 配置加载器 (`utilities/config_loader.py`)

这是使项目易于部署的关键。我们将创建一个简单的加载器，它能读取 `.env` 文件，并将其内容解析到指定的 Pydantic 模型中。

```python
# src/yai_nexus_agentkit/utilities/config_loader.py

import os
from typing import Type, TypeVar
from pydantic import BaseModel
from pydantic_settings import BaseSettings

T = TypeVar("T", bound=BaseModel)

class Settings(BaseSettings):
    """
    使用 pydantic-settings 自动从环境变量和 .env 文件加载配置。
    """
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" # 忽略 .env 中多余的字段

def load_config(config_model: Type[T]) -> T:
    """
    加载配置到指定的 Pydantic 模型。

    它会按以下优先级顺序查找配置值：
    1. 环境变量
    2. .env 文件中的值
    3. Pydantic 模型中定义的默认值

    Args:
        config_model: 要加载配置的 Pydantic 模型类。

    Returns:
        一个填充了配置的 Pydantic 模型实例。
    """
    # pydantic-settings 会自动完成所有加载工作
    return config_model()

```

**使用示例:**
```python
# examples/fast_api_app/configs.py
from pydantic import BaseModel
from yai_nexus_agentkit.utilities.config_loader import load_config
from yai_nexus_agentkit.persistence.db_config import DatabaseConfig

class AppConfig(BaseModel):
    """应用总配置"""
    db: DatabaseConfig
    # llm: LLMFactoryConfig 等

# 在应用启动时加载
app_config = load_config(AppConfig)
db_url = app_config.db.db_url
```

### 2.2. 唯一ID生成器 (`utilities/id_generator.py`)

我们将旧的雪花算法实现封装到一个更通用的接口后面，使其未来可以被其他ID生成策略（如KSUID）替换。

```python
# src/yai_nexus_agentkit/core/id_generator.py (接口)
from abc import ABC, abstractmethod

class IdGenerator(ABC):
    @abstractmethod
    def generate(self) -> str:
        raise NotImplementedError

# src/yai_nexus_agentkit/utilities/id_generator.py (实现)
import time
from yai_nexus_agentkit.core.id_generator import IdGenerator

class SnowflakeGenerator(IdGenerator):
    """
    雪花算法ID生成器。
    (此处省略与 old/ 中类似的具体实现代码...)
    """
    def __init__(self, worker_id: int = 1, datacenter_id: int = 1):
        # ... 初始化
        pass

    def generate(self) -> str:
        # ... 生成ID的逻辑
        return "generated_id"
```

### 2.3. 工具执行器 (`utilities/tool_executor.py`)

这是 Agent 与外部世界交互的桥梁，取代了旧的 `MCPClient`。我们将基于 Python 的 `Callable` 和 `inspect` 模块来动态地将普通函数转换为 Agent 可调用的工具。

```python
# src/yai_nexus_agentkit/core/tool.py (接口)
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, Dict, List, Callable

class BaseTool(ABC):
    """工具的抽象基类"""
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    async def ainvoke(self, **kwargs: Any) -> Any:
        """异步执行工具"""
        raise NotImplementedError

# src/yai_nexus_agentkit/utilities/tool_executor.py (实现)
from typing import List, Dict, Any, Callable
from pydantic import create_model
import inspect

class ToolExecutor:
    """工具执行器，管理和调用一组工具"""
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, func: Callable):
        """
        将一个普通函数注册为 Agent 可用工具。
        自动根据函数签名和文档字符串生成工具的 schema。
        """
        name = func.__name__
        description = inspect.getdoc(func) or "No description."
        
        # 根据签名创建 Pydantic 模型作为参数 schema
        sig = inspect.signature(func)
        fields = {
            param.name: (param.annotation, ...)
            for param in sig.parameters.values()
        }
        args_schema = create_model(f"{name}Args", **fields)

        self._tools[name] = func
        self._tool_schemas[name] = {
            "name": name,
            "description": description,
            "parameters": args_schema.model_json_schema()
        }

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return list(self._tool_schemas.values())

    async def execute(self, tool_name: str, **kwargs: Any) -> Any:
        if tool_name not in self._tools:
            raise ValueError(f"工具 '{tool_name}' 未注册。")
        
        func = self._tools[tool_name]
        if inspect.iscoroutinefunction(func):
            return await func(**kwargs)
        else:
            return func(**kwargs)
```
**使用示例:**
```python
# 定义一个工具函数
async def get_current_weather(city: str) -> str:
    """获取指定城市的当前天气。"""
    # ... API调用
    return f"{city}现在是晴天。"

# 注册和执行
tool_executor = ToolExecutor()
tool_executor.register_tool(get_current_weather)

# Agent 可以获取 schema 来决定如何调用
schemas = tool_executor.get_tool_schemas()
# [{'name': 'get_current_weather', 'description': '...', 'parameters': ...}]

# Agent 执行工具
result = await tool_executor.execute("get_current_weather", city="北京")
```

## 3. 目录结构

```
src/yai_nexus_agentkit/
├── core/
│   ├── id_generator.py     # IdGenerator 接口 (新增)
│   └── tool.py             # BaseTool 接口 (新增)
└── utilities/
    ├── __init__.py
    ├── config_loader.py    # 配置加载器
    ├── id_generator.py     # SnowflakeGenerator 实现
    └── tool_executor.py    # 工具注册与执行器
```

## 4. 实施计划

1.  在 `src/yai_nexus_agentkit/utilities/` 目录下创建 `config_loader.py`。
2.  创建 `core/id_generator.py` 和 `utilities/id_generator.py`，并将旧的雪花算法代码迁移和封装进去。
3.  创建 `core/tool.py` 和 `utilities/tool_executor.py`，实现一个灵活的工具注册和调用机制。
4.  在 `examples/fast_api_app` 中全面应用新的 `config_loader` 来管理所有配置。
5.  编写示例来演示如何定义一个函数，将其注册为工具，并被 Agent 调用。 