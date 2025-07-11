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

# Run FastAPI example application
python -m examples.fast_api_app.main

# Or with uvicorn directly
uvicorn examples.fast_api_app.main:app --reload
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
npm run dev      # Start development server with Turbopack
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
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
- `@ag-ui/client`, `@ag-ui/core`, `@ag-ui/encoder`, `@ag-ui/proto` (v0.0.31)

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
- `MODEL_TO_USE`: (Optional) Specific model to use from config

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
- `examples/llm_usage_demo.py` - Complete usage demonstration

**Frontend (`packages/fekit/`)**
- `src/index.ts` - Main entry point, re-exports from @ag-ui/proto
- `src/handler.ts` - Currently empty, likely for future CopilotKit integration
- `tsup.config.ts` - Build configuration for the SDK

**Root Configuration**
- `tsconfig.base.json` - Shared TypeScript configuration
- `pnpm-workspace.yaml` - Workspace configuration
- `package.json` - Root package configuration

## Development Notes

- The frontend SDK is in early development stage with many placeholder files
- SDK is designed to integrate yai-nexus-agentkit with CopilotKit in Next.js applications
- Example application uses latest Next.js 15 with React 19 and TailwindCSS 4
- The backend testing uses pytest with configuration in `packages/agentkit/pyproject.toml`
- Python path includes both root and `src` directories for testing

## Legacy Code

The `old/` directory contains previous implementation (`lucas_ai_core`) that's being refactored. Don't modify files in this directory.