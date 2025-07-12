# `yai-loguru-support` 扩展包设计方案

## 1. 目的与定位

为了使核心的 `agentkit` 保持轻量和通用，同时满足向特定云服务（如阿里云日志服务 SLS）上报日志的生产环境需求，我们提议创建一个新的、独立的 Python 包，专门用于桥接 `loguru` 和各种第三方服务。

-   **包名**: `yai-loguru-support`
-   **定位**: 一个 `loguru` 的“插件”或“扩展”集合，为 `loguru` 提供连接到不同外部系统的 Sink（接收器）。它本身不处理业务逻辑，只专注于日志的可靠投递。
-   **层级**: 在 Monorepo 中，它将与 `agentkit` 和 `fekit` 平级，位于 `packages/` 目录下。

## 2. 核心优势

将此功能独立成包，具有以下显著优势：

1.  **高内聚，低耦合**: `agentkit` 核心不依赖任何特定的云服务 SDK，仅依赖 `loguru`。`yai-loguru-support` 则专门负责处理与外部服务对接的逻辑。
2.  **独立发布与复用**: `yai-loguru-support` 可以独立打包、发布和版本控制，未来可被公司内任何其他使用 `loguru` 的 Python 项目复用。
3.  **依赖隔离**: `aliyun-log-python-sdk` 等重量级或特定平台的依赖将被隔离在此包内，避免“污染”核心的 `agentkit`。
4.  **清晰的架构**: 应用层（如 `examples/python-backend`）的日志配置逻辑变得非常清晰：配置 `loguru`，然后从 `yai-loguru-support` 导入并添加所需的 Sink。
5.  **易于测试与维护**: 可以为此包编写独立的单元测试和集成测试，确保其与外部服务的连接稳定可靠。

## 3. 设计与实现

### 3.1. 项目结构

新包将遵循标准的 Python 项目布局：

```
/ (monorepo 根目录)
├── packages/
│   ├── agentkit/
│   ├── fekit/
│   └── loguru-support/  # <--- 新包
│       ├── pyproject.toml
│       ├── src/
│       │   └── loguru_support/
│       │       ├── __init__.py
│       │       └── sls/             # 按服务划分模块
│       │           ├── __init__.py
│       │           └── sink.py      # AliyunSlsSink 的实现
│       └── README.md
└── ...
```

**说明**:
- 在 `loguru_support` 内部，我们将按目标服务创建子模块（如 `sls`）。这样设计有很好的扩展性，未来若要支持如 `Datadog` 或 `Sentry`，只需新增 `datadog/` 或 `sentry/` 模块即可。

### 3.2. `pyproject.toml`

```toml
[project]
name = "yai-loguru-support"
version = "0.1.0"
description = "A collection of Loguru sinks for integrating with third-party services like Aliyun SLS."
dependencies = [
    "loguru>=0.7.0",
    "aliyun-log-python-sdk>=0.7.8"  # 阿里云官方 SDK
]
```

### 3.3. `AliyunSlsSink` 实现

文件路径: `packages/loguru-support/src/loguru_support/sls/sink.py`

核心思路是创建一个类 `AliyunSlsSink`，它在内部实例化并持有一个阿里云官方的 `QueuedLogHandler`。这个类的实例可以被用作 `loguru` 的 Sink。

```python
# src/loguru_support/sls/sink.py (概念代码)
import logging
from loguru import logger
from aliyun.log import QueuedLogHandler

class AliyunSlsSink:
    """
    A Loguru sink that sends logs to Aliyun Log Service (SLS).
    It uses the official aliyun-log-python-sdk's QueuedLogHandler for
    asynchronous, batched log shipping.
    """
    def __init__(self, endpoint: str, access_key_id: str, access_key: str, project: str, logstore: str):
        # 1. 配置阿里云官方的 Handler
        self.handler = QueuedLogHandler(
            endpoint, access_key_id, access_key, project, logstore,
            # 可配置更多高级选项，如 io_thread_count, send_interval_seconds 等
        )

        # 2. 创建一个临时的、仅用于转发的标准库 logger
        #    这个 logger 不会向上传播日志 (propagate=False)
        self.forwarder = logging.getLogger('loguru_support.sls_forwarder')
        self.forwarder.propagate = False
        self.forwarder.addHandler(self.handler)
        self.forwarder.setLevel(logging.DEBUG) # 接收所有级别的日志

    def write(self, message):
        """
        This method is called by Loguru for each log record.
        """
        # 从 Loguru 的 record 中提取信息，构建一个标准库的 LogRecord
        log_record = message.record
        
        # 将结构化的 extra 数据转换为字符串，以便发送
        # SLS Handler 会处理 LogRecord 的 msg 字段
        # 我们需要确保所有上下文信息都在里面
        # Loguru 的 `serialize=True` 会将 record 变成一个 JSON 字符串
        # 这正是我们需要的
        
        std_log_record = logging.LogRecord(
            name=log_record["name"],
            level=log_record["level"].no,
            pathname=log_record["file"].path,
            lineno=log_record["line"],
            msg=message.strip(),  # 传递序列化后的 JSON 字符串
            args=(),
            exc_info=log_record["exception"],
            func=log_record["function"],
        )
        
        # 3. 使用转发器来处理记录，这将自动调用 QueuedLogHandler
        self.forwarder.handle(std_log_record)

    def stop(self):
        """
        Ensures all buffered logs are sent before application exit.
        Call this method during a graceful shutdown.
        """
        self.handler.close()

```

### 3.4. 导出与使用

-   **`__init__.py`**
    ```python
    # src/loguru_support/__init__.py
    from .sls.sink import AliyunSlsSink
    
    __all__ = ["AliyunSlsSink"]
    ```

-   **在应用中使用**:
    ```python
    # examples/python-backend/main.py (或任何应用入口)
    import os
    from loguru import logger
    from loguru_support import AliyunSlsSink
    
    # ... 其他配置 ...
    
    # 如果是生产环境，则添加 Aliyun SLS Sink
    if os.getenv("ENV") == "production":
        sls_sink = AliyunSlsSink(
            endpoint=os.environ['SLS_ENDPOINT'],
            access_key_id=os.environ['SLS_AK_ID'],
            access_key=os.environ['SLS_AK_KEY'],
            project=os.environ['SLS_PROJECT'],
            logstore=os.environ['SLS_LOGSTORE']
        )
        # `serialize=True` 是关键，它将日志记录转为 JSON 字符串
        # `level="INFO"` 确保只有 INFO 及以上级别的日志被发送到 SLS
        logger.add(sls_sink.write, serialize=True, level="INFO")

        # 优雅停机时调用 stop
        # e.g. with atexit.register(sls_sink.stop)
    
    # 现在可以正常使用 logger
    logger.info("This message goes to both console and Aliyun SLS.")
    ```

## 4. 后续步骤

1.  **评审**: 请评审此设计方案。
2.  **实施**:
    -   在 `packages/` 目录下创建 `loguru-support` 的基本结构和 `pyproject.toml`。
    -   实现 `AliyunSlsSink` 类。
    -   编写独立的测试用例来验证 `AliyunSlsSink` 的功能。
    -   在 `examples/python-backend` 中集成并演示其用法。
3.  **文档**: 为 `loguru-support` 编写 `README.md`，说明其用途和使用方法。 