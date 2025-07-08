# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Package Installation
```bash
# Install the package in development mode with all dependencies
pip install -e ".[all]"

# Install specific optional dependencies
pip install -e ".[openai,anthropic,fastapi]"  # Common subset
pip install -e ".[dev]"  # Development tools only
```

### Code Quality Tools
```bash
# Format code with black
black .

# Lint with ruff
ruff check .

# Run tests
pytest

# Run tests with coverage
pytest --cov
```

### Running Examples
```bash
# Run FastAPI example application
python -m examples.fast_api_app.main

# Or with uvicorn directly
uvicorn examples.fast_api_app.main:app --reload
```

## Project Architecture

This is a Python toolkit for building AI applications with multi-LLM support and extensible architecture.

### Core Components

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

**Module Structure**
- `adapter/`: Interaction adapters (planned)
- `infrastructure/`: Infrastructure components
- `orchestration/`: Workflow orchestration (planned)
- `persistence/`: Data persistence layer (planned)

### Key Design Patterns

**Factory Pattern for LLM Creation**
The `create_llm()` function in `src/yai_nexus_agentkit/llm/factory.py` dynamically imports and instantiates LLM clients based on provider configuration. The LLM module is organized as:
- `factory.py`: Main factory function
- `providers.py`: Provider enumeration
- `config.py`: Configuration models
- `__init__.py`: Clean public interface

**Configuration-Driven Architecture**
- LLM configurations are externalized to JSON files
- Environment variables are used for sensitive data (API keys)
- The `MODEL_TO_USE` environment variable allows runtime model selection

**Optional Dependencies**
The project uses optional dependencies for different LLM providers and features:
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

## Testing

The project uses pytest with configuration in `pyproject.toml`. Python path includes both root and `src` directories.

## Usage Examples

### Basic LLM Usage
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

### Multi-LLM Management
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

### Business Layer Usage
```python
from yai_nexus_agentkit.core.llm import BusinessLLM

business_llm = BusinessLLM(llm)
response = await business_llm.chat(
    prompt="Explain quantum computing",
    system_prompt="You are a science educator"
)
```

Run `python examples/llm_usage_demo.py` for a complete demonstration.

## Legacy Code

The `old/` directory contains previous implementation (`lucas_ai_core`) that's being refactored. Don't modify files in this directory.