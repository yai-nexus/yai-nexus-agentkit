# 统一示例应用日志策略方案

## 1. 目标与背景

当前 `examples` 目录下的各个示例应用（`python-backend`, `sls-loguru-example`, `nextjs-app`）采用了不同的日志记录方式。为了提升项目可维护性、标准化开发体验和简化调试流程，我们建议对所有示例应用的日志策略进行统一。

**核心目标**：
1.  **控制台输出**：所有应用都应能将日志打印到控制台。
2.  **文件输出**：所有应用都应能将日志写入根目录下的 `logs` 文件夹，并采用统一的目录结构（例如，按小时 `YYYYMMDD-HH/` 分割）。
3.  **按需集成**：支持按需开启或关闭特定的日志输出目标（如阿里云 SLS）。
4.  **技术栈覆盖**：方案需同时覆盖 Python（`loguru`）和 Node.js/TypeScript（`pino`）技术栈，并为未来新增的 `sls-pino-example` 应用做好准备。

## 2. 现状分析

-   `python-backend`: 使用了 `agentkit` 内的 `LoggerConfigurator` 和一个位于 `examples` 内部的 `HourlyDirectoryStrategy`，实现了控制台和文件日志，是目前最完善的。
-   `sls-loguru-example`: 主要使用了 `loguru-support` 包来集成阿里云 SLS，但缺少统一的本地文件日志策略。
-   `nextjs-app`: 作为一个标准的 Next.js 应用，目前仅将日志输出到控制台。
-   `sls-pino-example` (设想中): 作为一个新的 pino 应用，需要从零开始设计其日志系统。

**主要问题**: 各示例之间日志行为不一致，配置分散，缺乏统一管理。

## 3. 统一日志方案

我们提出以下两种方案，它们是递进关系，可以分步实施。

---

### 方案一：分栈统一，务实推进 (Pragmatic Stack-by-Stack Unification)

**核心思想**：为 Python 和 Node.js/TS 技术栈分别打造一个可复用的、标准化的日志工具，并在各自技术栈内部实现统一。

#### 3.1 Python 技术栈统一

1.  **增强 `agentkit` 的日志能力**:
    -   将 `examples/python-backend/logging_strategies.py` 中的 `HourlyDirectoryStrategy` 策略类移动并整合到 `packages/agentkit/src/yai_nexus_agentkit/core/` 目录下，作为 `agentkit` 的内置功能。
    -   在 `agentkit` 的 `LoggerConfigurator` 中增加一个更高级的封装函数，例如 `setup_default_logging(service_name: str)`，该函数会自动配置好“控制台输出”和“基于 `HourlyDirectoryStrategy` 的文件输出”。

2.  **改造 Python 示例**:
    -   **`python-backend`**: 修改 `main.py`，移除本地的 `logging_strategies` 导入，直接调用 `agentkit` 中新的 `setup_default_logging("python-backend")` 函数来完成日志配置。
    -   **`sls-loguru-example`**:
        -   首先，同样调用 `setup_default_logging("sls-loguru-example")` 来获得统一的控制台和文件日志。
        -   然后，像原来一样，创建 `AliyunSlsSink` 并通过 `logger.add()` 将其作为第三个 sink 添加进去。`loguru` 原生支持添加多个 sink，这使得改造非常简单。

#### 3.2 Node.js/TS 技术栈统一

1.  **增强 `pino-support` 包**:
    -   在 `packages/pino-support` 中，创建一个高级配置函数，例如 `createDefaultLogger({ serviceName: string })`。
    -   这个函数将返回一个 `pino` 实例，该实例已预先配置好：
        -   一个用于美化控制台输出的 transport (例如 `pino-pretty`)。
        -   一个自定义的 transport，负责将日志写入到 `logs/YYYYMMDD-HH/<serviceName>.log`，实现与 Python 端相同的日志文件结构。

2.  **改造 Node.js 示例**:
    -   **`nextjs-app`**: 在其后端逻辑中（例如 API 路由或服务器组件），导入并使用 `createDefaultLogger` 来获取 logger 实例并记录日志。
    -   **`sls-pino-example` (设想中)**:
        -   调用 `createDefaultLogger("sls-pino-example")` 获取基础 logger。
        -   然后，利用 `pino-support` 中已有的 `SlsTransport`，将其作为额外的 transport 添加到 logger 中。

#### 3.3 方案一评估

-   **优点**:
    -   **务实高效**: 改动清晰，能快速实现每个技术栈内部的统一。
    -   **代码复用**: 将日志配置逻辑集中到了 `agentkit` 和 `pino-support` 中，避免了在每个示例中重复编写。
    -   **低耦合**: Python 和 Node.js 的日志系统各自独立，互不影响。
-   **缺点**:
    -   **配置分散**: 开发者仍需知道 Python 和 Node.js 分别调用的是哪个函数。
    -   **跨栈不一致**: 如果未来要调整日志格式或目录结构，需要同时修改 `agentkit` 和 `pino-support` 两个包。

---

### 方案二：标准化配置，统一体验 (Standardized Configuration via Env Vars)

**核心思想**：在**方案一**的基础上，引入一套标准化的环境变量，使得所有示例的日志行为都可以通过相同的方式进行控制，无论其底层技术栈是什么。

#### 3.1 标准化环境变量

定义一套通用的环境变量，并写入根目录的 `.env.example` 文件中：

```dotenv
# ========================
# UNIFIED LOGGING SETTINGS
# ========================

# 日志级别 (e.g., DEBUG, INFO, WARN, ERROR)
LOG_LEVEL=INFO

# 是否开启文件日志 (true/false)
LOG_TO_FILE=true

# 日志根目录
LOG_DIR=logs

# 是否开启阿里云 SLS 日志 (true/false)
SLS_LOGGING_ENABLED=false
```

#### 3.2 实现方式

-   **Python 端 (`agentkit`)**: 修改 `setup_default_logging` 函数，使其内部读取上述环境变量。例如，`LOG_TO_FILE=false` 时，就不再添加文件 sink。
-   **Node.js 端 (`pino-support`)**: 同样修改 `createDefaultLogger` 函数，使其也读取这些环境变量，并根据其值来决定是否添加文件 transport。
-   **SLS 集成**: `sls-loguru-example` 和 `sls-pino-example` 会检查 `SLS_LOGGING_ENABLED` 变量，仅当其为 `true` 时，才执行添加 SLS sink/transport 的逻辑。

#### 3.3 方案二评估

-   **优点**:
    -   **配置统一**: 开发者可以通过一套环境变量控制所有示例的日志行为，无需关心内部实现。
    -   **体验极佳**: 启动不同示例时的配置心智负担降到最低。
    -   **灵活开关**: 可以轻松地在不同环境中（如本地开发、CI）打开或关闭文件日志、SLS 日志。
-   **缺点**:
    -   **增加了复杂度**: 需要在两个包中实现读取和解析环境变量的逻辑。
    -   **维护成本**: 环境变量的 schema 一旦确定，两个包的实现必须严格保持同步。

---

## 4. 方案对比与建议

| 特性 | 方案一 (分栈统一) | 方案二 (标准化配置) |
| :--- | :--- | :--- |
| **实现复杂度** | 低 | 中 |
| **代码复用性** | 高 | 高 |
| **配置一致性** | 中（栈内一致） | **高**（跨栈一致） |
| **开发者体验** | 好 | **优秀** |
| **维护成本** | 低 | 中（需同步两端实现） |

**建议的实施路径**:

我建议采用**分步实施**的策略：
1.  **首先，完成方案一**。这是基础，能快速解决当前代码重复和不一致的核心问题。
2.  **然后，在方案一的基础上，实施方案二**。将环境变量作为一种“增强配置”引入，使项目整体的日志管理能力再上一个台阶。

这个路径风险最低，每一步都能带来切实的价值。

---

## 5. 下一步行动计划

如果此方案获得批准，建议的下一步骤是：
1.  将 `HourlyDirectoryStrategy` 整合进 `packages/agentkit`。
2.  为 `agentkit` 添加 `setup_default_logging` 高级函数。
3.  增强 `packages/pino-support`，添加文件日志 transport 和 `createDefaultLogger` 函数。
4.  逐个重构 `python-backend`, `sls-loguru-example`, `nextjs-app` 以使用新的统一日志工具。
5.  （可选，进入方案二）为 `agentkit` 和 `pino-support` 添加读取环境变量的逻辑。 