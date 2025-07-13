# `sls_example.py` 简化方案

## 1. 核心问题

当前的 `examples/python-backend/sls_example.py` 文件（约 200 行）过于复杂，混合了日志上报、系统监控、优雅停机和多种日志记录技巧的演示。这对于想快速了解如何集成 SLS 的用户来说不够直观，学习成本较高。

## 2. 简化目标

将示例代码**聚焦于单一职责**：**演示如何以最简单、最直接的方式将 Loguru 日志发送到阿里云 SLS**。

简化后的代码应清晰地展示 `yai-loguru-support` 包的核心价值——用几行代码完成生产级的日志集成。

## 3. 简化方向

### 3.1. 移除监控和告警 (`setup_monitoring_example`)

*   **现状**: 包含一个 `setup_monitoring_example` 函数，用于设置对 Sink 本身的监控，并配置了控制台和日志告警通道。这部分代码占据了约 70 行。
*   **简化方案**: **完全移除**。监控是 `yai-loguru-support` 的一个高级功能，适合在专门的示例中展示，而不应与基础的日志上报功能混在一起。

### 3.2. 简化日志记录逻辑 (`demo_logging`)

*   **现状**: `demo_logging` 函数演示了绑定上下文 (`bind`)、上下文管理器 (`contextualize`)、异常捕获 (`exception`) 和性能日志等多种用法。
*   **简化方案**: **完全移除**。在主函数中保留几条简单的 `logger.info()`, `logger.warning()`, `logger.exception()` 调用即可，足以证明日志已成功发送。

### 3.3. 简化配置过程 (`setup_sls_logging`)

*   **现状**: 该函数手动检查了 5 个环境变量，并包含环境判断逻辑 (`if os.getenv("ENV") != "production":`)。
*   **简化方案**:
    1.  用 `AliyunSlsSink.from_env()` 工厂方法替代手动检查。这可以将十几行代码简化为一行。
    2.  移除环境判断。示例文件默认就是为了演示功能，不需要区分生产和开发环境。
    3.  移除 `try/except ImportError`，如果依赖没装，让程序直接报错 `ImportError`，信息更清晰。

### 3.4. 精简主流程 (`main` 函数)

*   **现状**: `main` 函数中包含一个无限循环 `while True: ...`，其主要目的是为了配合监控系统持续运行。
*   **简化方案**: **移除无限循环**。脚本的逻辑应改为“启动 -> 发送日志 -> 结束”。`create_production_setup` 会确保在脚本退出前，所有缓冲区的日志都被成功发送。

## 4. 简化前后对比（伪代码）

### **简化前 (核心逻辑)**

```python
# 检查依赖
try:
    # ... import ...
except ImportError:
    # ... handle ...

# 检查配置
def setup_sls_logging():
    if os.getenv("ENV") != "production":
        return
    # ... 检查一堆环境变量 ...
    # ... 创建 SlsConfig 和 AliyunSlsSink ...
    return sls_sink

# 设置监控
def setup_monitoring_example(sink):
    # ... 创建 Monitor 和 AlertChannel ...
    return monitor

# 主函数
async def main():
    sls_sink = setup_sls_logging()
    monitor = setup_monitoring_example(sls_sink)
    create_production_setup([sls_sink])
    
    await demo_logging() # 演示复杂日志
    
    # 无限循环以维持监控
    while True:
        await asyncio.sleep(10)
```

### **简化后 (核心逻辑)**

```python
import asyncio
import os
from yai_nexus_agentkit.core.logging import logger
from yai_loguru_support.sls import AliyunSlsSink
from yai_loguru_support.utils import create_production_setup

async def main():
    # 1. 从环境变量创建 Sink
    # (假设 SLS_* 环境变量已设置)
    sls_sink = AliyunSlsSink.from_env()

    # 2. 设置优雅停机
    # (自动处理 Ctrl+C, 确保日志在退出前发送)
    create_production_setup([sls_sink])
    
    # 3. 发送日志
    logger.info("这是一个简单的 INFO 日志")
    logger.warning("这是一个 WARNING 日志", user_id="test_user")
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("这是一个自动捕获的异常日志")
        
    logger.info("示例运行结束，等待日志发送...")
    await asyncio.sleep(5) # 等待批处理发送

if __name__ == "__main__":
    # 确保环境变量已设置
    if not os.getenv("SLS_ENDPOINT"):
        print("错误: 缺少必要的 SLS_* 环境变量。")
        print("请参考 README.md 设置环境变量。")
    else:
        asyncio.run(main())
```

## 5. 预期结果

*   `sls_example.py` 文件行数从约 200 行减少到 50 行以内。
*   示例代码的目的变得非常清晰：只演示 SLS 日志集成。
*   用户可以更容易地理解和复用代码。
*   保留了生产级实践的核心：从环境变量配置和优雅停机。

## 6. 目录结构调整

为了使示例项目结构更清晰、职责更单一，建议将简化后的 SLS 示例迁移到一个新的、专门的目录中。

*   **创建新目录**: 在 `examples/` 目录下创建一个新目录 `sls-logger-example`，与 `python-backend` 平级。

*   **移动并重命名脚本**: 将简化后的 `sls_example.py` 脚本移动到 `examples/sls-logger-example/` 目录下，并重命名为 `main.py`。

*   **删除旧文件**: 删除原有的 `examples/python-backend/sls_example.py` 文件。

*   **创建 `README.md`**: 在 `sls-logger-example/` 目录中创建一个新的 `README.md` 文件，说明示例的用途、如何配置环境变量以及如何安装和运行。

*   **创建 `requirements.txt`**: 在 `sls-logger-example/` 目录中创建一个 `requirements.txt` 文件，包含运行此示例所需的最小依赖：
    ```txt
    yai-nexus-agentkit
    yai-loguru-support[sls]
    ``` 