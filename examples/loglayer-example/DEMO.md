# LogLayer Support 演示指南

这是一个完整的演示项目，展示了 `@yai-nexus/loglayer-support` 如何解决 Next.js 日志兼容性问题，并提供了从 `@yai-nexus/pino-support` 的完整迁移方案。

## 🎯 演示亮点

### 1. 代码量减少 99%+

**迁移前** (136 行复杂代码)：
```typescript
// 复杂的异步初始化、代理对象、错误处理...
let globalLogger: EnhancedLogger | null = null;
let initPromise: Promise<EnhancedLogger> | null = null;

async function initLogger(): Promise<EnhancedLogger> {
  // ... 130+ 行复杂逻辑
}

function createLoggerProxy(): EnhancedLogger {
  // ... 复杂的代理实现
}

export const logger = createLoggerProxy();
```

**迁移后** (1 行代码)：
```typescript
import { createNextjsLoggerSync } from '@yai-nexus/loglayer-support';

export const logger = createNextjsLoggerSync('nextjs-app');
```

### 2. 完全解决 Next.js 兼容性问题

- ✅ 自动检测 Next.js 环境
- ✅ 自动选择兼容的传输器 (Winston/Console)
- ✅ 自动回退机制，确保日志系统稳定
- ✅ 零配置，开箱即用

### 3. API 100% 向后兼容

所有原有的 API 调用都可以直接使用：
```typescript
// 基础日志
logger.info('消息', metadata);

// 上下文绑定
logger.forRequest(requestId).info('请求日志');
logger.forUser(userId).info('用户日志');
logger.forModule(moduleName).info('模块日志');

// 增强方法
logger.logError(error, context);
logger.logPerformance('operation', duration, metadata);
```

## 🚀 快速演示

### 运行基础示例
```bash
cd examples/loglayer-example
npm run test:basic
```

**演示内容**：
- 环境自动检测
- 多种预设配置
- 上下文绑定功能
- 增强日志方法
- Next.js 兼容性

### 运行传输器测试
```bash
npm run test:transports
```

**演示内容**：
- Console 传输器
- Winston 传输器
- Pino 传输器
- SimplePrettyTerminal 传输器
- Redaction 数据脱敏插件
- 性能对比测试

### 运行迁移示例
```bash
npm run test:migration
```

**演示内容**：
- 迁移前后代码对比
- API 兼容性验证
- 详细迁移步骤
- 性能和维护性对比

## 📊 核心优势对比

| 指标 | 旧版 (pino-support) | 新版 (loglayer-support) | 改善 |
|------|---------------------|-------------------------|------|
| **代码行数** | 136 行 | 1 行 | **减少 99%+** |
| **Next.js 兼容性** | ❌ 有问题 | ✅ 完美解决 | **彻底解决** |
| **传输器支持** | 仅 Pino | Pino/Winston/Console | **更灵活** |
| **自动回退** | ❌ 无 | ✅ 有 | **更可靠** |
| **维护复杂度** | 高 | 极低 | **大幅简化** |
| **API 兼容性** | N/A | 100% 兼容 | **无缝迁移** |
| **错误处理** | 复杂 | 自动化 | **更健壮** |
| **配置复杂度** | 高 | 零配置 | **极简化** |

## 🔧 技术架构

### 抽象层设计
```
应用代码
    ↓
LogLayer 抽象层
    ↓
可插拔传输器 (Pino/Winston/Console)
```

### 自动回退机制
```
Next.js 环境检测
    ↓
尝试 Pino 传输器
    ↓ (失败)
回退到 Winston 传输器
    ↓ (失败)
回退到 Console 传输器
```

## 💡 最佳实践演示

### 1. Next.js 项目推荐用法
```typescript
import { createNextjsLoggerSync } from '@yai-nexus/loglayer-support';

export const logger = createNextjsLoggerSync('my-nextjs-app');
```

### 2. 通用项目用法
```typescript
import { createLoggerWithPreset } from '@yai-nexus/loglayer-support';

const logger = await createLoggerWithPreset('my-app', 'development');
```

### 3. 自定义配置
```typescript
import { createEnhancedLogger, presets } from '@yai-nexus/loglayer-support';

const config = presets.nextjsCompatible('my-app');
const logger = await createEnhancedLogger(config);
```

## 🎉 演示总结

这个示例项目成功展示了：

1. **问题解决**：彻底解决了 Next.js webpack 兼容性问题
2. **代码简化**：从 136 行复杂逻辑简化为 1 行代码
3. **架构优越**：基于 LogLayer 的抽象层设计，可插拔传输器
4. **完全兼容**：API 100% 向后兼容，无需修改业务代码
5. **未来保障**：基于成熟的 LogLayer 生态系统

### 关键价值
- **开发效率**：大幅减少日志系统的开发和维护工作
- **系统稳定性**：自动回退机制确保日志系统始终可用
- **技术债务**：消除了复杂的日志初始化逻辑
- **团队协作**：统一的日志接口，降低学习成本

这个项目为日志系统的现代化改造提供了完整的解决方案和最佳实践！
