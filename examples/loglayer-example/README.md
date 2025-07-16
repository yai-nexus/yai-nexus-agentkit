# LogLayer Support 示例项目

这个项目展示了 `@yai-nexus/loglayer-support` 的各种使用方法和最佳实践。

## 🎯 项目目标

- 演示 loglayer-support 的核心功能
- 提供完整的使用示例
- 展示从 pino-support 的迁移过程
- 验证各种传输器的兼容性

## 📦 安装依赖

```bash
# 在项目根目录运行
pnpm install

# 或者在当前目录运行
cd examples/loglayer-example
pnpm install
```

## 🚀 运行示例

### 基础使用示例
```bash
npm run test:basic
```
演示：
- 环境检测
- 预设配置使用
- 上下文绑定
- 增强方法
- Next.js 兼容性

### 传输器测试
```bash
npm run test:transports
```
测试：
- Console 传输器
- Winston 传输器
- Pino 传输器
- SimplePrettyTerminal 传输器
- Redaction 插件
- 性能对比

### 迁移示例
```bash
npm run test:migration
```
展示：
- 迁移前后代码对比
- API 兼容性验证
- 迁移步骤指南
- 性能和维护性对比

### 运行所有测试
```bash
npm run test:all
```

## 📁 项目结构

```
examples/loglayer-example/
├── package.json              # 项目配置
├── README.md                 # 项目文档
└── src/
    ├── basic-usage.js        # 基础使用示例
    ├── transport-tests.js    # 传输器测试
    ├── migration-example.js  # 迁移示例
    └── compatibility-tests.js # 兼容性测试
```

## 🔧 核心功能演示

### 1. 一行代码解决 Next.js 兼容性
```javascript
import { createNextjsLoggerSync } from '@yai-nexus/loglayer-support';

// 一行代码解决所有问题！
export const logger = createNextjsLoggerSync('my-app');
```

### 2. 完全兼容的 API
```javascript
// 所有原有 API 都可以直接使用
logger.info('基础日志');
logger.forRequest(requestId).info('请求日志');
logger.logError(error, context);
logger.logPerformance('operation', duration, metadata);
```

### 3. 自动传输器选择
```javascript
// 自动选择最佳传输器：Pino -> Winston -> Console
const logger = await createLoggerWithPreset('app', 'development');
```

### 4. 多种预设配置
```javascript
// 开发环境
const devLogger = await createLoggerWithPreset('app', 'development');

// 生产环境
const prodLogger = await createLoggerWithPreset('app', 'production');

// Next.js 兼容
const nextLogger = await createLoggerWithPreset('app', 'nextjsCompatible');

// 仅控制台
const consoleLogger = await createLoggerWithPreset('app', 'consoleOnly');
```

## 📊 迁移效果对比

| 指标 | 旧版 (pino-support) | 新版 (loglayer-support) | 改善 |
|------|---------------------|-------------------------|------|
| 代码行数 | 136 行 | 1 行 | **减少 99%+** |
| Next.js 兼容性 | ❌ 有问题 | ✅ 完美解决 | **彻底解决** |
| 传输器支持 | 仅 Pino | Pino/Winston/Console | **更灵活** |
| 自动回退 | ❌ 无 | ✅ 有 | **更可靠** |
| 维护复杂度 | 高 | 极低 | **大幅简化** |

## 🔍 故障排除

### 传输器依赖问题
如果某个传输器测试失败，请安装相应依赖：

```bash
# Pino 传输器
npm install @loglayer/transport-pino pino pino-pretty

# Winston 传输器
npm install @loglayer/transport-winston winston

# SimplePrettyTerminal 传输器
npm install @loglayer/transport-simple-pretty-terminal

# Redaction 插件
npm install @loglayer/plugin-redaction
```

### Next.js 兼容性问题
如果在 Next.js 环境中遇到问题，使用兼容预设：

```javascript
const logger = await createLoggerWithPreset('app', 'nextjsCompatible');
```

## 💡 最佳实践

1. **使用预设配置**：优先使用内置预设，减少配置复杂度
2. **Next.js 项目**：使用 `createNextjsLoggerSync` 获得最佳兼容性
3. **上下文绑定**：充分利用 `forRequest`、`forUser`、`forModule` 等方法
4. **错误处理**：使用 `logError` 方法记录结构化错误信息
5. **性能监控**：使用 `logPerformance` 方法记录性能指标

## 📚 相关文档

- [LogLayer 官方文档](https://loglayer.dev)
- [@yai-nexus/loglayer-support README](../../packages/loglayer-support/README.md)
- [迁移指南](./src/migration-example.js)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进示例项目！
