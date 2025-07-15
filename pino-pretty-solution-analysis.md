# Pino Pretty 文件输出解决方案分析

## 问题背景

在 `@yai-nexus/pino-support` 包中，我们遇到了 `pino-pretty` 格式化的问题：

- ✅ **控制台输出**：`pino-pretty` 工作正常，显示漂亮的格式化日志
- ❌ **文件输出**：始终输出 JSON 格式，`pino-pretty` 格式化不生效

### 已尝试的方法

1. **流管道方式**：`prettyTransform.pipe(fileStream)` - 失败
2. **destination 配置**：`pretty({ destination: filePath })` - 失败  
3. **worker 禁用**：各种 worker 相关配置 - 失败

根本原因可能是 `pino.multistream` 与 `pino-pretty` 的兼容性问题。

## 解决方案分析

### 方案一：轻量级自定义格式化 ⭐⭐⭐⭐⭐

**实现思路**：
不依赖 `pino-pretty`，自己实现简单的日志格式化逻辑。

```typescript
const formatLogMessage = (obj: any): string => {
  const timestamp = new Date(obj.time).toLocaleString();
  const level = obj.level === 30 ? 'INFO' : 
               obj.level === 40 ? 'WARN' : 
               obj.level === 50 ? 'ERROR' : 'DEBUG';
  
  const service = obj.service || 'unknown';
  const msg = obj.msg || '';
  
  // 提取额外字段
  const extra = { ...obj };
  delete extra.time; delete extra.level; delete extra.service; 
  delete extra.msg; delete extra.pid; delete extra.hostname;
  
  const extraStr = Object.keys(extra).length > 0 ? 
    '\n    ' + JSON.stringify(extra, null, 2).replace(/\n/g, '\n    ') : '';
  
  return `[${timestamp}] ${level}: ${msg}${extraStr}\n`;
};

// 拦截 fileStream.write
const originalWrite = fileStream.write.bind(fileStream);
fileStream.write = (chunk: any) => {
  try {
    const obj = JSON.parse(chunk.toString());
    return originalWrite(formatLogMessage(obj));
  } catch (error) {
    return originalWrite(chunk); // 降级处理
  }
};
```

**优势**：
- ✅ **简单可靠**：无外部依赖，代码易懂
- ✅ **完全可控**：格式完全自定义，想要什么样的输出都可以
- ✅ **性能优秀**：无流处理开销，直接字符串操作
- ✅ **易于调试**：出问题容易定位和修复
- ✅ **轻量级**：不增加包大小，减少依赖风险

**劣势**：
- ❌ **功能有限**：需要自己实现复杂格式化功能
- ❌ **维护成本**：需要自己维护格式化逻辑

**适用场景**：追求稳定性和可控性，对格式化需求不复杂的场景。

---

### 方案二：分离式 Pretty 流 ⭐⭐⭐⭐

**实现思路**：
不使用 `pino.multistream`，而是创建两个独立的 logger 实例。

```typescript
export async function createLogger(config: LoggerConfig): Promise<pino.Logger> {
  // 主 logger：JSON 格式到控制台
  const mainLogger = pino({
    level: config.level || "info",
    base: { service: config.serviceName, environment: env.environment },
  }, process.stdout);

  // 文件 logger：pretty 格式到文件
  if (config.file?.enabled && config.file?.pretty) {
    const { default: pretty } = await import("pino-pretty");
    const fileLogger = pino({
      level: config.level || "info", 
      base: { service: config.serviceName, environment: env.environment },
    }, pretty({
      destination: config.file.path,
      colorize: false,
      translateTime: "SYS:yyyy-mm-dd HH:MM:ss",
      ignore: "pid,hostname",
      sync: true,
    }));

    // 创建代理 logger，同时写入两个目标
    return new Proxy(mainLogger, {
      get(target, prop) {
        if (typeof target[prop] === 'function' && ['info', 'warn', 'error', 'debug'].includes(prop)) {
          return (...args) => {
            target[prop](...args);      // 控制台输出
            fileLogger[prop](...args);  // 文件输出
          };
        }
        return target[prop];
      }
    });
  }
  
  return mainLogger;
}
```

**优势**：
- ✅ **利用成熟方案**：直接使用 `pino-pretty` 的最佳实践
- ✅ **格式丰富**：支持 `pino-pretty` 的所有格式化选项
- ✅ **分离关注点**：控制台和文件输出完全独立
- ✅ **灵活配置**：可以给不同输出设置不同格式

**劣势**：
- ❌ **复杂度增加**：需要维护两个 logger 实例
- ❌ **性能开销**：每条日志需要处理两次
- ❌ **API 复杂**：Proxy 可能导致类型推断问题

**适用场景**：需要 `pino-pretty` 完整功能，且可以接受一定复杂度的场景。

---

### 方案三：后处理转换 ⭐⭐⭐

**实现思路**：
日志时写入 JSON 格式，提供工具在后台或定时任务中转换为 pretty 格式。

```typescript
// 1. 正常写入 JSON 格式
export async function createLogger(config: LoggerConfig): Promise<pino.Logger> {
  // 标准实现，文件始终 JSON 格式
  return pino(options, pino.multistream(streams));
}

// 2. 提供转换工具
export async function convertLogsToPretty(inputPath: string, outputPath: string) {
  const { default: pretty } = await import("pino-pretty");
  const fs = await import("fs");
  const readline = await import("readline");
  
  const prettyTransform = pretty({
    colorize: false,
    translateTime: "SYS:yyyy-mm-dd HH:MM:ss",
    ignore: "pid,hostname",
  });
  
  const fileStream = readline.createInterface({
    input: fs.createReadStream(inputPath),
    crlfDelay: Infinity
  });
  
  const outputStream = fs.createWriteStream(outputPath);
  
  for await (const line of fileStream) {
    if (line.trim()) {
      const formatted = await formatLine(prettyTransform, line);
      outputStream.write(formatted);
    }
  }
}

// 3. CLI 工具或脚本
// pnpm logs:prettify logs/current/app.log logs/current/app-pretty.log
```

**优势**：
- ✅ **运行时简单**：日志写入无额外开销
- ✅ **格式完整**：能使用 `pino-pretty` 的所有功能
- ✅ **按需处理**：只在需要时才进行格式化
- ✅ **灵活性高**：可以批量处理历史日志

**劣势**：
- ❌ **非实时**：无法实时查看格式化日志
- ❌ **额外步骤**：需要手动或定时执行转换
- ❌ **存储翻倍**：需要同时保存两种格式

**适用场景**：主要用于日志分析和调试，不需要实时 pretty 格式的场景。

## 推荐方案

### 🥇 首选：方案一（轻量级自定义格式化）

**理由**：
1. **最稳定**：无外部依赖，不会因为 `pino-pretty` 版本更新而出问题
2. **最简单**：代码逻辑清晰，维护成本低
3. **最高效**：性能最优，无额外开销
4. **最灵活**：可以根据具体需求定制格式

### 🥈 备选：方案二（分离式 Pretty 流）

**适用于**：
- 确实需要 `pino-pretty` 的高级格式化功能
- 团队对代码复杂度接受度较高
- 性能要求不是特别严格

### 🥉 特殊场景：方案三（后处理转换）

**适用于**：
- 主要用于日志分析和调试
- 对实时性要求不高
- 希望保持运行时的最佳性能

## 实施建议

1. **立即实施方案一**：作为默认实现，确保基本功能可用
2. **保留 pretty 选项**：在配置中保留 `file.pretty` 选项，为将来切换做准备
3. **添加格式配置**：允许用户自定义日志格式模板
4. **提供工具函数**：如果有需要，后续可以添加方案三的转换工具

## 代码示例

完整的方案一实现见附录代码片段，可以直接替换现有实现。

---

*文档生成时间：2025-07-15*  
*问题分析：pino-pretty 在 multistream 环境下的文件输出兼容性问题*