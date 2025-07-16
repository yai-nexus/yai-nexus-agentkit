# YAI Nexus Monorepo

YAI Nexus 生态系统的统一 Monorepo，包含用于构建具有多 LLM 支持和现代 Web 界面的 AI 应用的后端和前端组件。

## 🏗️ 项目结构

```
/ (monorepo 根目录)
├── packages/
│   ├── agentkit/              # Python 后端工具包
│   ├── fekit/                 # TypeScript 前端 SDK
│   ├── loglayer-support/      # 🆕 统一日志抽象层 (v0.3.0+)
│   └── loguru-support/        # Python 日志支持
├── examples/
│   ├── nextjs-app/            # Next.js 15 示例应用
│   ├── python-backend/        # Python 后端示例
│   └── loglayer-example/      # 🆕 日志系统使用示例和迁移指南
├── package.json               # 根工作区配置
├── pnpm-workspace.yaml        # pnpm 工作区配置
├── CHANGELOG.md               # 🆕 版本更新日志
└── tsconfig.base.json         # 共享 TypeScript 配置
```

## ✨ v0.3.0 重大更新

### 🎉 LogLayer 抽象层
- **全新的日志解决方案**：基于 LogLayer 的统一日志抽象层
- **解决 Next.js 兼容性**：彻底解决 webpack 打包问题
- **代码量减少 99%+**：从 136 行复杂逻辑简化为 1 行代码
- **完全向后兼容**：无需修改现有业务代码

```typescript
// 新版本：一行代码搞定日志系统！
import { createNextjsLoggerSync } from "@yai-nexus/loglayer-support";
export const logger = createNextjsLoggerSync('my-app');
```

详细信息请查看：
- 📚 [迁移指南](./examples/loglayer-example/)
- 📋 [更新日志](./CHANGELOG.md)
- 🎯 [项目总结](./PROJECT_SUMMARY.md)

## 🚀 快速上手

### 环境要求

- **Python 3.8+** 用于后端开发
- **Node.js 18+** 和 **pnpm** 用于前端开发

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/yai-nexus/yai-nexus-agentkit.git
cd yai-nexus-agentkit

# 安装所有工作区的依赖
pnpm install

# 安装后端开发依赖
# 这将以可编辑模式安装 agentkit 及其所有可选依赖
cd packages/agentkit
pip install -e ".[all]"
```

### 开发运行

**后端开发:**
```bash
cd packages/agentkit

# 运行测试
pytest

# 格式化代码
black .

# 检查代码风格
ruff check .

# 运行 FastAPI 示例
# 注意：此示例旨在通过 python 命令直接启动
python examples/fast_api_app/main.py
```

**前端开发:**
```bash
# 构建前端 SDK
pnpm --filter @yai-nexus/fekit build

# 运行 Next.js 示例应用
pnpm --filter nextjs-app dev
```

## 📦 核心包

### 🐍 后端: `packages/agentkit/`

一个用于构建具有多LLM支持和可扩展架构的AI应用的Python工具包。

**主要特性:**
- **多LLM支持**: OpenAI, Anthropic, ZhipuAI, Tongyi, OpenRouter
- **工厂模式**: 类型安全的LLM客户端创建
- **配置驱动**: 基于JSON的配置，支持环境变量
- **可扩展架构**: 清晰的持久化、编排和适配器抽象

**快速示例:**
```python
from yai_nexus_agentkit import create_llm, OpenAIModel

config = {
    "provider": "openai",
    "model": OpenAIModel.GPT_4O.value,
    "api_key": "sk-..."
}
llm = create_llm(config)
response = llm.invoke("你好，世界！")
```

### 🌐 前端: `packages/fekit/`

一个用于将AI功能集成到Next.js应用程序的TypeScript SDK。

**主要特性:**
- **Next.js 集成**: 与 Next.js 14+ 无缝集成
- **TypeScript 优先**: 完全的类型安全和智能感知支持
- **兼容 CopilotKit**: 为现代AI驱动的UX模式而构建
- **双模块支持**: 同时支持 CommonJS 和 ESM

**快速示例:**
```typescript
import { ... } from '@yai-nexus/fekit';

// 在你的 Next.js 应用中使用
// 以此来集成 yai-nexus-agentkit 后端
```

## 🎯 示例应用

### Next.js 应用 (`examples/nextjs-app/`)

一个展示前端AI集成的现代Next.js 15应用：

- **React 19**
- **TailwindCSS 4**
- **Turbopack**
- 已集成 **CopilotKit**

```bash
cd examples/nextjs-app
pnpm dev    # 启动开发服务器
pnpm build  # 构建生产版本
```

### Python 后端 (`examples/python-backend/`)

演示 `agentkit` 用法的Python后端示例：

```bash
cd examples/python-backend
python main.py
```

## 🔧 配置

### 环境变量

根据你使用的LLM提供商，设置以下环境变量：

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# OpenRouter
export OPENROUTER_API_KEY="sk-or-..."

# 阿里云通义千问
export DASHSCOPE_API_KEY="sk-..."

# 可选：指定默认使用的模型
export MODEL_TO_USE="gpt-4o"
```

### LLM 配置

后端 LLM 配置存储在 `packages/agentkit/configs/DEFAULT_GROUP/llms.json` 中：

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

## 🧪 测试

**后端测试:**
```bash
cd packages/agentkit
pytest         # 运行所有测试
pytest --cov   # 运行并检查测试覆盖率
```

**前端测试:**
```bash
pnpm --filter @yai-nexus/fekit test    # 运行 SDK 测试
pnpm --filter nextjs-app test          # 运行应用测试
```

## 🔨 构建

**构建所有包:**
```bash
pnpm --filter 'packages/*' build
```

**构建特定包:**
```bash
pnpm --filter @yai-nexus/fekit build
pnpm --filter nextjs-app build
```

## 🤝 贡献指南

我们欢迎各种形式的贡献！

1.  Fork 本仓库
2.  创建你的功能分支: `git checkout -b feature/amazing-feature`
3.  提交你的修改: `git commit -m 'Add amazing feature'`
4.  推送至分支: `git push origin feature/amazing-feature`
5.  提交一个 Pull Request

### 开发工作流

- **后端代码规范**: 使用 `black` 进行格式化，使用 `ruff` 进行代码检查。
- **前端代码规范**: 使用 `prettier` 和 `eslint`。
- **提交前**: 确保运行并通过所有相关测试。

## 📄 许可证

本项目基于 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。
