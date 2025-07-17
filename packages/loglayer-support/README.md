# @yai-nexus/loglayer-support

`@yai-nexus/loglayer-support` 是一个基于 [LogLayer](https://loglayer.dev) 构建的、生产就绪的日志解决方案，专为现代 TypeScript/JavaScript 项目（尤其是 Next.js）设计。它提供了一个统一、可靠且可插拔的日志记录接口。

## 🌟 核心价值

- ✅ **完美兼容 Next.js**：从根本上解决了在 Next.js Edge 和 Serverless 环境中常见的 Webpack 打包和运行时问题。
- ✅ **架构解耦**：将您的业务代码与底层的日志实现（如 Pino, Winston）完全解耦。您可以随时切换日志库，而无需修改一行业务代码。
- ✅ **零配置启动**：提供专为 Next.js 优化的同步创建函数，真正实现“一行代码，即可拥有”的开发体验。
- ✅ **环境自适应**：自动检测运行环境（服务器、浏览器、边缘函数），并选择最高效、最兼容的日志传输器。

## 💿 安装

1.  **核心库**:
    ```bash
    pnpm add @yai-nexus/loglayer-support loglayer
    ```

2.  **安装传输器 (Transports)**:
    根据您的需求和环境，安装一个或多个日志传输器。
    ```bash
    # [推荐] 用于服务端的强大传输器
    pnpm add @loglayer/transport-pino pino

    # [高兼容性] 适用于各种环境的传输器
    pnpm add @loglayer/transport-winston winston
    
    # [可选] 数据脱敏插件
    pnpm add @loglayer/plugin-redaction
    ```

## 🚀 使用指南

### 推荐：在 Next.js 中使用

我们提供了专为 Next.js 设计的同步创建函数，它能在应用初始化时安全地创建 logger 实例，并自动处理所有环境兼容性问题。

在您的 `lib/logger.ts` 或类似文件中：
```typescript
import { createNextjsLoggerSync } from '@yai-nexus/loglayer-support';

export const logger = createNextjsLoggerSync('my-nextjs-app');

// 然后在您的应用中任意位置导入和使用
// logger.info(...)
```
`createNextjsLoggerSync` 会在后台异步初始化最高效的传输器（如 Pino），如果失败，则会自动、安全地回退到兼容性更好的传输器（如 Winston 或 Console），确保您的日志系统永不中断。

### 通用用法 (Node.js 服务)

在非 Next.js 的 Node.js 环境中，您可以使用预设来异步创建一个 logger。

```typescript
import { createLoggerWithPreset } from '@yai-nexus/loglayer-support';

async function initializeLogger() {
  // 根据环境变量自动选择 'development' 或 'production' 预设
  const logger = await createLoggerWithPreset('my-service');
  
  logger.info('服务已启动', { pid: process.pid });
}

initializeLogger();
```

### API 特性

无论使用何种方式创建，`logger` 实例都拥有强大的功能：

```typescript
// 基础日志
logger.info('用户登录成功', { userId: '123' });

// 结构化上下文
const requestLogger = logger.forRequest('req-abc');
requestLogger.info('处理入站请求');

// 错误记录
try {
  // ... some code
} catch (error) {
  logger.logError(error, '处理支付时发生错误');
}
```

## 🏗️ 架构优势

使用 `@yai-nexus/loglayer-support` 意味着您的日志架构具备了：

- **可移植性**: 您的日志代码与具体实现无关，未来可以轻松迁移到任何 [LogLayer 支持的传输器](https://loglayer.dev/docs/transports)。
- **健壮性**: 自动回退机制确保了即使在最苛刻的环境下，日志功能依然可用。
- **可维护性**: 将复杂的日志系统配置和管理工作抽象掉，让您专注于业务逻辑。

## 🤝 贡献

我们欢迎任何形式的社区贡献。请在提交 Pull Request 前，确保代码通过了格式化和 lint 检查。
