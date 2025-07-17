# YAI Nexus AgentKit

YAI Nexus AgentKit 是一个功能强大、可扩展的 Python 工具包，旨在简化和加速具有复杂工作流和多语言模型（LLM）支持的 AI Agent 的构建过程。

## 🌟 核心特性

- **多 LLM 支持**: 无缝集成多家主流 LLM 提供商，包括 OpenAI, Anthropic, ZhipuAI, Tongyi, OpenRouter 等。
- **配置驱动**: 通过简单的 Python 字典或 JSON 文件即可轻松初始化和切换 LLM，无需修改代码。
- **可扩展分层架构**:
  - **编排层 (`orchestration`)**: 与 [LangGraph](https://python.langchain.com/docs/langgraph/) 等现代 AI 工作流引擎深度集成。
  - **适配器层 (`adapter`)**: 将后端事件（如 LangGraph 的事件流）转换为标准化的前端协议（如 AG-UI），解耦前后端逻辑。
  - **持久化层 (`persistence`)**: 提供开箱即用的检查点（Checkpoint）和会话历史记录功能，支持多种数据库后端。
- **类型安全**: 大量使用类型提示，提供卓越的开发体验和代码健壮性。
- **生产就绪**: 内置日志、错误处理和可配置的工厂模式，专为生产环境设计。

## 💿 安装

根据您的需求，选择合适的安装方式：

1.  **基础安装** (仅包含核心库):
    ```bash
    pip install yai-nexus-agentkit
    ```

2.  **安装特定依赖**:
    如果您需要使用特定的 LLM 提供商，可以按需安装：
    ```bash
    # 安装 OpenAI 依赖
    pip install "yai-nexus-agentkit[openai]"
    
    # 同时安装 OpenAI 和 Anthropic 依赖
    pip install "yai-nexus-agentkit[openai,anthropic]"
    ```

3.  **完整安装** (用于开发):
    克隆仓库后，在 `packages/agentkit` 目录下运行：
    ```bash
    pip install -e ".[all]"
    ```

## 🚀 快速上手

以下示例展示了如何通过配置创建一个 `gpt-4o` 客户端并进行调用：

```python
from yai_nexus_agentkit.llm import create_llm, OpenAIModel
import os

# 建议从环境变量加载 API Key
# os.environ["OPENAI_API_KEY"] = "sk-..." 

# 1. 定义配置
config = {
    "provider": "openai",
    "model": OpenAIModel.GPT_4O.value,
    "api_key": os.getenv("OPENAI_API_KEY"),
}

# 2. 使用工厂函数创建 LLM 实例
llm = create_llm(config)

# 3. 同步调用
response = llm.invoke("你好，世界！")
print(response)

# 4. 异步调用
async def main():
    response_async = await llm.ainvoke("Hello, async world!")
    print(response_async)

# asyncio.run(main())
```

## 深入使用

### 使用 LangGraph 和 AG-UI 适配器

AgentKit 的核心优势在于将 LangGraph 的复杂事件流与前端解耦。`AGUIAdapter` 会将 LangGraph 的事件转换为 AG-UI 协议，前端只需处理标准化的 UI 事件即可。

```python
from yai_nexus_agentkit.adapter.agui_adapter import AGUIAdapter
# 假设 'graph' 是一个已构建的 langgraph.Graph 实例

# 1. 创建适配器实例
adapter = AGUIAdapter(graph=graph)

# 2. 在 API (如 FastAPI) 中处理事件流
async def stream_events(request_data):
    # astream_events 会产生符合 AG-UI 协议的事件
    async for event in adapter.astream_events(
        input_data, # 发送给 graph 的输入
        config={"configurable": {"thread_id": "some_thread_id"}}
    ):
        yield f"data: {event.model_dump_json()}\n\n"
```

### 持久化

AgentKit 提供了一个简单的 API 来管理会话的检查点 (Checkpoint)。

```python
from yai_nexus_agentkit.persistence.checkpoint import CheckpointRepository

# 初始化仓库 (通常在应用启动时)
repo = CheckpointRepository()

# 获取检查点
checkpoint = repo.get_checkpoint("some_thread_id")

# 更新检查点
# checkpoint_data 是从 langgraph.get_state() 获取的状态
repo.update_checkpoint("some_thread_id", checkpoint_data)
```

## 🧪 运行测试

在 `packages/agentkit` 目录下运行测试套件：

```bash
pytest
```

要同时生成覆盖率报告：
```bash
pytest --cov=src
```

## 🤝 贡献

我们欢迎任何形式的社区贡献！请在提交 Pull Request 前，确保代码通过了 `black` 和 `ruff` 的检查，并且所有测试都能通过。