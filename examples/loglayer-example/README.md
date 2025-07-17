# `@yai-nexus/loglayer-support` 示例

欢迎来到 `loglayer-support` 的官方示例项目！本项目旨在通过生动的演示，展示 `@yai-nexus/loglayer-support` 如何彻底解决现代 Web 开发中的日志痛点，特别是 Next.js 环境下的兼容性问题。

## 🌟 核心亮点：一行代码的革命

### 1. 极致简化

传统上，在 Next.js 中设置一个健壮的日志系统可能需要上百行复杂的代码。`@yai-nexus/loglayer-support` 将其简化为 **1 行** 代码。

**传统方式**:
```typescript
// 可能需要复杂的异步初始化、代理对象、错误处理...
// ... 100+ 行复杂、难以维护的逻辑
```

**使用 `loglayer-support`**:
```typescript
import { createNextjsLoggerSync } from '@yai-nexus/loglayer-support';

export const logger = createNextjsLoggerSync('nextjs-app');
```

### 2. 专为 Next.js 设计

- ✅ **零配置**：自动检测 Next.js 环境，无需手动配置。
- ✅ **智能回退**：自动在 Pino、Winston 和 Console 传输器之间选择最佳方案，确保日志系统永不崩溃。
- ✅ **开箱即用**：解决了 Webpack 和边缘计算环境中的所有已知兼容性问题。

### 3. 直观易用的 API

提供了一套富有表现力且易于使用的 API，帮助您创建结构化的、可查询的日志。

```typescript
// 基础日志
logger.info('这是一条基础日志', { a: 1 });

// 结构化上下文绑定
logger.forRequest(requestId).info('带请求 ID 的日志');

// 强大的错误和性能记录
logger.logError(new Error('出错了'), { userId: '123' });
logger.logPerformance('dbQuery', 120, { query: 'SELECT *' });
```

## 📊 核心优势

| 特性 | 优势 |
|:--- |:--- |
| **代码简洁** | 将 100+ 行的设置代码简化为 1 行。|
| **完美兼容 Next.js** | 零配置，自动解决 Webpack 和边缘环境的兼容性问题。|
| **灵活的传输器** | 支持 Pino, Winston, Console，并能根据环境智能选择。|
| **高可靠性** | 具备自动回退机制，确保日志系统在任何情况下都能工作。|
| **极低维护成本** | “即插即用”的设计，几乎无需维护。|


## 🚀 快速上手

### 1. 安装

在项目根目录执行以下命令，pnpm 会自动安装所有工作区依赖。

```bash
pnpm install
```

### 2. 运行示例

我们提供了多个脚本来演示不同功能：

| 命令 | 描述 |
| --- | --- |
| `npm run test:basic` | 演示环境检测、预设配置、上下文绑定等核心功能。 |
| `npm run test:transports` | 测试并对比 Console, Winston, Pino 等多种日志传输器的表现。 |
| `npm run test:migration` | 展示了如何轻松集成到现有项目中。 |
| `npm run test:all` | 运行所有示例。 |

## 📂 项目结构

```
src/
├── basic-usage.js        # 基础功能演示
├── transport-tests.js    # 多种传输器对比测试
└── migration-example.js  # 集成示例
```

## 💡 最佳实践

- **对于 Next.js 项目**：强烈推荐使用 `createNextjsLoggerSync`，它能提供最佳的兼容性和性能。
- **对于通用 Node.js 项目**：使用 `createLoggerWithPreset`，并根据环境（`development` 或 `production`）选择合适的预设。
- **利用上下文**：充分使用 `.forRequest()`, `.forUser()` 等方法来创建结构化的、易于查询的日志。

## 🤝 贡献

如果您发现任何问题或有改进建议，欢迎提交 Issue 或 Pull Request！
