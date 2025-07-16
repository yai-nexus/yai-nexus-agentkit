# Next.js 环境下的 Logger 解决方案设计

## 📋 问题背景

当前项目在集成 Pino 与 Next.js 时遇到兼容性问题：

- **核心问题**：`pino.multistream is not a function`
- **根本原因**：Next.js webpack 配置与 Pino 的 Node.js 原生模块依赖不兼容
- **影响范围**：无法在 Next.js 环境中正常使用 @yai-nexus/pino-support

## 🎯 设计目标

1. **完全兼容 Next.js**：无 webpack 打包问题
2. **统一日志接口**：服务器端和客户端一致的 API
3. **性能优秀**：低开销，适合生产环境
4. **易于集成**：与现有 fekit 等组件无缝集成
5. **功能完整**：支持结构化日志、上下文绑定、多级别输出

## 🔍 方案对比

### 方案 A：next-logger

#### 设计思路
使用专为 Next.js 设计的轻量级日志库，避免 Node.js 模块兼容性问题。

#### 实现方案
```typescript
// 安装依赖
// npm install next-logger

// lib/logger.ts
import { createLogger } from 'next-logger';

export const logger = createLogger({
  level: process.env.NODE_ENV === 'development' ? 'debug' : 'info',
  format: 'json',
  transports: {
    console: true,
    file: process.env.NODE_ENV === 'production' ? 'logs/app.log' : false,
  },
});

// 使用示例
logger.info('API request processed', { 
  endpoint: '/api/data',
  duration: 150,
  userId: 'user123'
});
```

#### 优势
- ✅ **零配置兼容**：专为 Next.js 设计，无 webpack 问题
- ✅ **轻量级**：包体积小，性能开销低
- ✅ **简单易用**：API 简洁，学习成本低
- ✅ **环境自适应**：自动处理服务器端/客户端差异

#### 劣势
- ❌ **功能有限**：相比 Pino 功能较少
- ❌ **生态较小**：社区支持和插件生态不如主流方案
- ❌ **定制性差**：高级功能支持有限

#### 风险评估
- **低风险**：专门为 Next.js 设计，兼容性有保障

---

### 方案 B：winston

#### 设计思路
使用 Winston 作为底层日志引擎，通过条件导入和环境检测避免 Next.js 兼容性问题。

#### 实现方案
```typescript
// 安装依赖
// npm install winston

// lib/logger.ts
import winston from 'winston';

// 环境感知的传输配置
const transports: winston.transport[] = [
  new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  })
];

// 仅在服务器端添加文件传输
if (typeof window === 'undefined' && process.env.NODE_ENV === 'production') {
  transports.push(
    new winston.transports.File({ 
      filename: 'logs/error.log', 
      level: 'error' 
    }),
    new winston.transports.File({ 
      filename: 'logs/combined.log' 
    })
  );
}

export const logger = winston.createLogger({
  level: process.env.NODE_ENV === 'development' ? 'debug' : 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports,
});

// 增强接口，兼容现有代码
export interface EnhancedWinstonLogger extends winston.Logger {
  child(bindings: Record<string, any>): EnhancedWinstonLogger;
  forRequest(requestId: string, traceId?: string): EnhancedWinstonLogger;
  raw: winston.Logger;
}

function createEnhancedLogger(baseLogger: winston.Logger): EnhancedWinstonLogger {
  const enhanced = baseLogger as EnhancedWinstonLogger;
  
  enhanced.child = (bindings: Record<string, any>) => {
    return createEnhancedLogger(baseLogger.child(bindings));
  };
  
  enhanced.forRequest = (requestId: string, traceId?: string) => {
    const context = { requestId, ...(traceId && { traceId }) };
    return enhanced.child(context);
  };
  
  enhanced.raw = baseLogger;
  
  return enhanced;
}

export const enhancedLogger = createEnhancedLogger(logger);
```

#### 优势
- ✅ **功能丰富**：支持多种传输方式、格式化、过滤等
- ✅ **生态成熟**：大量插件和社区支持
- ✅ **高度可配置**：可以精确控制日志行为
- ✅ **兼容性好**：通过条件导入避免 Next.js 问题

#### 劣势
- ❌ **配置复杂**：需要处理环境差异和条件导入
- ❌ **包体积大**：相比轻量级方案体积较大
- ❌ **性能开销**：功能丰富带来的性能成本

#### 风险评估
- **中等风险**：需要正确处理环境检测，但 Winston 本身稳定可靠

---

### 方案 C：loglevel + 自定义增强

#### 设计思路
使用超轻量级的 loglevel 作为基础，自定义增强功能以满足项目需求。

#### 实现方案
```typescript
// 安装依赖
// npm install loglevel

// lib/logger.ts
import log from 'loglevel';

// 设置日志级别
log.setLevel(process.env.NODE_ENV === 'production' ? 'warn' : 'debug');

// 自定义增强包装器
class NextJSLogger {
  private context: Record<string, any> = {};
  
  constructor(private baseLogger = log) {}
  
  private formatMessage(level: string, message: string, data?: Record<string, any>) {
    const entry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      ...this.context,
      ...data
    };
    
    // 服务器端：结构化输出
    if (typeof window === 'undefined') {
      return JSON.stringify(entry);
    }
    
    // 客户端：友好格式
    return `[${entry.timestamp}] ${level.toUpperCase()}: ${message}`;
  }
  
  debug(message: string, data?: Record<string, any>) {
    const formatted = this.formatMessage('debug', message, data);
    this.baseLogger.debug(formatted);
  }
  
  info(message: string, data?: Record<string, any>) {
    const formatted = this.formatMessage('info', message, data);
    this.baseLogger.info(formatted);
  }
  
  warn(message: string, data?: Record<string, any>) {
    const formatted = this.formatMessage('warn', message, data);
    this.baseLogger.warn(formatted);
  }
  
  error(message: string, data?: Record<string, any>) {
    const formatted = this.formatMessage('error', message, data);
    this.baseLogger.error(formatted);
  }
  
  child(bindings: Record<string, any>): NextJSLogger {
    const childLogger = new NextJSLogger(this.baseLogger);
    childLogger.context = { ...this.context, ...bindings };
    return childLogger;
  }
  
  forRequest(requestId: string, traceId?: string): NextJSLogger {
    const context = { requestId, ...(traceId && { traceId }) };
    return this.child(context);
  }
  
  get raw() {
    return this.baseLogger;
  }
}

export const logger = new NextJSLogger();
```

#### 优势
- ✅ **超轻量级**：loglevel 仅 2KB，几乎无性能开销
- ✅ **完全兼容**：无任何 Node.js 依赖，完美支持 Next.js
- ✅ **高度定制**：可以根据项目需求精确定制功能
- ✅ **渐进增强**：可以逐步添加需要的功能

#### 劣势
- ❌ **需要自实现**：高级功能需要自己开发
- ❌ **维护成本**：自定义代码需要持续维护
- ❌ **功能有限**：基础功能相对简单

#### 风险评估
- **低风险**：loglevel 非常稳定，自定义部分可控

---

### 方案 D：Vercel 原生日志 + 增强

#### 设计思路
利用 Vercel 平台的原生日志收集能力，通过增强 console 对象提供结构化日志。

#### 实现方案
```typescript
// lib/logger.ts
interface LogEntry {
  level: string;
  message: string;
  timestamp: string;
  service: string;
  [key: string]: any;
}

class VercelLogger {
  private context: Record<string, any> = {};
  
  constructor(private serviceName: string = 'nextjs-app') {}
  
  private log(level: keyof Console, message: string, data?: Record<string, any>) {
    const entry: LogEntry = {
      level: level.toString(),
      message,
      timestamp: new Date().toISOString(),
      service: this.serviceName,
      ...this.context,
      ...data
    };
    
    // Vercel 自动收集 console 输出
    console[level](JSON.stringify(entry));
    
    return entry;
  }
  
  debug(message: string, data?: Record<string, any>) {
    return this.log('debug', message, data);
  }
  
  info(message: string, data?: Record<string, any>) {
    return this.log('info', message, data);
  }
  
  warn(message: string, data?: Record<string, any>) {
    return this.log('warn', message, data);
  }
  
  error(message: string, data?: Record<string, any>) {
    return this.log('error', message, data);
  }
  
  child(bindings: Record<string, any>): VercelLogger {
    const childLogger = new VercelLogger(this.serviceName);
    childLogger.context = { ...this.context, ...bindings };
    return childLogger;
  }
  
  forRequest(requestId: string, traceId?: string): VercelLogger {
    const context = { requestId, ...(traceId && { traceId }) };
    return this.child(context);
  }
  
  get raw() {
    return console;
  }
}

export const logger = new VercelLogger();
```

#### 优势
- ✅ **零配置**：无需额外设置，Vercel 自动收集
- ✅ **完美集成**：与 Vercel 控制台无缝集成
- ✅ **无兼容性问题**：基于标准 console API
- ✅ **实时监控**：可在 Vercel 控制台实时查看日志

#### 劣势
- ❌ **平台绑定**：仅适用于 Vercel 部署
- ❌ **功能有限**：依赖 Vercel 平台的日志功能
- ❌ **本地开发体验**：本地开发时功能受限

#### 风险评估
- **低风险**：如果确定使用 Vercel 部署，这是最简单的方案

---

### 方案 E：next-axiom

#### 设计思路
使用 Axiom 提供的 Next.js 专用日志解决方案，获得企业级日志管理能力。

#### 实现方案
```typescript
// 安装依赖
// npm install next-axiom

// next.config.js
const { withAxiom } = require('next-axiom');

module.exports = withAxiom({
  // 其他 Next.js 配置
});

// lib/logger.ts
import { log } from 'next-axiom';

// 创建增强包装器以兼容现有接口
class AxiomLogger {
  private context: Record<string, any> = {};
  
  debug(message: string, data?: Record<string, any>) {
    log.debug(message, { ...this.context, ...data });
  }
  
  info(message: string, data?: Record<string, any>) {
    log.info(message, { ...this.context, ...data });
  }
  
  warn(message: string, data?: Record<string, any>) {
    log.warn(message, { ...this.context, ...data });
  }
  
  error(message: string, data?: Record<string, any>) {
    log.error(message, { ...this.context, ...data });
  }
  
  child(bindings: Record<string, any>): AxiomLogger {
    const childLogger = new AxiomLogger();
    childLogger.context = { ...this.context, ...bindings };
    return childLogger;
  }
  
  forRequest(requestId: string, traceId?: string): AxiomLogger {
    const context = { requestId, ...(traceId && { traceId }) };
    return this.child(context);
  }
  
  get raw() {
    return log;
  }
}

export const logger = new AxiomLogger();
```

#### 优势
- ✅ **企业级功能**：强大的查询、分析、告警功能
- ✅ **Next.js 优化**：专门为 Next.js 优化的集成
- ✅ **实时监控**：实时日志流和仪表板
- ✅ **高性能**：优化的日志传输和存储

#### 劣势
- ❌ **成本考虑**：企业级服务可能有成本
- ❌ **外部依赖**：依赖第三方服务
- ❌ **配置复杂**：需要额外的配置和账户设置

#### 风险评估
- **中等风险**：依赖外部服务，但 Axiom 是可靠的企业级解决方案

---

### 方案 F：日志抽象层 (LogLayer)

#### 设计思路
引入日志门面（Logging Facade）或抽象层，通过统一接口解耦应用逻辑与具体日志库实现，实现可插拔的传输器架构。

#### 实现方案
```typescript
// 安装依赖
// npm install @loglayer/core @loglayer/transport-pino @loglayer/transport-winston

// lib/logger-config.ts
import { LogLayer } from '@loglayer/core';

// 环境感知的传输器配置
function createLoggerConfig() {
  const isServer = typeof window === 'undefined';
  const isDev = process.env.NODE_ENV === 'development';

  if (isServer) {
    // 服务器端：使用高性能的 Pino 或 Winston
    if (isDev) {
      return {
        transport: '@loglayer/transport-winston',
        config: {
          level: 'debug',
          format: 'pretty',
          transports: ['console']
        }
      };
    } else {
      return {
        transport: '@loglayer/transport-pino',
        config: {
          level: 'info',
          streams: [
            { stream: process.stdout },
            { stream: 'logs/app.log' }
          ]
        }
      };
    }
  } else {
    // 客户端：使用轻量级传输器
    return {
      transport: '@loglayer/transport-console',
      config: {
        level: isDev ? 'debug' : 'warn',
        format: 'simple'
      }
    };
  }
}

// lib/logger.ts
import { LogLayer } from '@loglayer/core';

class UnifiedLogger {
  private logLayer: LogLayer;
  private context: Record<string, any> = {};

  constructor() {
    const config = createLoggerConfig();
    this.logLayer = new LogLayer(config);
  }

  debug(message: string, data?: Record<string, any>) {
    this.logLayer.withMetadata({ ...this.context, ...data }).debug(message);
  }

  info(message: string, data?: Record<string, any>) {
    this.logLayer.withMetadata({ ...this.context, ...data }).info(message);
  }

  warn(message: string, data?: Record<string, any>) {
    this.logLayer.withMetadata({ ...this.context, ...data }).warn(message);
  }

  error(message: string, data?: Record<string, any>) {
    this.logLayer.withMetadata({ ...this.context, ...data }).error(message);
  }

  child(bindings: Record<string, any>): UnifiedLogger {
    const childLogger = new UnifiedLogger();
    childLogger.context = { ...this.context, ...bindings };
    childLogger.logLayer = this.logLayer;
    return childLogger;
  }

  forRequest(requestId: string, traceId?: string): UnifiedLogger {
    const context = { requestId, ...(traceId && { traceId }) };
    return this.child(context);
  }

  // 切换底层传输器（运行时配置）
  switchTransport(transportConfig: any) {
    this.logLayer.configure(transportConfig);
  }

  get raw() {
    return this.logLayer.getUnderlyingLogger();
  }
}

export const logger = new UnifiedLogger();

// 使用示例 - 应用代码完全解耦
logger.withMetadata({ userId: 'user123' }).info('User action performed');
```

#### 高级配置示例
```typescript
// config/logger-transports.ts
export const loggerTransports = {
  development: {
    server: {
      transport: '@loglayer/transport-winston',
      config: {
        level: 'debug',
        format: 'pretty',
        transports: ['console', 'file']
      }
    },
    client: {
      transport: '@loglayer/transport-console',
      config: { level: 'debug', format: 'colorized' }
    }
  },

  production: {
    server: {
      transport: '@loglayer/transport-pino',
      config: {
        level: 'info',
        streams: [
          { stream: process.stdout },
          { stream: 'logs/app.log' },
          { stream: 'logs/error.log', level: 'error' }
        ]
      }
    },
    client: {
      transport: '@loglayer/transport-remote',
      config: {
        endpoint: '/api/logs',
        batchSize: 10,
        flushInterval: 5000
      }
    }
  },

  // 解决 Next.js 兼容性问题的配置
  nextjs_compatible: {
    server: {
      transport: '@loglayer/transport-winston', // 避免 Pino 的 webpack 问题
      config: {
        level: 'info',
        format: 'json',
        transports: ['console']
      }
    },
    client: {
      transport: '@loglayer/transport-console',
      config: { level: 'warn' }
    }
  }
};

// 动态配置切换
export function getLoggerConfig() {
  const env = process.env.NODE_ENV;
  const hasNextjsIssues = process.env.NEXTJS_LOGGER_COMPAT === 'true';

  if (hasNextjsIssues) {
    return loggerTransports.nextjs_compatible;
  }

  return loggerTransports[env] || loggerTransports.development;
}
```

#### 优势
- ✅ **架构解耦**：应用代码与具体日志库完全解耦
- ✅ **未来保障**：可以无痛切换底层日志库
- ✅ **环境适配**：服务器端/客户端自动使用最优传输器
- ✅ **配置灵活**：运行时可切换日志策略
- ✅ **问题隔离**：兼容性问题只影响传输器层，不影响应用代码
- ✅ **最佳实践**：结合各种日志库的优势
- ✅ **渐进迁移**：可以逐步替换传输器而不影响业务代码

#### 劣势
- ❌ **抽象开销**：引入额外的抽象层，轻微的性能开销
- ❌ **学习成本**：需要理解抽象层的概念和配置
- ❌ **依赖复杂**：需要管理多个传输器包
- ❌ **调试复杂**：问题可能出现在抽象层或传输器层

#### 风险评估
- **低风险**：抽象层模式是成熟的架构模式，LogLayer 等库经过实战验证

#### 解决原始问题的方式
```typescript
// 当遇到 Pino 兼容性问题时，解决方案仅仅是配置切换：

// 之前的配置
const config = {
  transport: '@loglayer/transport-pino',  // 有 Next.js 兼容性问题
  config: { /* pino 配置 */ }
};

// 解决方案：切换传输器
const config = {
  transport: '@loglayer/transport-winston', // 兼容 Next.js
  config: { /* winston 配置 */ }
};

// 应用代码完全不需要修改！
logger.info('This works the same way', { data: 'unchanged' });
```

## 📊 方案对比总结

| 方案 | Next.js 兼容性 | 功能丰富度 | 配置复杂度 | 性能 | 成本 | 未来保障 | 推荐度 |
|------|--------------|-----------|-----------|------|------|---------|--------|
| **A: next-logger** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | 免费 | ⭐⭐ | ⭐⭐⭐⭐ |
| **B: winston** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 免费 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **C: loglevel+** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | 免费 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **D: Vercel 原生** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | 免费 | ⭐⭐ | ⭐⭐⭐ |
| **E: next-axiom** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | 付费 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **F: LogLayer** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 免费 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🎯 推荐方案

### 🏆 战略推荐：方案 F (LogLayer 抽象层)

**理由：**
1. **架构优越性**：从根本上解决日志库选型和兼容性问题
2. **未来保障**：技术栈演进时无需重构应用代码
3. **问题隔离**：Next.js 兼容性问题只需切换传输器配置
4. **最佳实践**：结合各种日志库的优势，环境自适应
5. **战略价值**：适合大型、长期维护的项目

**适用场景：**
- 企业级项目或长期维护的项目
- 需要在多种环境（开发/测试/生产）中部署
- 团队希望避免技术债务和未来重构风险
- 对日志系统有较高要求的项目

### 🥈 实用推荐：方案 C (loglevel + 自定义增强)

**理由：**
1. **完美兼容**：零 Next.js 兼容性问题
2. **性能最优**：超轻量级，几乎无性能开销
3. **高度可控**：可以精确实现项目需要的功能
4. **渐进演进**：可以根据需求逐步增强功能
5. **成本最低**：无外部依赖，完全免费

**适用场景：**
- 中小型项目或快速原型
- 团队希望完全控制日志实现
- 对性能有极致要求的项目
- 预算有限的项目

### 🥉 快速方案：方案 A (next-logger)

**适用场景：**
- 希望快速解决问题，不想自己实现增强功能
- 对日志功能要求不高的项目
- 团队更偏好使用现成的库

## 🚀 实施计划

### 方案 F (LogLayer) 实施计划

#### 阶段 1：抽象层搭建 (2-3 天)
1. 安装 LogLayer 核心包和传输器
2. 设计统一的 logger 接口
3. 实现环境感知的传输器配置
4. 创建基础的抽象层包装

#### 阶段 2：传输器配置 (2-3 天)
1. 配置服务器端传输器（Winston/Pino）
2. 配置客户端传输器（Console/Remote）
3. 实现 Next.js 兼容性配置
4. 测试传输器切换功能

#### 阶段 3：应用集成 (2-3 天)
1. 替换现有的 pino 调用为抽象接口
2. 集成到 fekit 等组件
3. 实现上下文绑定和请求追踪
4. 优化配置和性能

#### 阶段 4：验证和优化 (1-2 天)
1. 全面测试各种环境配置
2. 性能基准测试
3. 生产环境验证
4. 文档和最佳实践整理

### 方案 C (loglevel+) 快速实施计划

#### 阶段 1：基础替换 (1-2 天)
1. 安装 loglevel 依赖
2. 实现自定义增强包装器
3. 替换现有的 pino 调用
4. 验证基本功能

#### 阶段 2：功能增强 (2-3 天)
1. 实现 child logger 和上下文绑定
2. 添加请求追踪功能
3. 优化日志格式和输出
4. 集成到 fekit 等组件

#### 阶段 3：测试验证 (1-2 天)
1. 单元测试和集成测试
2. 性能测试和压力测试
3. 生产环境验证
4. 文档更新

### 风险缓解策略
- **回滚计划**：保留当前 pino 配置作为备份
- **渐进迁移**：先在非关键路径测试新方案
- **监控验证**：密切监控迁移后的系统表现
- **A/B 测试**：在方案 F 和方案 C 之间进行小规模对比测试

## 📝 结论

### 战略建议

对于**企业级或长期维护的项目**，强烈推荐采用**方案 F (LogLayer 抽象层)**。这是一个架构上更优越的解决方案，它不仅能解决当前的 Next.js 兼容性问题，更重要的是为项目提供了强大的未来保障能力。当遇到类似的技术栈兼容性问题时，解决方案仅仅是配置文件的修改，而非代码重构。

### 实用建议

对于**中小型项目或快速原型**，**方案 C (loglevel + 自定义增强)** 仍然是一个优秀的选择。它在兼容性、性能、可控性方面都表现优秀，能够完美解决当前的 Next.js 兼容性问题，同时保持最小的复杂度。

### 决策矩阵

- **选择方案 F**：如果项目预期长期维护、团队规模较大、对架构质量有高要求
- **选择方案 C**：如果项目周期较短、团队偏好轻量级方案、对性能有极致要求
- **选择方案 A**：如果希望快速解决问题、对日志功能要求不高

技术顾问的反馈揭示了一个重要的架构原则：**通过抽象层解耦是解决技术选型和兼容性问题的根本之道**。这种模式不仅适用于日志系统，也适用于数据库、缓存、消息队列等基础设施组件的选型。
