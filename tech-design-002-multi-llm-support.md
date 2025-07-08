
# 技术设计方案: 002-多 LLM 提供商支持

## 1. 背景

`yai-nexus-agentkit` 的核心是与大型语言模型 (LLM) 的交互。当前 `src` 目录中的实现 (`OpenAIClient`) 只针对 OpenAI 进行了硬编码，缺乏灵活性和扩展性。

旧代码库 (`old/lucas_ai_core`) 中通过枚举 (`LLMClientEnum`) 和工具类 (`LLMClientUtils`) 的方式支持了多模型，但这种方式耦合度较高，不易于扩展新的 LLM 提供商，且依赖于一个全局的 Nacos 配置中心，不符合开源项目易于部署的原则。

此方案旨在设计一个全新的、优雅的、面向接口的 LLM 客户端框架，使其具备以下特性：

- **提供商无关**: 核心逻辑不依赖于任何特定的 LLM 提供商。
- **易于扩展**: 添加新的 LLM 提供商（如智谱、通义千问）应简单直观，无需修改核心代码。
- **配置灵活**: 支持从环境变量或配置文件中加载配置，方便用户部署。
- **功能可插拔**: 如日志、追踪 (Langfuse)、缓存等高级功能应作为可插拔的中间件或回调实现。

## 2. 核心设计

我们将采用“工厂模式 + 接口驱动 + 枚举”的设计，并依赖 `yai-nexus-configuration` 进行配置管理。

### 2.1. 核心接口 (`core/llm.py`)

`BaseLLM` 抽象基类定义了统一契约。`model` 参数将接受字符串或枚举，以兼顾灵活性和易用性。

```python
# src/yai_nexus_agentkit/core/llm.py

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Union


class BaseLLM(ABC):
    """语言模型客户端的抽象基类 (ABC)。"""

    @abstractmethod
    async def astream(
        self, prompt: str, model: Optional[Union[str, Enum]] = None, **kwargs: Any
    ) -> AsyncIterator[str]:
        """
        以流式方式向语言模型发送提示并获取回复。

        Args:
            prompt: 发送给语言模型的提示字符串。
            model: (可选) 要使用的具体模型名称或模型枚举。
            **kwargs: 传递给底层客户端的其他参数。

        Yields:
            来自语言模型的回复字符串块。
        """
        raise NotImplementedError

    @abstractmethod
    async def ainvoke(
        self, prompt: str, model: Optional[Union[str, Enum]] = None, **kwargs: Any
    ) -> str:
        """
        向语言模型发送一个提示并一次性获取完整回复。

        Args:
            prompt: 发送给语言模型的提示字符串。
            model: (可选) 要使用的具体模型名称或模型枚举。
            **kwargs: 传递给底层客户端的其他参数。

        Returns:
            来自语言模型的完整回复字符串。
        """
        raise NotImplementedError
```

### 2.2. 提供商与模型定义 (`infrastructure/llm/llm_enums.py`) (新增)

我们将提供商和常用模型定义为枚举，以提高类型安全性和代码可读性。

```python
# src/yai_nexus_agentkit/infrastructure/llm/llm_enums.py

from enum import Enum

class LLMProvider(str, Enum):
    """支持的 LLM 提供商枚举。"""
    OPENAI = "openai"
    ZHIPU = "zhipu"
    # ... 未来可添加更多

class OpenAIModel(str, Enum):
    """OpenAI 常用模型枚举 (作为快捷方式)。"""
    GPT_4O = "gpt-4o"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

# 未来可为其他提供商添加模型枚举，如 ZhipuModel
```

### 2.3. 提供商实现 (`infrastructure/llm/`)

#### 2.3.1. 配置模型

配置模型将使用 `LLMProvider` 枚举来确保提供商标识的正确性。

```python
# src/yai_nexus_agentkit/infrastructure/llm/openai_client.py

from pydantic import BaseModel, Field
from .llm_enums import LLMProvider, OpenAIModel

class OpenAIConfig(BaseModel):
    """OpenAIClient 的配置模型。"""
    provider: LLMProvider = Field(LLMProvider.OPENAI, Literal=True) # 使用枚举
    api_key: str = Field(..., description="OpenAI API 密钥。")
    base_url: str = Field("https://api.openai.com/v1", description="OpenAI API 的基础 URL。")
    default_model: str = Field(OpenAIModel.GPT_4O.value, description="默认使用的模型。")
```

#### 2.3.2. 客户端实现

客户端实现将处理 `Union[str, Enum]` 类型的 `model` 参数。

```python
# src/yai_nexus_agentkit/infrastructure/llm/openai_client.py

from yai_nexus_agentkit.core.llm import BaseLLM
from openai import AsyncOpenAI
from enum import Enum
from typing import Union, Optional

class OpenAIClient(BaseLLM):
    """OpenAI 语言模型的客户端实现。"""
    
    def __init__(self, config: OpenAIConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )

    def _resolve_model_name(self, model: Optional[Union[str, Enum]] = None) -> str:
        """解析出最终要使用的模型名称字符串。"""
        if model is None:
            return self.config.default_model
        
        return model.value if isinstance(model, Enum) else model

    async def astream(self, prompt: str, model: Optional[Union[str, Enum]] = None, **kwargs) -> AsyncIterator[str]:
        model_name = self._resolve_model_name(model)
        # ... 实现流式调用
    
    async def ainvoke(self, prompt: str, model: Optional[Union[str, Enum]] = None, **kwargs) -> str:
        model_name = self._resolve_model_name(model)
        # ... 实现一次性调用
```

### 2.4. LLM 工厂 (`infrastructure/llm/llm_factory.py`)

`LLMFactory` 将使用 `LLMProvider` 枚举来注册和获取客户端。

```python
# src/yai_nexus_agentkit/infrastructure/llm/llm_factory.py

from typing import Dict, Type, List, Any
from pydantic import BaseModel
from yai_nexus_agentkit.core.llm import BaseLLM
from .llm_enums import LLMProvider
from .openai_client import OpenAIClient, OpenAIConfig
# from .zhipu_client import ZhipuClient, ZhipuConfig # 示例：未来可添加

class LLMFactory:
    def __init__(self, configs: List[Dict[str, Any]]):
        self._clients: Dict[str, BaseLLM] = {}
        self._provider_map: Dict[LLMProvider, Type[BaseLLM]] = {
            LLMProvider.OPENAI: OpenAIClient,
            # LLMProvider.ZHIPU: ZhipuClient, # 示例
        }
        self._config_map: Dict[LLMProvider, Type[BaseModel]] = {
            LLMProvider.OPENAI: OpenAIConfig,
            # LLMProvider.ZHIPU: ZhipuConfig, # 示例
        }

        for config_dict in configs:
            provider_str = config_dict.get("provider")
            if not provider_str:
                raise ValueError("LLM 配置必须包含 'provider' 字段。")
            
            provider = LLMProvider(provider_str) # 转换为枚举
            config_cls = self._config_map[provider]
            client_cls = self._provider_map[provider]
            
            config = config_cls(**config_dict)
            self._clients[provider.value] = client_cls(config)

    def get_client(self, provider: LLMProvider = LLMProvider.OPENAI) -> BaseLLM:
        """
        获取指定提供商的 LLM 客户端。
        
        Args:
            provider: 提供商枚举 (例如, LLMProvider.OPENAI)。
        
        Returns:
            对应的 LLM 客户端实例。
        """
        client = self._clients.get(provider.value)
        if not client:
            raise ValueError(f"未找到或未配置提供商 '{provider.value}' 的客户端。")
        return client

```

### 2.5. 高级功能：Langfuse 回调

为了集成 Langfuse，我们将设计一个可插拔的回调机制，而不是在客户端实现中硬编码。

```python
# src/yai_nexus_agentkit/callbacks/langfuse_handler.py

from yai_nexus_agentkit.core.callbacks import BaseCallbackHandler

class LangfuseCallbackHandler(BaseCallbackHandler):
    def __init__(self, **kwargs):
        # 初始化 langfuse.CallbackHandler
        pass

    async def on_llm_start(self, **kwargs):
        # ...
    
    async def on_llm_end(self, **kwargs):
        # ...
```

`BaseLLM` 接口和 `LLMFactory` 将增加对回调的支持，允许在调用时注入回调处理器。

## 3. 目录结构

```
src/yai_nexus_agentkit/
├── core/
│   ├── llm.py              # BaseLLM 接口
│   └── callbacks.py        # 回调处理器基类 (新增)
└── infrastructure/
    └── llm/
        ├── __init__.py
        ├── llm_enums.py        # LLM 枚举 (新增)
        ├── openai_client.py    # OpenAI 实现和配置
        ├── zhipu_client.py     # 智谱AI 实现和配置 (示例)
        └── llm_factory.py      # LLM 工厂
```

## 4. 使用示例

在应用的依赖注入容器中，可以这样初始化和使用 `LLMFactory`。这里我们使用 `yai-nexus-configuration` 来加载配置。

假设 `pyproject.toml` 或环境变量中有如下配置:

```toml
# pyproject.toml
[tool.yai_nexus_configuration.llms]
# 第一个 LLM 配置
0.provider = "openai"
0.api_key = "${OPENAI_API_KEY}" # 从环境变量加载
0.default_model = "gpt-4o"

# 第二个 LLM 配置 (示例)
# 1.provider = "zhipu"
# 1.api_key = "${ZHIPU_API_KEY}"
```

```python
# In dependency injection container (e.g., examples/fast_api_app/core/services.py)

from yai_nexus_agentkit.infrastructure.llm.llm_factory import LLMFactory
from yai_nexus_agentkit.infrastructure.llm.llm_enums import LLMProvider, OpenAIModel
from yai_nexus_configuration import config # 导入配置对象

# 1. 使用 yai-nexus-configuration 从配置源加载LLM配置
# config.llms 会自动解析为一个配置列表
llm_configs = config.get("llms", [])

# 2. 创建工厂实例
llm_factory = LLMFactory(configs=llm_configs)

# 3. 在需要的地方注入和使用
class ChatService:
    def __init__(self, llm_factory: LLMFactory):
        # 使用枚举获取客户端，更安全
        self.llm_client = llm_factory.get_client(LLMProvider.OPENAI)

    async def chat(self, prompt: str):
        # 使用默认模型
        response = await self.llm_client.ainvoke(prompt)
        
        # 使用模型枚举，方便且安全
        response_stream = self.llm_client.astream(prompt, model=OpenAIModel.GPT_3_5_TURBO)
        
        # 也可以使用字符串，支持自定义或新模型
        response_stream_custom = self.llm_client.astream(prompt, model="a-custom-model-name")
        
        return response_stream
```

## 5. 实施计划

1.  创建 `src/yai_nexus_agentkit/infrastructure/llm/llm_enums.py` 文件，定义 `LLMProvider` 和 `OpenAIModel` 枚举。
2.  更新 `src/yai_nexus_agentkit/core/llm.py` 中的 `BaseLLM` 接口，使其 `model` 参数接受 `Union[str, Enum]`。
3.  创建 `src/yai_nexus_agentkit/infrastructure/llm/openai_client.py`，包含 `OpenAIConfig` 和 `OpenAIClient` 实现，并处理模型名称解析。
4.  创建 `src/yai_nexus_agentkit/infrastructure/llm/llm_factory.py`，实现使用枚举的 `LLMFactory`。
5.  (可选) 创建 `src/yai_nexus_agentkit/core/callbacks.py` 和 `callbacks/langfuse_handler.py` 来支持可插拔的追踪。
6.  更新 `examples/fast_api_app` 以演示如何通过 `yai-nexus-configuration` 配置和使用新的 LLM 框架。 