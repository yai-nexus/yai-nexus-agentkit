# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is a monorepo containing:
- `packages/agentkit/` - Python backend toolkit for building AI applications with multi-LLM support
- `packages/fekit/` - Frontend SDK package for Next.js integration with yai-nexus-agentkit and CopilotKit
- `examples/nextjs-app/` - Next.js 15 example application with React 19 and TailwindCSS
- `examples/python-backend/` - Python backend example

## Development Commands

### Backend Package (`packages/agentkit/`)

```bash
cd packages/agentkit

# Install the package in development mode with all dependencies
pip install -e ".[all]"

# Install specific optional dependencies
pip install -e ".[openai,anthropic,fastapi]"  # Common subset
pip install -e ".[dev]"  # Development tools only

# Format code with black
black .

# Lint with ruff
ruff check .

# Run tests
pytest

# Run tests with coverage
pytest --cov

# Run single test file
pytest tests/unit/test_specific_file.py

# Run specific test function
pytest tests/unit/test_specific_file.py::test_function_name
```

### Frontend Package (`packages/fekit/`)

```bash
cd packages/fekit
npm run build    # Build the SDK using tsup
npm run dev      # Build in watch mode
```

### Next.js Example App (`examples/nextjs-app/`)

```bash
cd examples/nextjs-app
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Python Backend Example (`examples/python-backend/`)

```bash
cd examples/python-backend

# Install dependencies
pip install -r requirements.txt

# Run the backend server (FastAPI with ag-ui-protocol integration)
python main.py
```

### Monorepo Management

```bash
# Install all dependencies and link workspaces
pnpm install

# Build all packages
pnpm --filter packages/* build

# Build specific package
pnpm --filter @yai-nexus/fekit build
pnpm --filter nextjs-app build
```

## Architecture

### Backend Package (`packages/agentkit/`)

This is a Python toolkit for building AI applications with multi-LLM support and extensible architecture.

**LLM Factory (`src/yai_nexus_agentkit/llm/`)**
- `create_llm()` factory function creates LangChain-compatible LLM clients (in `factory.py`)
- `LLMFactory` class manages multiple LLM instances (in `factory.py`)
- `LLMProvider` enum defines supported providers (in `providers.py`)
- `LLMConfig` model for configuration validation (in `config.py`)
- Model enums for type-safe model selection (in `models.py`):
  - `OpenAIModel`, `AnthropicModel`, `ZhipuModel`, `TongyiModel`, `OpenRouterModel`
- Supports multiple providers: OpenAI, Anthropic, ZhipuAI, Tongyi, OpenRouter
- Configuration-driven approach using JSON config files
- Environment variable substitution for API keys

**Configuration System**
- Uses `yai-nexus-configuration` package for config management
- LLM configs stored in `configs/DEFAULT_GROUP/llms.json`
- Supports environment variable interpolation (e.g., `${OPENAI_API_KEY}`)

**Core Abstractions (`src/yai_nexus_agentkit/core/`)**
- `BaseCheckpoint`: Abstract interface for state persistence
- `BusinessLLM`: Business layer LLM wrapper with simplified interfaces
- `embedding.py`: Embedding functionality
- `repository.py`: Repository pattern abstractions

### Frontend Package (`packages/fekit/`)

**SDK Package (`@yai-nexus/fekit`)**
- Built with TypeScript and bundled using tsup
- Configured as both CommonJS and ESM modules with TypeScript declarations
- Currently re-exports from `@ag-ui/proto` package
- Includes "use client" banner for Next.js client-side compatibility
- Peer dependencies: CopilotKit, Next.js 14+, React 18+

**Build Configuration**
- Uses shared TypeScript configuration via `tsconfig.base.json`
- tsup configured for dual format output (CJS/ESM) with sourcemaps
- TypeScript targeting ES2020 with strict mode enabled

**Dependencies**
The SDK depends on the ag-ui ecosystem:
- `@ag-ui/client`, `@ag-ui/core`, `@ag-ui/encoder`, `@ag-ui/proto` (v0.0.28+)

## Key Design Patterns

**Factory Pattern for LLM Creation**
The `create_llm()` function in `packages/agentkit/src/yai_nexus_agentkit/llm/factory.py` dynamically imports and instantiates LLM clients based on provider configuration.

**Configuration-Driven Architecture**
- LLM configurations are externalized to JSON files
- Environment variables are used for sensitive data (API keys)
- The `MODEL_TO_USE` environment variable allows runtime model selection

**Optional Dependencies**
The backend project uses optional dependencies for different LLM providers and features:
- `[openai]`: OpenAI support
- `[anthropic]`: Anthropic support
- `[zhipu]`: ZhipuAI support
- `[tongyi]`: Tongyi support
- `[postgres]`: PostgreSQL persistence
- `[redis]`: Redis support
- `[fastapi]`: FastAPI web framework
- `[dev]`: Development tools

## Environment Setup

Required environment variables depend on which LLM providers you use:
- `OPENAI_API_KEY`: For OpenAI models
- `OPENROUTER_API_KEY`: For OpenRouter models  
- `DASHSCOPE_API_KEY`: For Tongyi models
- `ANTHROPIC_API_KEY`: For Anthropic models
- `ZHIPUAI_API_KEY`: For ZhipuAI models
- `MODEL_TO_USE`: (Optional) Specific model to use from config

For the Python backend example (`examples/python-backend/`), ensure you have the required API keys set based on which LLM providers are configured in your `llms.json`.

## Usage Examples

### Basic LLM Usage (Backend)
```python
from yai_nexus_agentkit import create_llm, OpenAIModel

# Create LLM with model enum (type-safe)
config = {
    "provider": "openai",
    "model": OpenAIModel.GPT_4O.value,
    "api_key": "sk-..."
}
llm = create_llm(config)
```

### Multi-LLM Management (Backend)
```python
from yai_nexus_agentkit import LLMFactory, LLMProvider

configs = [
    {"provider": "openai", "model": "gpt-4o", "api_key": "sk-..."},
    {"provider": "openrouter", "model": "google/gemini-pro", "api_key": "sk-or-...", "base_url": "https://openrouter.ai/api/v1"},
]

factory = LLMFactory(configs)
openai_client = factory.get_client(LLMProvider.OPENAI)
openrouter_client = factory.get_client(LLMProvider.OPENROUTER)
```

### Frontend Integration
```typescript
import { ... } from '@yai-nexus/fekit';

// Use the SDK in your Next.js application
// Currently re-exports from @ag-ui/proto
```

## Key Files

**Backend (`packages/agentkit/`)**
- `src/yai_nexus_agentkit/llm/factory.py` - Main LLM factory implementation
- `configs/DEFAULT_GROUP/llms.json` - LLM configurations
- `src/yai_nexus_agentkit/__init__.py` - Public API exports

**Frontend (`packages/fekit/`)**
- `src/index.ts` - Main entry point, re-exports from @ag-ui/proto
- `src/client.ts` - Client-side exports for Next.js components
- `src/server.ts` - Server-side exports for API routes
- `tsup.config.ts` - Build configuration for the SDK

**Examples**
- `examples/nextjs-app/` - Complete Next.js 15 application with CopilotKit integration
- `examples/python-backend/main.py` - FastAPI backend with ag-ui-protocol and yai-nexus-agentkit integration

**Root Configuration**
- `tsconfig.base.json` - Shared TypeScript configuration
- `pnpm-workspace.yaml` - Workspace configuration
- `package.json` - Root package configuration

## Code Quality Standards

### Python Development (Backend)

**Required Tools:**
- **Code formatting**: Use `black` for all Python code formatting
- **Linting**: Use `ruff` for static analysis and import sorting
- **Type hints**: Always use type hints for function parameters and return values

**Testing Requirements:**
- **Coverage target**: Maintain 85%+ test coverage using `pytest-cov`
- **Test types**: Unit tests (with mocks), integration tests (no mocks, logs to `logs/` directory), example tests
- **Naming**: Test files as `test_*.py`, functions as `test_具体功能描述`

**Development Workflow:**
- Use `pre-commit` hooks to automatically run `black` and `ruff` before commits
- All custom exceptions should inherit from a base `AgentKitError` class
- Examples in `examples/` directory must be runnable independently

### Frontend Development

**Build Process:**
- Always build `@yai-nexus/fekit` SDK before running Next.js app: `pnpm --filter @yai-nexus/fekit build`
- Use separate client/server imports: `@yai-nexus/fekit/client` for client components, `@yai-nexus/fekit/server` for API routes
- Must use `pnpm` from monorepo root, never use `npm` or `yarn` in subdirectories

## Development Notes

- The frontend SDK uses separated client/server entry points to prevent Node.js modules from being bundled in client code
- Example application uses Next.js 15 with React 19 and TailwindCSS 4
- Python backend uses FastAPI with ag-ui-protocol for streaming AI responses
- All Python projects use `pyproject.toml` with pytest configured for both root and `src` paths