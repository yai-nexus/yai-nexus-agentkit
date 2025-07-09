# YAI Nexus AgentKit

> **一个 FastAPI 优先、支持 AG-UI 协议的 AI 代理工具包，用于构建现代流式 AI 应用。**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-first-green.svg)](https://fastapi.tiangolo.com/)
[![AG-UI](https://img.shields.io/badge/AG--UI-protocol-orange.svg)](https://github.com/ag-ui/protocol)

## 🚀 快速开始

```bash
# 安装工具包
pip install yai-nexus-agentkit

# 运行示例应用
python -m examples.fast_api_app.main
```

打开浏览器访问 `http://localhost:8000/docs` 来探索交互式 API 文档。

## 🎯 项目特色

**YAI Nexus AgentKit** 专为希望使用 **FastAPI** 构建支持 **AG-UI 协议** 的 **现代流式 AI 应用** 的开发者而设计。与通用 AI 框架不同，我们提供：

- **🔥 FastAPI 优先设计**: 从零开始为 Web 应用构建
- **📡 默认支持流式传输**: 通过服务器发送事件 (SSE) 实现实时 AI 交互
- **🎨 AG-UI 协议**: 标准化事件模型，实现无缝前端集成
- **📊 支持多种 LLM**: OpenAI, Anthropic, 智谱AI, 通义千问, OpenRouter
- **🔧 渐进式复杂度**: 提供从简单到高级的三个 API 级别
- **🏗️ 生产就绪**: 基于 LangChain 和 LangGraph 构建

## 🏛️ 架构概览

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 UI       │◄──►│  AG-UI 协议   │◄──►│  YAI AgentKit   │
│                 │    │  (SSE 事件)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   LangGraph     │◄──►│   FastAPI 应用  │
                       │  (编排)         │    │   (Web 层)      │
                       └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │    多 LLM 支持   │
                       │   (OpenAI 等)   │
                       └─────────────────┘
```

## 🎨 三个级别的 API 复杂度

### 级别 1: 简单模式
非常适合入门 - 只需最少的设置即可直接调用 LLM。

```python
from yai_nexus_agentkit import create_llm

# 创建 LLM 客户端
llm = create_llm({
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "sk-..."
})

# 简单聊天
response = llm.invoke("你好，世界！")
print(response.content)
```

### 级别 2: 流式模式
通过服务器发送事件 (SSE) 添加实时流式响应。

```python
from yai_nexus_agentkit.adapter import BasicSSEAdapter
from sse_starlette.sse import EventSourceResponse

# 创建流式适配器
adapter = BasicSSEAdapter(llm)

# FastAPI 端点
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return EventSourceResponse(
        adapter.stream_response(request.message),
        media_type="text/event-stream"
    )
```

### 级别 3: 高级模式
完全支持 AG-UI 协议，并与 LangGraph 进行编排。

```python
from yai_nexus_agentkit.adapter import AGUIAdapter
from yai_nexus_agentkit.adapter.sse_advanced import Task

# 使用 LangGraph agent 创建 AG-UI 适配器
adapter = AGUIAdapter(your_langgraph_agent)

# 兼容 AG-UI 的端点
@app.post("/chat/advanced")
async def chat_advanced(task: Task):
    return EventSourceResponse(
        adapter.event_stream_adapter(task),
        ping=15,
        media_type="text/event-stream"
    )
```

## 🔧 安装与设置

### 基本安装
```bash
pip install yai-nexus-agentkit
```

### 带可选依赖的安装
```bash
# 针对特定的 LLM 提供商
pip install yai-nexus-agentkit[openai,anthropic]

# 支持持久化
pip install yai-nexus-agentkit[persistence]

# 用于开发
pip install yai-nexus-agentkit[dev]
```

### 环境配置
创建一个 `.env` 文件:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
MODEL_TO_USE=gpt-4o-mini  # 可选：指定默认模型
```

## 📊 支持的 LLM 提供商

| 提供商 | 模型 | 状态 |
|---|---|---|
| **OpenAI** | GPT-4, GPT-3.5, GPT-4o | ✅ 完全支持 |
| **Anthropic** | Claude-3, Claude-3.5 | ✅ 完全支持 |
| **智谱AI (ZhipuAI)** | GLM-4, GLM-3 | ✅ 完全支持 |
| **通义 (Tongyi)** | Qwen 系列 | ✅ 完全支持 |
| **OpenRouter** | 100+ 模型 | ✅ 完全支持 |

## 🎭 实际示例

这是一个完整的流式 AI 聊天应用：

```python
# main.py
from fastapi import FastAPI
from yai_nexus_agentkit import create_llm
from yai_nexus_agentkit.adapter import BasicSSEAdapter
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="我的 AI 聊天应用")

# 初始化 LLM
llm = create_llm({
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "your-api-key"
})

# 创建流式适配器
adapter = BasicSSEAdapter(llm)

@app.post("/chat/stream")
async def chat_stream(message: str):
    return EventSourceResponse(
        adapter.stream_response(message),
        media_type="text/event-stream"
    )

# 运行: uvicorn main:app --reload
```

前端 JavaScript:
```javascript
// 连接到流式端点
const eventSource = new EventSource('/chat/stream');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.event === 'content') {
        // 显示流式内容
        document.getElementById('chat').innerHTML += data.data.content;
    }
};
```

## 🏗️ 项目结构

```
yai-nexus-agentkit/
├── src/yai_nexus_agentkit/
│   ├── llm/                 # 多LLM支持
│   │   ├── factory.py       # LLM 创建工厂
│   │   ├── providers.py     # 提供商定义
│   │   └── models.py        # 模型枚举
│   ├── adapter/             # 交互适配器
│   │   ├── sse_basic.py     # 基础 SSE 支持
│   │   └── sse_advanced.py  # AG-UI 协议支持
│   ├── core/                # 核心抽象
│   └── persistence/         # 可选的持久化层
├── examples/
│   └── fast_api_app/        # 完整的 FastAPI 示例
└── configs/                 # 配置文件
```

## 🤝 贡献

我们欢迎贡献！请参阅我们的 [贡献指南](CONTRIBUTING.md) 了解详情。

### 开发设置
```bash
# 克隆仓库
git clone https://github.com/yai-nexus/yai-nexus-agentkit.git
cd yai-nexus-agentkit

# 以开发模式安装
pip install -e ".[dev]"

# 运行测试
pytest

# 格式化代码
black .
ruff check .
```

## 📖 文档

- **[API 参考](docs/api.md)** - 完整的 API 文档
- **[示例](examples/)** - 可运行的示例和教程
- **[FastAPI 集成](examples/fast_api_app/README.md)** - FastAPI 特定指南
- **[AG-UI 协议](docs/ag-ui.md)** - AG-UI 协议实现

## 🔒 安全

- ✅ API 密钥通过环境变量安全处理
- ✅ 不记录或存储敏感数据
- ✅ 输入验证和净化
- ✅ 支持速率限制 (通过 FastAPI 中间件)

## 🎯 路线图

- [ ] **v0.1.0**: 核心功能与基础流式传输
- [ ] **v0.2.0**: 高级 LangGraph 集成
- [ ] **v0.3.0**: WebSocket 支持
- [ ] **v0.4.0**: 内置身份验证
- [ ] **v0.5.0**: 分布式部署支持

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 基于 [LangChain](https://github.com/langchain-ai/langchain) 和 [LangGraph](https://github.com/langchain-ai/langgraph) 构建
- 开发体验受 [FastAPI](https://fastapi.tiangolo.com/) 启发
- AG-UI 协议用于标准化 AI 交互
- 开源 AI 社区

## 🚀 立即开始

```bash
pip install yai-nexus-agentkit
python -m examples.fast_api_app.main
```

**使用 FastAPI 和默认流式传输构建 AI 应用的未来！**

---

<div align="center">
  <p>由 YAI Nexus 团队倾情奉献 ❤️</p>
  <p>
    <a href="https://github.com/yai-nexus/yai-nexus-agentkit">GitHub</a> •
    <a href="https://docs.yai-nexus.com">文档</a> •
    <a href="https://discord.gg/yai-nexus">社区</a>
  </p>
</div> 