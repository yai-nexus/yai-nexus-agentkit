# YAI Nexus Monorepo

A unified monorepo containing both backend and frontend components for the YAI Nexus ecosystem - building AI applications with multi-LLM support and modern web interfaces.

## 🏗️ Project Structure

```
/ (monorepo root)
├── packages/
│   ├── agentkit/          # Python backend toolkit
│   └── fekit/             # TypeScript frontend SDK
├── examples/
│   ├── nextjs-app/        # Next.js 15 example application
│   └── python-backend/    # Python backend example
├── package.json           # Root workspace configuration
├── pnpm-workspace.yaml    # pnpm workspace config
└── tsconfig.base.json     # Shared TypeScript config
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** for backend development
- **Node.js 18+** and **pnpm** for frontend development

### Installation

```bash
# Clone the repository
git clone https://github.com/yai-nexus/yai-nexus-agentkit.git
cd yai-nexus-agentkit

# Install all workspace dependencies
pnpm install

# Install backend dependencies
cd packages/agentkit
pip install -e ".[all]"
```

### Development

**Backend Development:**
```bash
cd packages/agentkit

# Run tests
pytest

# Format code
black .

# Lint code
ruff check .

# Run FastAPI example
python -m examples.fast_api_app.main
```

**Frontend Development:**
```bash
# Build frontend SDK
pnpm --filter @yai-nexus/fekit build

# Run Next.js example app
pnpm --filter nextjs-app dev
```

## 📦 Packages

### 🐍 Backend: `packages/agentkit/`

A Python toolkit for building AI applications with multi-LLM support and extensible architecture.

**Key Features:**
- **Multi-LLM Support**: OpenAI, Anthropic, ZhipuAI, Tongyi, OpenRouter
- **Factory Pattern**: Type-safe LLM client creation
- **Configuration-driven**: JSON-based config with environment variable support
- **Extensible Architecture**: Clean abstractions for persistence, orchestration, and adapters

**Quick Example:**
```python
from yai_nexus_agentkit import create_llm, OpenAIModel

config = {
    "provider": "openai",
    "model": OpenAIModel.GPT_4O.value,
    "api_key": "sk-..."
}
llm = create_llm(config)
response = llm.invoke("Hello, world!")
```

### 🌐 Frontend: `packages/fekit/`

A TypeScript SDK for integrating AI capabilities into Next.js applications with CopilotKit.

**Key Features:**
- **Next.js Integration**: Seamless integration with Next.js 14+
- **TypeScript First**: Full type safety and IntelliSense support
- **CopilotKit Compatible**: Built for modern AI-powered UX patterns
- **Dual Module Support**: Both CommonJS and ESM exports

**Quick Example:**
```typescript
import { ... } from '@yai-nexus/fekit';

// Use in your Next.js application
// Integration with yai-nexus-agentkit backend
```

## 🎯 Examples

### Next.js Application (`examples/nextjs-app/`)

A modern Next.js 15 application showcasing frontend AI integration:

- **React 19** with latest features
- **TailwindCSS 4** for styling
- **Turbopack** for fast development
- **CopilotKit** integration ready

```bash
cd examples/nextjs-app
npm run dev    # Start development server
npm run build  # Build for production
```

### Python Backend (`examples/python-backend/`)

Example Python backend demonstrating agentkit usage:

```bash
cd examples/python-backend
python main.py
```

## 🔧 Configuration

### Environment Variables

Set up the following environment variables based on your LLM providers:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# OpenRouter
export OPENROUTER_API_KEY="sk-or-..."

# Tongyi (Alibaba)
export DASHSCOPE_API_KEY="sk-..."

# Optional: Specify default model
export MODEL_TO_USE="gpt-4o"
```

### LLM Configuration

Backend LLM configurations are stored in `packages/agentkit/configs/DEFAULT_GROUP/llms.json`:

```json
{
  "llms": [
    {
      "provider": "openai",
      "model": "gpt-4o",
      "api_key": "${OPENAI_API_KEY}",
      "default": true
    }
  ]
}
```

## 🧪 Testing

**Backend Tests:**
```bash
cd packages/agentkit
pytest                    # Run all tests
pytest --cov             # Run with coverage
```

**Frontend Tests:**
```bash
pnpm --filter @yai-nexus/fekit test    # Run SDK tests
pnpm --filter nextjs-app test           # Run app tests
```

## 🔨 Building

**Build All Packages:**
```bash
pnpm --filter packages/* build
```

**Build Specific Package:**
```bash
pnpm --filter @yai-nexus/fekit build
pnpm --filter nextjs-app build
```

## 📚 Documentation

- **Backend Documentation**: See `packages/agentkit/README.md`
- **Frontend Documentation**: See `packages/fekit/README.md`
- **Development Guide**: See `CLAUDE.md` for detailed development instructions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Workflow

- **Backend changes**: Work in `packages/agentkit/`
- **Frontend changes**: Work in `packages/fekit/`
- **Example updates**: Work in `examples/`
- **Run tests** before submitting PRs
- **Follow code style** (black, ruff for Python; prettier, eslint for TypeScript)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Issues**: [GitHub Issues](https://github.com/yai-nexus/yai-nexus-agentkit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yai-nexus/yai-nexus-agentkit/discussions)

---

Made with ❤️ by the YAI Nexus team