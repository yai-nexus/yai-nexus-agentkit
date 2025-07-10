# YAI Nexus AgentKit

> **一个以 FastAPI 为核心、支持 AG-UI 协议的 AI 代理工具包，专为构建现代流式 AI 应用而设计。**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-first-green.svg)](https://fastapi.tiangolo.com/)
[![AG-UI](https://img.shields.io/badge/AG--UI-高保真实现-orange.svg)](https://github.com/ag-ui/protocol)

---

## 🚀 快速开始

```bash
# 安装工具包
pip install yai-nexus-agentkit

# 运行示例应用
python -m examples.fast_api_app.main
```

现在，在浏览器中打开 `http://localhost:8000/docs`，即可探索交互式的 API 文档。

---

## 🎯 项目特色

**YAI Nexus AgentKit** 专为希望使用 **FastAPI** 构建**现代流式 AI 应用**的开发者而设计。与其他通用型 AI 框架不同，我们提供：

-   **🔥 FastAPI 优先**：专为 Web 应用场景从零开始设计，与 FastAPI 无缝集成。
-   **📡 默认即流式**：默认使用 SSE (Server-Sent Events) 提供真正的实时 AI 交互体验。
-   **🎨 高保真 AG-UI 协议**：我们对 [AG-UI 协议](https://github.com/ag-ui/protocol) 提供了高保真实现，能够完整、准确地将 Agent 的内部活动（包括工具调用细节）映射到标准事件，实现完全透明、可观察、可调试的前端交互界面。
-   **🔧 三层渐进式 API**：提供从简单到高级的三种 API 模式，满足不同复杂度的需求。
-   **📊 支持多种 LLM**：无缝切换 OpenAI, Anthropic, ZhipuAI, Tongyi, OpenRouter 等主流供应商。
-   **🏗️ 生产就绪**：基于 LangChain 和 LangGraph 的坚实基础构建，稳定可靠。

---

## 🏛️ 架构概览

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 UI 应用    │◄──►│ AG-UI 标准事件流 │◄──►│ YAI AgentKit    │
│ (React/Vue/...) │    │   (SSE)         │    │ (AGUIAdapter)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   LangGraph     │◄──►│   FastAPI 应用  │
                       │ (业务流程编排)  │    │   (Web 服务层)  │
                       └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   多LLM后端     │
                       │ (OpenAI, 等)    │
                       └─────────────────┘
```

---

## 🎨 三种复杂度的 API

### 第一层：简单模式
适合快速上手——以最少的设置直接调用 LLM。

```python
from yai_nexus_agentkit import create_llm

# 创建 LLM 客户端
llm = create_llm({
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "sk-..."
})

# 简单问答
response = llm.invoke("你好，世界！")
print(response.content)
```

### 第二层：流式模式
通过 SSE 增加实时流式响应。

```python
from yai_nexus_agentkit.adapter import BasicSSEAdapter
from sse_starlette.sse import EventSourceResponse

# 创建基础的 SSE 适配器
adapter = BasicSSEAdapter(llm)

# FastAPI 端点
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return EventSourceResponse(
        adapter.stream_response(request.message),
        media_type="text/event-stream"
    )
```

### 第三层：高级模式
使用 `AGUIAdapter`，提供完整的 AG-UI 协议支持和 LangGraph 流程编排，是构建复杂 Agent 的理想选择。

```python
from yai_nexus_agentkit.adapter import AGUIAdapter
from yai_nexus_agentkit.adapter.sse_advanced import Task

# 使用你的 LangGraph Agent 创建高级适配器
# Agent 的内部思考、工具调用等过程将被自动转换为 AG-UI 事件
adapter = AGUIAdapter(your_langgraph_agent)

# 创建兼容 AG-UI 的 FastAPI 端点
@app.post("/chat/agent")
async def chat_advanced(task: Task):
    # Task 模型支持 thread_id，用于实现多轮对话
    # task = Task(id="run-123", query="搜索一下今天的天气", thread_id="thread-abc")
    return EventSourceResponse(
        adapter.event_stream_adapter(task),
        ping=15,
        media_type="text/event-stream"
    )
```

---

## 🔧 安装与配置

### 基础安装
```bash
pip install yai-nexus-agentkit
```

### 带可选依赖项的安装
```bash
# 安装特定的 LLM 供应商支持
pip install yai-nexus-agentkit[openai,anthropic]

# 安装持久化支持
pip install yai-nexus-agentkit[persistence]

# 安装开发所需全部依赖
pip install yai-nexus-agentkit[dev]
```

### 环境配置
在项目根目录创建 `.env` 文件：
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
# ... 其他供应商的 API Key
```

---

## 🏗️ 项目结构

```
yai-nexus-agentkit/
├── src/yai_nexus_agentkit/
│   ├── llm/                 # 多LLM支持层
│   │   ├── factory.py       # LLM 创建工厂
│   │   └── ...
│   ├── adapter/             # 适配器层 (协议转换)
│   │   ├── sse_basic.py     # 基础 SSE 适配器
│   │   ├── sse_advanced.py  # 高级 AG-UI 适配器
│   │   ├── langgraph_events.py # LangGraph 事件枚举
│   │   └── errors.py        # 自定义异常
│   ├── core/                # 核心抽象与业务事件
│   │   └── events.py        # EventEmitter 定义
│   └── persistence/         # 可选的持久化层
├── examples/
│   └── fast_api_app/        # 一个完整的 FastAPI 示例应用
├── tests/
│   ├── unit/                # 单元测试
│   └── integration/         # 集成测试
└── pyproject.toml           # 项目配置文件
```

---

## 🤝 贡献代码

我们非常欢迎社区贡献！请参考我们的 [贡献指南](CONTRIBUTING.md)。

### 开发环境设置
```bash
# 克隆仓库
git clone https://github.com/yai-nexus/yai-nexus-agentkit.git
cd yai-nexus-agentkit

# 以可编辑模式安装，并包含开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化与检查
black .
ruff check .
```

---

## 📄 许可证

本项目基于 MIT 许可证开源 - 详情请见 [LICENSE](LICENSE) 文件。

---

<div align="center">
  <p>由 YAI Nexus 团队 ❤️ 倾情打造</p>
</div>