# YAI Nexus AgentKit

> **A FastAPI-first AI agent toolkit with AG-UI protocol support for building modern streaming AI applications.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-first-green.svg)](https://fastapi.tiangolo.com/)
[![AG-UI](https://img.shields.io/badge/AG--UI-protocol-orange.svg)](https://github.com/ag-ui/protocol)

## 🚀 Quick Start

```bash
# Install the toolkit
pip install yai-nexus-agentkit

# Run the example application
python -m examples.fast_api_app.main
```

Open your browser to `http://localhost:8000/docs` to explore the interactive API documentation.

## 🎯 What Makes This Special

**YAI Nexus AgentKit** is designed specifically for developers who want to build **modern streaming AI applications** with **FastAPI** and **AG-UI protocol** support. Unlike generic AI frameworks, we provide:

- **🔥 FastAPI-First Design**: Built from the ground up for web applications
- **📡 Streaming by Default**: Server-Sent Events (SSE) for real-time AI interactions
- **🎨 AG-UI Protocol**: Standard event models for seamless frontend integration
- **📊 Multi-LLM Support**: OpenAI, Anthropic, ZhipuAI, Tongyi, OpenRouter
- **🔧 Gradual Complexity**: Three API levels from simple to advanced
- **🏗️ Production Ready**: Built on LangChain and LangGraph foundations

## 🏛️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │◄──►│  AG-UI Protocol │◄──►│  YAI AgentKit   │
│                 │    │   (SSE Events)  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   LangGraph     │◄──►│   FastAPI App   │
                       │  (Orchestration)│    │   (Web Layer)   │
                       └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Multi-LLM     │
                       │   (OpenAI, etc) │
                       └─────────────────┘
```

## 🎨 Three Levels of API Complexity

### Level 1: Simple Mode
Perfect for getting started - direct LLM calls with minimal setup.

```python
from yai_nexus_agentkit import create_llm

# Create LLM client
llm = create_llm({
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "sk-..."
})

# Simple chat
response = llm.invoke("Hello, world!")
print(response.content)
```

### Level 2: Streaming Mode
Add real-time streaming responses with Server-Sent Events.

```python
from yai_nexus_agentkit.adapter import BasicSSEAdapter
from sse_starlette.sse import EventSourceResponse

# Create streaming adapter
adapter = BasicSSEAdapter(llm)

# FastAPI endpoint
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return EventSourceResponse(
        adapter.stream_response(request.message),
        media_type="text/event-stream"
    )
```

### Level 3: Advanced Mode
Full AG-UI protocol support with LangGraph orchestration.

```python
from yai_nexus_agentkit.adapter import AGUIAdapter
from yai_nexus_agentkit.adapter.sse_advanced import Task

# Create AG-UI adapter with LangGraph agent
adapter = AGUIAdapter(your_langgraph_agent)

# AG-UI compatible endpoint
@app.post("/chat/advanced")
async def chat_advanced(task: Task):
    return EventSourceResponse(
        adapter.event_stream_adapter(task),
        ping=15,
        media_type="text/event-stream"
    )
```

## 🔧 Installation & Setup

### Basic Installation
```bash
pip install yai-nexus-agentkit
```

### With Optional Dependencies
```bash
# For specific LLM providers
pip install yai-nexus-agentkit[openai,anthropic]

# For persistence support
pip install yai-nexus-agentkit[persistence]

# For development
pip install yai-nexus-agentkit[dev]
```

### Environment Configuration
Create a `.env` file:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
MODEL_TO_USE=gpt-4o-mini  # Optional: specify default model
```

## 📊 Supported LLM Providers

| Provider | Models | Status |
|----------|---------|--------|
| **OpenAI** | GPT-4, GPT-3.5, GPT-4o | ✅ Full Support |
| **Anthropic** | Claude-3, Claude-3.5 | ✅ Full Support |
| **ZhipuAI** | GLM-4, GLM-3 | ✅ Full Support |
| **Tongyi** | Qwen Series | ✅ Full Support |
| **OpenRouter** | 100+ Models | ✅ Full Support |

## 🎭 Real-World Example

Here's a complete streaming AI chat application:

```python
# main.py
from fastapi import FastAPI
from yai_nexus_agentkit import create_llm
from yai_nexus_agentkit.adapter import BasicSSEAdapter
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="My AI Chat App")

# Initialize LLM
llm = create_llm({
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "your-api-key"
})

# Create streaming adapter
adapter = BasicSSEAdapter(llm)

@app.post("/chat/stream")
async def chat_stream(message: str):
    return EventSourceResponse(
        adapter.stream_response(message),
        media_type="text/event-stream"
    )

# Run: uvicorn main:app --reload
```

Frontend JavaScript:
```javascript
// Connect to streaming endpoint
const eventSource = new EventSource('/chat/stream');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.event === 'content') {
        // Display streaming content
        document.getElementById('chat').innerHTML += data.data.content;
    }
};
```

## 🏗️ Project Structure

```
yai-nexus-agentkit/
├── src/yai_nexus_agentkit/
│   ├── llm/                 # Multi-LLM support
│   │   ├── factory.py       # LLM creation factory
│   │   ├── providers.py     # Provider definitions
│   │   └── models.py        # Model enumerations
│   ├── adapter/             # Interaction adapters
│   │   ├── sse_basic.py     # Basic SSE support
│   │   └── sse_advanced.py  # AG-UI protocol support
│   ├── core/                # Core abstractions
│   └── persistence/         # Optional persistence layer
├── examples/
│   └── fast_api_app/        # Complete FastAPI example
└── configs/                 # Configuration files
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone the repository
git clone https://github.com/yai-nexus/yai-nexus-agentkit.git
cd yai-nexus-agentkit

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .
```

## 📖 Documentation

- **[API Reference](docs/api.md)** - Complete API documentation
- **[Examples](examples/)** - Working examples and tutorials
- **[FastAPI Integration](examples/fast_api_app/README.md)** - FastAPI-specific guide
- **[AG-UI Protocol](docs/ag-ui.md)** - AG-UI protocol implementation

## 🔒 Security

- ✅ API keys handled securely through environment variables
- ✅ No sensitive data logged or stored
- ✅ Input validation and sanitization
- ✅ Rate limiting support (via FastAPI middleware)

## 🎯 Roadmap

- [ ] **v0.1.0**: Core functionality with basic streaming
- [ ] **v0.2.0**: Advanced LangGraph integration
- [ ] **v0.3.0**: WebSocket support
- [ ] **v0.4.0**: Built-in authentication
- [ ] **v0.5.0**: Distributed deployment support

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on the shoulders of [LangChain](https://github.com/langchain-ai/langchain) and [LangGraph](https://github.com/langchain-ai/langgraph)
- Inspired by [FastAPI](https://fastapi.tiangolo.com/)'s developer experience
- AG-UI protocol for standardized AI interactions
- The open-source AI community

## 🚀 Get Started Today

```bash
pip install yai-nexus-agentkit
python -m examples.fast_api_app.main
```

**Build the future of AI applications with FastAPI and streaming by default!**

---

<div align="center">
  <p>Made with ❤️ by the YAI Nexus team</p>
  <p>
    <a href="https://github.com/yai-nexus/yai-nexus-agentkit">GitHub</a> •
    <a href="https://docs.yai-nexus.com">Documentation</a> •
    <a href="https://discord.gg/yai-nexus">Community</a>
  </p>
</div>