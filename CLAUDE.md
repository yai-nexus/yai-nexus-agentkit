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

# Python backend setup (uses .venv + uv for speed)
uv venv .venv
source .venv/bin/activate  # Linux/Mac
# One-command install for all Python packages and examples (10-100x faster)
uv pip install -r requirements.txt

# Install additional test dependencies
uv pip install pytest-asyncio
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

# Logging examples (unified configuration)
pnpm dev:example:sls-pino       # Run SLS pino example (Node.js)
cd examples/sls-pino-example && npm run dev
cd examples/sls-loguru-example && python main.py
```

### Testing
```bash
# Python tests - install async test dependency first
cd packages/agentkit
source ../../.venv/bin/activate
uv pip install pytest-asyncio

# Run all tests
pytest                          # Run all tests
pytest --cov                    # Run with coverage
pytest --cov-report=html        # Generate HTML coverage report

# Run specific test files
pytest tests/unit/test_agui_adapter.py -v
pytest tests/integration/test_adapter_integration.py -v

# Run test patterns
pytest -k "tool_call" -v        # Run tests matching pattern
pytest -k "not integration" -v  # Exclude integration tests

# Run specific test methods/classes
pytest tests/unit/test_agui_adapter.py::TestToolCallTracker::test_start_call -v
pytest tests/unit/test_agui_adapter.py::TestToolCallTracker -v

# Async test support
pytest --asyncio-mode=auto      # Enable async mode

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

# SLS (Alibaba Cloud Simple Log Service) configuration
SLS_ENDPOINT=cn-hangzhou.log.aliyuncs.com
SLS_AK_ID=your_access_key_id
SLS_AK_KEY=your_access_key_secret
SLS_PROJECT=your_project_name
SLS_LOGSTORE=your_logstore_name
```

## Architecture Patterns

### LLM Factory Pattern
- Configuration-driven LLM client creation in `packages/agentkit/src/yai_nexus_agentkit/llm/`
- Provider registry with type-safe model enums
- Config stored in `packages/agentkit/configs/DEFAULT_GROUP/llms.json`

### Adapter System  
- Event-driven streaming with SSE and AG-UI protocols
- Located in `packages/agentkit/src/yai_nexus_agentkit/adapter/`
- **Key Components**:
  - `event_translator.py` - Abstract base class for event translation
  - `sse_advanced.py` - AGUIAdapter with full AG-UI protocol support
  - `langgraph_events.py` - LangGraph event type definitions  
  - `errors.py` - Adapter-specific error handling
- **Event Flow**: LangGraph events → EventTranslator → AG-UI events → SSE stream
- **Tool Call Tracking**: Maintains state across tool start/args/end/result events

### Persistence Architecture
- Tortoise ORM with PostgreSQL backend
- LangGraph checkpoint integration for conversation state
- Repository pattern in `packages/agentkit/src/yai_nexus_agentkit/persistence/`

### Logging Unification
- **统一配置接口**: Python 和 Node.js 使用语义一致的配置 API
- **同构支持**: Node.js 端自动检测环境（浏览器/Node.js/Next.js）
- **智能目录策略**: 按小时分目录 `logs/YYYYMMDD-HH/servicename.log`
- **多重输出**: 控制台 + 本地文件 + 云端日志（SLS）
- **配置位置**:
  - Python: `packages/loguru-support/src/yai_loguru_support/unified_config.py`
  - Node.js: `packages/pino-support/src/unified-config.ts`

## Unified Logging Usage

### Quick Start

#### Python (loguru-support)
```python
from yai_loguru_support import setup_dev_logging, setup_prod_logging
from loguru import logger

# Development (debug level, pretty console, hourly files)
setup_dev_logging("my-service")

# Production (info level, JSON console, hourly files) 
setup_prod_logging("my-service")

logger.info("Application started", version="1.0.0")
```

#### Node.js/TypeScript (pino-support)
```typescript
import { createDevLogger, createProdLogger } from '@yai-nexus/pino-support';

// Automatically detects environment (browser/Node.js/Next.js)
const logger = createDevLogger('my-service');     // Development
const logger = createProdLogger('my-service');    // Production

logger.info('Application started', { version: '1.0.0' });
```

### Advanced Configuration

#### Custom Configuration
```python
# Python
from yai_loguru_support import setup_logging

setup_logging("my-service", {
    "level": "debug",
    "console": {"enabled": True, "pretty": True},
    "file": {"enabled": True, "strategy": "daily"}
})
```

```typescript
// TypeScript
import { createLogger } from '@yai-nexus/pino-support';

const logger = createLogger({
  serviceName: 'my-service',
  level: 'debug',
  console: { enabled: true, pretty: true },
  file: { enabled: true, strategy: 'daily' }
});
```

#### SLS Cloud Integration
```python
# Python + SLS
from yai_loguru_support import setup_logging
from yai_loguru_support.sls import AliyunSlsSink

setup_logging("my-service")  # Base config
sls_sink = AliyunSlsSink.from_env()
logger.add(sls_sink, serialize=True, level="INFO")
```

```typescript
// TypeScript + SLS  
import { createLogger } from '@yai-nexus/pino-support';

const logger = createLogger({
  serviceName: 'my-service',
  cloud: {
    enabled: true,
    sls: {
      endpoint: process.env.SLS_ENDPOINT!,
      accessKeyId: process.env.SLS_AK_ID!,
      accessKeySecret: process.env.SLS_AK_KEY!,
      project: process.env.SLS_PROJECT!,
      logstore: process.env.SLS_LOGSTORE!
    }
  }
});
```

### Log Directory Structure
```
logs/
├── current -> 20241213-14          # Current hour symlink
├── 20241213-14/                    # Hourly directories
│   ├── README.md                   # Auto-generated documentation
│   ├── python-backend.log          # Python service logs
│   ├── nextjs-app.log              # Next.js application logs
│   └── my-service.log              # Custom service logs
└── 20241213-15/                    # Next hour directory
    └── ...
```

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

## Python Dependency Management

### Monorepo Structure
- **Root `requirements.txt`**: Unified entry point for all Python dependencies
- **Package `pyproject.toml`**: Each package/example maintains its own dependency specification
- **Installation Strategy**: Use `-e ./path/to/package` for editable local package installation

### Installation Options
```bash
# Recommended: Install all packages and examples at once
uv pip install -r requirements.txt

# Alternative: Install individual packages for focused development
cd packages/agentkit && uv pip install -e .
cd examples/python-backend && uv pip install -e .
```

### Package Structure
- All Python packages use standard `pyproject.toml` for dependency management
- No more individual `requirements.txt` files in sub-packages
- Local package dependencies are resolved automatically through editable installs

## Python Package Manager: uv

### Why uv?
- **Extreme Speed**: 10-100x faster than pip for package installation
- **Drop-in Replacement**: 100% compatible with pip commands
- **Better Dependency Resolution**: More reliable than pip
- **Built-in Virtual Environment**: `uv venv` replaces `python -m venv`

### Quick Start with uv
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate

# Install dependencies (much faster than pip)
uv pip install -r requirements.txt
```

### Common uv Commands
```bash
# Virtual environment
uv venv .venv                    # Create virtual environment
source .venv/bin/activate        # Activate (same as before)

# Package management
uv pip install -r requirements.txt  # Install from requirements
uv pip install package              # Install single package
uv pip freeze                       # List installed packages
uv pip uninstall package            # Uninstall package
```

## Virtual Environment Convention
Always use `.venv` as the Python virtual environment directory name for all Python projects in this monorepo.

## Debugging and Troubleshooting

### Common Issues
```bash
# Test failures due to missing dependencies
cd packages/agentkit
source ../../.venv/bin/activate
uv pip install pytest-asyncio

# Test failures due to import issues 
# Check that imports match the current adapter structure:
# - Use `from yai_nexus_agentkit.adapter.agui_adapter import AGUIAdapter`
# - Use `from yai_nexus_agentkit.adapter.models import Task`
# - Use `from yai_nexus_agentkit.adapter.tool_call_tracker import ToolCallTracker`

# Check adapter module structure
ls packages/agentkit/src/yai_nexus_agentkit/adapter/

# Verify database migrations (if using persistence)
cd packages/agentkit
aerich init -t yai_nexus_agentkit.persistence.db_config.TORTOISE_ORM
aerich init-db
```

### Development Tips
- **Event Translation**: The adapter system translates LangGraph events to AG-UI events in real-time
- **Tool Call State**: Tool calls must maintain consistent UUIDs across start/args/end/result events  
- **Async Testing**: Always use `@pytest.mark.asyncio` for async test methods
- **Mock Agents**: Use `CompiledStateGraph` mock with `astream_events()` for integration tests

## Future Improvements

### Logging System Enhancements
- **Unit Testing**: Add comprehensive unit tests for `setup_logging()` (Python) and `createLogger()` (TypeScript) functions
- **SLS Transport Integration**: Complete SLS cloud logging integration in unified configuration API
- **Performance Optimization**: Benchmark and optimize logging performance across high-throughput scenarios
- **Advanced Monitoring**: Expand logging metrics collection and alerting capabilities