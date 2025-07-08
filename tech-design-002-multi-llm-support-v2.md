# 技术设计方案: 002-多 LLM 提供商支持 (基于 LangChain 的设计)

## 1. 背景

`yai-nexus-agentkit` 的核心是与大型语言模型 (LLM) 的交互。原设计文档提出了从零开始构建 LLM 抽象层的方案，但经过深入分析，我们认为基于 LangChain 生态系统的封装方案更加合理。

**为什么选择基于 LangChain 的设计？**

1. **避免重复造轮子**：LangChain 已经提供了成熟的多 LLM 提供商支持
2. **功能丰富**：自动获得流式处理、异步支持、回调机制等功能
3. **生态兼容**：与 LangChain 生态系统无缝集成
4. **持续更新**：LangChain 社区持续维护和更新各种 LLM 集成

## 2. 核心设计

我们将采用"基于 LangChain 的封装 + 工厂模式 + 配置驱动"的设计，并依赖 `yai-nexus-configuration` 进行配置管理。

**设计理念：**
- **复用 LangChain 生态**：底层使用 LangChain 的各种 ChatModel 实现
- **统一工厂接口**：通过配置驱动的工厂函数创建 LLM 实例
- **可选业务抽象**：在需要时提供更高层次的业务抽象
- **类型安全**：使用枚举和 Pydantic 模型确保类型安全

### 2.1. 核心工厂函数 (`llm/factory.py`)

当前实现已经采用了正确的方向，核心是 `create_llm()` 工厂函数：

```python
# src/yai_nexus_agentkit/llm/factory.py

from typing import Any, Dict
from langchain_core.language_models import BaseChatModel
from .providers import LLMProvider

def create_llm(config: Dict[str, Any]) -> BaseChatModel:
    """
    根据配置创建 LangChain 兼容的 LLM 客户端。
    
    这个函数是我们的核心工厂，它会根据 provider 字段
    动态导入并创建相应的 LangChain ChatModel 实例。
    
    优势：
    - 直接复用 LangChain 的成熟实现
    - 自动获得 LangChain 的所有功能（流式、异步、回调等）
    - 减少重复代码，专注于业务逻辑
    
    Args:
        config: 包含 provider 和其他配置的字典
        
    Returns:
        BaseChatModel: LangChain 兼容的 LLM 客户端
    """
    # 当前实现已经很好地处理了多提供商支持
    pass
```

### 2.2. 提供商枚举 (`llm/providers.py`)

```python
# src/yai_nexus_agentkit/llm/providers.py

from enum import Enum

class LLMProvider(str, Enum):
    """支持的 LLM 提供商枚举。"""
    
    OPENAI = "openai"
    ZHIPU = "zhipu"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    TONGYI = "tongyi"
    
    # 未来可以轻松添加更多提供商
    # AZURE_OPENAI = "azure_openai"
    # BEDROCK = "bedrock"
    # VERTEX_AI = "vertex_ai"
```

### 2.3. 模型枚举 (`llm/models.py`) - 可选增强

为了提供类型安全的模型选择，我们可以定义常用模型的枚举：

```python
# src/yai_nexus_agentkit/llm/models.py

from enum import Enum

class OpenAIModel(str, Enum):
    """OpenAI 常用模型枚举。"""
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

class AnthropicModel(str, Enum):
    """Anthropic 常用模型枚举。"""
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

class ZhipuModel(str, Enum):
    """智谱 AI 常用模型枚举。"""
    GLM_4 = "glm-4"
    GLM_4_TURBO = "glm-4-turbo"
    GLM_3_TURBO = "glm-3-turbo"

class TongyiModel(str, Enum):
    """通义千问常用模型枚举。"""
    QWEN_PLUS = "qwen-plus"
    QWEN_TURBO = "qwen-turbo"
    QWEN_MAX = "qwen-max"

class OpenRouterModel(str, Enum):
    """
    OpenRouter 常用模型枚举。
    
    OpenRouter 是一个聚合平台，支持多家提供商的模型。
    模型名称格式通常为 "provider/model-name"。
    """
    # OpenAI 模型 (通过 OpenRouter)
    OPENAI_GPT_4O = "openai/gpt-4o"
    OPENAI_GPT_4O_MINI = "openai/gpt-4o-mini"
    OPENAI_GPT_4_TURBO = "openai/gpt-4-turbo"
    
    # Anthropic 模型 (通过 OpenRouter)
    ANTHROPIC_CLAUDE_3_5_SONNET = "anthropic/claude-3.5-sonnet"
    ANTHROPIC_CLAUDE_3_OPUS = "anthropic/claude-3-opus"
    ANTHROPIC_CLAUDE_3_HAIKU = "anthropic/claude-3-haiku"
    
    # Google 模型 (通过 OpenRouter)
    GOOGLE_GEMINI_PRO = "google/gemini-pro"
    GOOGLE_GEMINI_PRO_1_5 = "google/gemini-pro-1.5"
    
    # Meta 模型 (通过 OpenRouter)
    META_LLAMA_3_1_70B = "meta-llama/llama-3.1-70b-instruct"
    META_LLAMA_3_1_8B = "meta-llama/llama-3.1-8b-instruct"
    
    # Mistral 模型 (通过 OpenRouter)
    MISTRAL_LARGE = "mistralai/mistral-large"
    MISTRAL_MEDIUM = "mistralai/mistral-medium"
    
    # 其他热门模型
    PERPLEXITY_LLAMA_3_1_SONAR_LARGE = "perplexity/llama-3.1-sonar-large-128k-online"
    DEEPSEEK_CODER = "deepseek/deepseek-coder"

# 统一的模型枚举映射
MODEL_MAPPING = {
    "openai": OpenAIModel,
    "anthropic": AnthropicModel,
    "zhipu": ZhipuModel,
    "tongyi": TongyiModel,
    "openrouter": OpenRouterModel,
}

def get_model_enum(provider: str):
    """
    根据提供商获取对应的模型枚举类。
    
    Args:
        provider: 提供商名称
        
    Returns:
        对应的模型枚举类，如果不存在则返回 None
    """
    return MODEL_MAPPING.get(provider.lower())
```

**OpenRouter 特殊处理说明：**

1. **模型名称格式**：OpenRouter 的模型名称通常为 `"provider/model-name"` 格式
2. **聚合特性**：OpenRouter 聚合了多家提供商的模型，所以枚举中包含了各种提供商的模型
3. **动态更新**：OpenRouter 经常添加新模型，建议定期更新枚举或支持字符串形式的模型名称

### 2.4. 配置模型 (`llm/config.py`)

```python
# src/yai_nexus_agentkit/llm/config.py

from pydantic import BaseModel, Field
from .providers import LLMProvider

class LLMConfig(BaseModel):
    """LLM 配置的基础模型。"""
    
    provider: LLMProvider = Field(..., description="LLM 提供商的名称。")
    model: str = Field(..., description="要使用的具体模型名称。")
    
    class Config:
        extra = "allow"  # 允许提供商特定的配置字段
```

### 2.5. 业务抽象层 (`core/llm.py`) - 可选增强

如果需要更高层次的业务抽象，可以在 LangChain 基础上添加封装：

```python
# src/yai_nexus_agentkit/core/llm.py

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

class BusinessLLM:
    """
    业务层 LLM 封装类。
    
    这是一个可选的封装层，在 LangChain 基础上提供
    更符合业务需求的接口。
    """

    def __init__(self, langchain_client: BaseChatModel):
        """
        初始化时接收一个 LangChain 的 BaseChatModel 实例。
        
        Args:
            langchain_client: 由 create_llm() 创建的 LangChain 客户端
        """
        self.client = langchain_client

    async def chat(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """
        简化的聊天接口。
        
        Args:
            prompt: 用户提示
            system_prompt: 可选的系统提示词
            **kwargs: 其他参数
            
        Returns:
            LLM 的回复
        """
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        response = await self.client.ainvoke(messages, **kwargs)
        return response.content

    async def stream_chat(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """
        流式聊天接口。
        
        Args:
            prompt: 用户提示
            system_prompt: 可选的系统提示词
            **kwargs: 其他参数
            
        Yields:
            LLM 的回复片段
        """
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        async for chunk in self.client.astream(messages, **kwargs):
            yield chunk.content
```

### 2.6. 增强的工厂类 (`llm/factory.py`) - 可选

如果需要管理多个 LLM 实例，可以添加一个工厂类：

```python
# src/yai_nexus_agentkit/llm/factory.py

from typing import Dict, List, Any, Optional
from langchain_core.language_models import BaseChatModel
from .providers import LLMProvider
from .config import LLMConfig

class LLMFactory:
    """
    LLM 工厂类，管理多个 LLM 实例。
    
    这是一个可选的增强，适合需要同时使用多个 LLM 的场景。
    """
    
    def __init__(self, configs: List[Dict[str, Any]]):
        """
        初始化工厂，从配置列表创建多个 LLM 实例。
        
        Args:
            configs: LLM 配置列表
        """
        self._clients: Dict[str, BaseChatModel] = {}
        
        for config_dict in configs:
            # 验证配置
            config = LLMConfig(**config_dict)
            
            # 创建 LLM 实例
            client = create_llm(config_dict)
            
            # 使用 provider 作为键存储
            self._clients[config.provider.value] = client
    
    def get_client(self, provider: LLMProvider) -> BaseChatModel:
        """
        获取指定提供商的 LLM 客户端。
        
        Args:
            provider: 提供商枚举
            
        Returns:
            对应的 LLM 客户端
        """
        client = self._clients.get(provider.value)
        if not client:
            raise ValueError(f"未找到提供商 '{provider.value}' 的客户端")
        return client
    
    def list_providers(self) -> List[str]:
        """返回所有可用的提供商列表。"""
        return list(self._clients.keys())
```

## 3. 目录结构

```
src/yai_nexus_agentkit/
├── llm/                    # LLM 相关模块 (当前实现)
│   ├── __init__.py         # 公共接口
│   ├── factory.py          # 核心工厂函数
│   ├── providers.py        # 提供商枚举
│   ├── config.py           # 配置模型
│   └── models.py           # 模型枚举 (可选)
├── core/                   # 核心抽象 (可选)
│   └── llm.py              # 业务抽象层
└── callbacks/              # 回调系统 (可选)
    └── langfuse_handler.py # Langfuse 集成
```

## 4. 使用示例

### 4.1. 基础使用 (直接使用 LangChain)

```python
from yai_nexus_agentkit.llm import create_llm

# 创建 OpenAI 客户端
config = {
    "provider": "openai",
    "model": "gpt-4o",
    "api_key": "sk-...",
    "base_url": "https://api.openai.com/v1"
}

llm = create_llm(config)

# 直接使用 LangChain 接口
from langchain_core.messages import HumanMessage

response = await llm.ainvoke([HumanMessage(content="Hello, world!")])
print(response.content)
```

### 4.2. 使用工厂类管理多个 LLM

```python
from yai_nexus_agentkit.llm.factory import LLMFactory
from yai_nexus_agentkit.llm.providers import LLMProvider

# 配置多个 LLM
configs = [
    {"provider": "openai", "model": "gpt-4o", "api_key": "sk-..."},
    {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "api_key": "sk-ant-..."},
    {"provider": "openrouter", "model": "google/gemini-pro", "api_key": "sk-or-...", "base_url": "https://openrouter.ai/api/v1"},
]

factory = LLMFactory(configs)

# 获取不同的 LLM 客户端
openai_client = factory.get_client(LLMProvider.OPENAI)
anthropic_client = factory.get_client(LLMProvider.ANTHROPIC)
openrouter_client = factory.get_client(LLMProvider.OPENROUTER)
```

### 4.3. 使用模型枚举 (类型安全)

```python
from yai_nexus_agentkit.llm import create_llm
from yai_nexus_agentkit.llm.models import OpenAIModel, OpenRouterModel
from langchain_core.messages import HumanMessage

# 使用 OpenAI 模型枚举
config = {
    "provider": "openai",
    "model": OpenAIModel.GPT_4O.value,  # 类型安全的模型选择
    "api_key": "sk-..."
}
llm = create_llm(config)

# 使用 OpenRouter 模型枚举
openrouter_config = {
    "provider": "openrouter", 
    "model": OpenRouterModel.ANTHROPIC_CLAUDE_3_5_SONNET.value,  # "anthropic/claude-3.5-sonnet"
    "api_key": "sk-or-...",
    "base_url": "https://openrouter.ai/api/v1"
}
openrouter_llm = create_llm(openrouter_config)

# 使用 OpenRouter 访问 Google 模型
gemini_config = {
    "provider": "openrouter",
    "model": OpenRouterModel.GOOGLE_GEMINI_PRO.value,  # "google/gemini-pro"
    "api_key": "sk-or-...",
    "base_url": "https://openrouter.ai/api/v1"
}
gemini_llm = create_llm(gemini_config)

# 调用示例
response = await gemini_llm.ainvoke([HumanMessage(content="Hello from Gemini!")])
```

### 4.4. 使用业务抽象层

```python
from yai_nexus_agentkit.core.llm import BusinessLLM
from yai_nexus_agentkit.llm import create_llm

# 创建基础 LLM
llm = create_llm({"provider": "openai", "model": "gpt-4o", "api_key": "sk-..."})

# 包装为业务 LLM
business_llm = BusinessLLM(llm)

# 使用简化的业务接口
response = await business_llm.chat(
    prompt="解释一下量子计算",
    system_prompt="你是一个专业的科学解释员"
)
```

## 5. 实施计划

### 阶段 1: 完善当前实现 (已基本完成)
- ✅ `create_llm()` 工厂函数
- ✅ `LLMProvider` 枚举
- ✅ `LLMConfig` 配置模型
- ✅ 多提供商支持

### 阶段 2: 可选增强 (按需实现)
- [ ] 模型枚举 (`OpenAIModel`, `AnthropicModel` 等)
- [ ] 工厂类 (`LLMFactory`)
- [ ] 业务抽象层 (`BusinessLLM`)

### 阶段 3: 高级功能 (长期规划)
- [ ] 回调系统集成
- [ ] 缓存机制
- [ ] 监控和日志

## 6. 优势总结

**基于 LangChain 的设计优势：**

1. **快速开发**：无需重新实现各种 LLM 集成
2. **功能丰富**：自动获得流式、异步、回调等功能
3. **生态兼容**：与 LangChain 生态系统无缝集成
4. **持续更新**：跟随 LangChain 社区的持续更新
5. **降低维护成本**：减少重复代码，专注于业务价值

**当前实现的优势：**
- 已经采用了正确的技术方向
- 代码结构清晰，易于扩展
- 配置驱动，使用灵活
- 类型安全，开发体验良好

这个设计充分利用了 LangChain 的成熟生态，同时保持了代码的简洁性和可扩展性。