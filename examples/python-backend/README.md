# Python Backend Example

This example demonstrates how to use YAI Nexus AgentKit to build a FastAPI-based AI backend with AG-UI protocol support.

## Features

- FastAPI web framework with AG-UI protocol
- LangGraph integration for AI workflow orchestration
- SSE (Server-Sent Events) streaming
- Multi-LLM provider support
- Structured logging with yai-loguru-support

## Usage

```bash
# Install dependencies (from repo root)
pip install -r requirements.txt

# Run the backend
cd examples/python-backend
python main.py
```

## Configuration

Set up your environment variables:

```bash
OPENAI_API_KEY="sk-..."
MODEL_TO_USE="gpt-4o"
```

The backend will be available at `http://localhost:8000`.