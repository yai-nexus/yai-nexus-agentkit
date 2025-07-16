# @yai-nexus/loglayer-support

基于 [LogLayer](https://loglayer.dev) 的统一日志解决方案，解决 Next.js 兼容性问题并提供未来保障。

## 🎯 解决的问题

- ✅ **Next.js 兼容性**：解决 `pino.multistream is not a function` 等 webpack 打包问题
- ✅ **架构解耦**：应用代码与具体日志库完全分离
- ✅ **未来保障**：可以无痛切换底层日志库
- ✅ **环境自适应**：服务器端/客户端自动选择最优传输器
- ✅ **接口兼容**：与现有 `EnhancedLogger` API 完全兼容

## 🚀 快速开始

### 安装

```bash
npm install @yai-nexus/loglayer-support loglayer
```

### 基础使用

```typescript
import { createLoggerWithPreset } from '@yai-nexus/loglayer-support';

// 使用预设快速创建 logger
const logger = await createLoggerWithPreset('my-app', 'development');

logger.info('应用启动', { version: '1.0.0' });
```

### Next.js 兼容方案

```typescript
// lib/logger.ts
import { createNextjsLoggerSync } from '@yai-nexus/loglayer-support';

// 创建 Next.js 兼容的 logger（同步 API，支持异步初始化）
export const logger = createNextjsLoggerSync('nextjs-app');

// 使用方式与原来完全一致
logger.info('Next.js 应用启动');
logger.forRequest('req123').info('处理请求');
```

## 📦 可选依赖

根据需要安装相应的传输器：

```bash
# Pino 传输器（高性能）
npm install @loglayer/transport-pino pino

# Winston 传输器（兼容性好）
npm install @loglayer/transport-winston winston

# 简单终端传输器（Next.js 兼容）
npm install @loglayer/transport-simple-pretty-terminal

# 数据脱敏插件
npm install @loglayer/plugin-redaction
```

## 🔧 API 参考

### 预设配置

- `development(serviceName)` - 开发环境预设
- `production(serviceName)` - 生产环境预设  
- `nextjsCompatible(serviceName)` - Next.js 兼容预设
- `test(serviceName)` - 测试环境预设
- `consoleOnly(serviceName)` - 仅控制台预设

### 便捷函数

- `createLoggerWithPreset(serviceName, preset)` - 使用预设创建 logger
- `createNextjsLogger(serviceName)` - 创建 Next.js 兼容 logger
- `createNextjsLoggerSync(serviceName)` - 同步创建 Next.js logger
- `detectEnvironment()` - 检测运行环境

## 🔄 迁移指南

### 从 @yai-nexus/pino-support 迁移

```typescript
// 之前
import { createEnhancedLogger, presets } from '@yai-nexus/pino-support';

const logger = await createEnhancedLogger({
  serviceName: 'my-app',
  ...presets.nextjs('../../logs')
});

// 现在
import { createNextjsLogger } from '@yai-nexus/loglayer-support';

const logger = await createNextjsLogger('my-app');
```

### 迁移效果对比

| 指标 | 迁移前 | 迁移后 | 改善 |
|------|--------|--------|------|
| 代码行数 | 50+ 行 | 3 行 | **减少 90%+** |
| 复杂度 | 高 | 低 | **大幅简化** |
| Next.js 兼容性 | 有问题 | 完美 | **彻底解决** |
| 维护成本 | 困难 | 简单 | **显著降低** |

## 🏗️ 架构优势

1. **抽象层解耦**：应用代码与日志库完全分离
2. **传输器可插拔**：运行时切换日志库，无需修改代码
3. **环境自适应**：根据运行环境自动选择最优配置
4. **兼容性隔离**：兼容性问题只影响传输器层
5. **未来保障**：LogLayer 生态系统持续演进

## 📄 许可证

MIT
