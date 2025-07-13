# AliyunSlsSink 的优雅生命周期管理建议

在实际生产环境中，推荐采用如下更优雅的生命周期管理方式，避免自动启动和混淆同步/异步接口：

## 1. 不自动 create_task，由用户手动控制启动/关闭

AliyunSlsSink 不应在 `__init__` 中自动启动，而是由用户根据实际场景手动调用 `await sink.async_start()` 和 `await sink.async_close()`。

## 2. 区分异步和同步关闭接口

- `async def async_start()` / `async def async_close()`：推荐在异步环境下直接 await 管理 sink 生命周期。
- `async def __aenter__()` / `async def __aexit__()`：支持异步上下文管理器，自动管理资源生命周期。
- `def stop()`：提供同步关闭包装器，专为 loguru 的 `logger.remove(sink)` 场景设计，命名更具语义性，便于理解和维护。

## 3. 推荐用法示例

### 纯异步场景（如 FastAPI、异步脚本）

```python
from yai_loguru_support.sls import AliyunSlsSink, SlsConfig
from loguru import logger
import asyncio

async def main():
    config = SlsConfig(
        endpoint="cn-hangzhou.log.aliyuncs.com",
        access_key_id="your_key_id",
        access_key="your_key",
        project="your_project",
        logstore="your_logstore"
    )
    sls_sink = AliyunSlsSink(config)
    await sls_sink.async_start()
    logger.add(sls_sink, serialize=True, level="INFO")
    logger.info("Hello SLS!")
    await sls_sink.async_close()

asyncio.run(main())
```

### 异步上下文管理器（推荐方式）

```python
from yai_loguru_support.sls import AliyunSlsSink, SlsConfig
from loguru import logger
import asyncio

async def main():
    config = SlsConfig(
        endpoint="cn-hangzhou.log.aliyuncs.com",
        access_key_id="your_key_id",
        access_key="your_key",
        project="your_project",
        logstore="your_logstore"
    )
    
    # 使用异步上下文管理器自动管理生命周期
    async with AliyunSlsSink(config) as sls_sink:
        logger.add(sls_sink, serialize=True, level="INFO")
        logger.info("Hello SLS!")
        # 自动调用 async_close()

asyncio.run(main())
```

### 兼容 loguru 的同步关闭（如 logger.remove）

```python
from yai_loguru_support.sls import AliyunSlsSink, SlsConfig
from loguru import logger

config = SlsConfig(...)
sls_sink = AliyunSlsSink(config)
logger.add(sls_sink, serialize=True, level="INFO")
# ... 日志使用 ...
logger.remove()  # loguru 会自动调用 sls_sink.stop()
```

### AliyunSlsSink 推荐实现片段

```python
class AliyunSlsSink(BaseSink):
    async def async_start(self):
        """异步启动 sink"""
        await self.start()
    
    async def async_close(self):
        """异步关闭 sink"""
        await self.stop()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.async_start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.async_close()
    
    def stop(self):
        """兼容 loguru 的同步关闭（logger.remove 时自动调用）"""
        try:
            loop = asyncio.get_running_loop()
            # 创建后台任务并保存引用防止被垃圾回收
            self._cleanup_task = loop.create_task(self.async_close())
        except RuntimeError:
            # 没有运行中的事件循环，直接运行
            asyncio.run(self.async_close())
```

## 4. 说明

- 推荐在异步框架下直接 await 管理 sink 生命周期，分别调用 `async_start()` 和 `async_close()`，避免自动 create_task。
- 优先使用异步上下文管理器 `async with AliyunSlsSink(...) as sink:` 进行自动资源管理。
- 仅在 loguru 需要同步关闭 sink 时，调用 `stop()`。
- `async_start`/`async_close` 命名对称、语义清晰，符合 Python 异步资源管理习惯。
- 文档和注释中应明确区分同步/异步接口，提升可维护性和可读性。 