# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a monorepo for the YAI Nexus AgentKit ecosystem, providing Python backend tools and TypeScript frontend SDKs for building AI applications with multi-LLM support and modern web interfaces.

### Core Architecture

- **Monorepo Structure**: Uses pnpm workspaces with packages and examples
- **Python Backend**: `packages/agentkit/` - Core AI agent toolkit with LLM factories, adapters, and persistence
- **TypeScript Frontend**: `packages/fekit/` - Next.js SDK for CopilotKit integration
- **Logging Support**: Separate packages for `loguru-support` (Python) and `pino-support` (Node.js)
- **Examples**: NextJS app, Python backend, and specialized logging examples

### Key Components

- **LLM Factory System**: Multi-provider support (OpenAI, Anthropic, ZhipuAI, Tongyi, Doubao, OpenRouter)
- **AG-UI Protocol**: FastAPI-first with SSE streaming and event-driven architecture
- **Persistence Layer**: Tortoise ORM with PostgreSQL, LangGraph checkpoints
- **Adapter Pattern**: BasicSSEAdapter, AGUIAdapter for different streaming protocols
- **Logging Infrastructure**: Unified logging with structured output and cloud integration

## Development Commands

### Environment Setup
```bash
# Install all workspace dependencies
pnpm install

# Python backend setup (uses .venv)
cd packages/agentkit
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -e ".[all]"
```

### Development Workflows
```bash
# Backend development
pnpm dev:sdk                    # Build agentkit in watch mode
pnpm dev:example:python         # Run Python backend example
pnpm dev:example:sls-loguru     # Run SLS loguru example

# Frontend development  
pnpm dev:example:next           # Run Next.js example app
pnpm --filter @yai-nexus/fekit build   # Build frontend SDK
```

### Testing
```bash
# Python tests
cd packages/agentkit
pytest                          # Run all tests
pytest --cov                    # Run with coverage

# Python code quality
black .                         # Format code
ruff check .                    # Lint code
```

### Building
```bash
# Build specific packages
pnpm build:sdk                  # Build agentkit
pnpm --filter @yai-nexus/fekit build   # Build fekit
pnpm --filter nextjs-app build # Build Next.js example
```

### Log Management
```bash
# Log utilities (logs stored in ./logs/)
pnpm logs:cleanup               # Clean old logs
pnpm logs:cleanup:dry           # Dry run cleanup
pnpm logs:stats                 # Show log statistics
pnpm logs:cleanup:14d           # Keep last 14 days
pnpm logs:cleanup:1gb           # Max 1GB total size
```

## Environment Variables

Core LLM provider configuration:
```bash
# Required for LLM providers
OPENAI_API_KEY="sk-..."
OPENROUTER_API_KEY="sk-or-..."
DASHSCOPE_API_KEY="sk-..."      # Tongyi/Alibaba
MODEL_TO_USE="gpt-4o"           # Default model

# Logging configuration (unified across Python/Node.js)
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_DIR=logs
SLS_LOGGING_ENABLED=false
```

## Architecture Patterns

### LLM Factory Pattern
- Configuration-driven LLM client creation in `packages/agentkit/src/yai_nexus_agentkit/llm/`
- Provider registry with type-safe model enums
- Config stored in `packages/agentkit/configs/DEFAULT_GROUP/llms.json`

### Adapter System  
- Event-driven streaming with SSE and AG-UI protocols
- Located in `packages/agentkit/src/yai_nexus_agentkit/adapter/`
- Supports both basic SSE and advanced AG-UI streaming

### Persistence Architecture
- Tortoise ORM with PostgreSQL backend
- LangGraph checkpoint integration for conversation state
- Repository pattern in `packages/agentkit/src/yai_nexus_agentkit/persistence/`

### Logging Unification
- Python: `loguru` with custom sinks for file/cloud logging
- Node.js: `pino` with transports for structured logging
- Hourly directory strategy: `logs/YYYYMMDD-HH/servicename.log`
- Cloud integrations: Alibaba Cloud SLS support

## Package Dependencies

### Python Stack
- FastAPI + Uvicorn for web framework
- LangChain + LangGraph for AI orchestration
- Tortoise ORM + AsyncPG for persistence
- Loguru for structured logging
- AG-UI Protocol for event streaming

### Node.js Stack  
- Next.js 15 with React 19
- CopilotKit for AI UI components
- Pino for structured logging
- TailwindCSS 4 for styling
- AG-UI Client for backend integration

## Virtual Environment Convention
Always use `.venv` as the Python virtual environment directory name for all Python projects in this monorepo.