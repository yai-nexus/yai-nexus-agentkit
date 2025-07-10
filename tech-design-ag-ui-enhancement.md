# AGUIAdapter 功能增强技术方案

## 1. 背景与目标

### 1.1 背景

当前的 `AGUIAdapter` 实现了 `AG-UI` (Agent-UI) 协议的一个核心子集，能够支持基本的 Agent 运行状态展示和文本流式输出。然而，它缺少对 Agent 内部思考过程，特别是工具调用（Tool Calls）细节的展示，并且部分事件的使用方式与协议规范存在偏差。这使得前端用户无法观察到 Agent "思考" 的关键步骤，限制了最终用户体验的透明度和可调试性。

### 1.2 目标

本次技术改造旨在将 `AGUIAdapter` 升级为对 `AG-UI` 协议的 "高保真" 实现。目标是利用 `langgraph` 提供的丰富的事件流，将 Agent 的内部活动完整、准确地映射到 `AG-UI` 的标准事件上，从而在前端实现一个完全透明、可观察、可调试的 Agent 交互界面。

---

## 2. 现状与差距分析 (详细版)

我们将所有 `AG-UI` 事件分为三类进行全面分析：

### ✅ 2.1 已支持 (Supported)

-   `RunStartedEvent`: 标志运行开始。
-   `RunFinishedEvent`: 标志运行成功结束。
-   `RunErrorEvent`: 标志运行出错。
-   `TextMessageChunkEvent`: 用于流式传输最终的文本回答。

### ❌ 2.2 未支持 - 高优先级差距 (High-Priority Gaps)

这些是严重影响核心功能和用户体验的缺失部分，是本次改造的 **主要目标**。

| AG-UI 关键事件        | 缺失原因                                                     | 影响                                                         |
| ----------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `ToolCallStartEvent`    | 未从 `on_tool_start` 映射。                                  | 无法在前端结构化地展示一个工具调用的开始。                   |
| `ToolCallArgsEvent`     | **(最关键缺失)** 未从 `on_tool_start` 事件的 `input` 字段映射。 | 用户无法看到 Agent 调用工具时传入的具体参数，透明度严重不足。  |
| `ToolCallEndEvent`      | 未从 `on_tool_end` 映射。                                    | 无法在前端结构化地展示一个工具调用的结束。                   |
| `ToolCallResultEvent`   | **(最关键缺失)** 未从 `on_tool_end` 事件的 `output` 字段映射。 | 用户无法看到工具执行后返回了什么具体结果，无法理解 Agent 的决策依据。 |
| `ThinkingStartEvent`    | 未从 `on_chain_start` 等事件映射。                           | 无法在 UI 上明确展示一个独立的 "思考" 或 "规划" 阶段。       |
| `ThinkingEndEvent`      | 未从 `on_chain_end` 等事件映射。                             | -                                                            |

### ⚠️ 2.3 未支持 - 低优先级或实现有偏差 (Lower-Priority Gaps & Deviations)

这些是更精细的事件，或当前实现与协议规范有出入的地方，可作为 **第二阶段** 增强目标。

| AG-UI 事件              | 问题描述                                                     | 改进方向                                                     |
| ----------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `StateDeltaEvent`       | **实现有偏差**。协议要求 `delta` 是 JSON Patch (RFC 6902) 列表，而我们仅传递了自定义的键值对。 | 1.  停止使用此事件。<br/>2.  或严格按照 JSON Patch 格式构造 `delta`。<br/>3.  或改用 `CustomEvent` 传递非标状态。 |
| `StepStartedEvent`      | 未支持。`langgraph` 的 `on_node_start` 可映射于此。          | 可用于展示比 `Thinking` 更细粒度的执行步骤。                 |
| `StepFinishedEvent`     | 未支持。`langgraph` 的 `on_node_end` 可映射于此。            | -                                                            |
| `TextMessageStart/End`  | 未支持。当前仅使用 `Chunk`，无法标识消息的边界。             | 实现完整的消息生命周期管理，对需要精确聚合消息的前端更有利。 |
| `ToolCallChunkEvent`    | 未支持。                                                     | 适用于工具的输出内容本身是长文本流的场景。                   |
| `MessagesSnapshotEvent` | 未支持。                                                     | 用于一次性发送完整的消息历史快照。                           |

---

## 3. 设计决策：事件类型的强类型化

### 3.1 问题：魔术字符串 (Magic Strings)

在代码中直接使用字符串字面量（如 `"on_tool_start"`) 来判断事件类型是一种 "坏味道" (Code Smell)，被称为 "魔术字符串"。它存在以下弊端：
- **易出错**: 手动输入字符串容易产生拼写错误，这种错误在运行时才能发现，且难以调试。
- **可维护性差**: 如果上游 `langgraph` 库修改了事件名称，我们需要在代码库中进行全局搜索和替换，容易遗漏。
- **可读性与智能提示缺失**: 代码读者无法一目了然地知道所有可能的事件类型，IDE 也无法提供智能自动补全。

### 3.2 方案：定义枚举 (Enum)

为了解决以上问题，我们决定对 `langgraph` 的事件类型进行强类型化。

**调研结论**: 经查阅 `langgraph` 源代码（特别是 `constants.py`），确认其并未以常量或枚举的形式公开暴露流式事件的名称。

**决策**: 我们将在自己的适配器模块中定义一个 `LangGraphEventType` 枚举，将所有我们关心的事件字符串收敛到这一个地方。

### 3.3 实施细节

1.  **创建新文件**: 在 `src/yai_nexus_agentkit/adapter/` 目录下创建新文件 `langgraph_events.py`。
2.  **定义枚举类**: 在该文件中添加以下内容：
    ```python
    # src/yai_nexus_agentkit/adapter/langgraph_events.py
    from enum import Enum

    class LangGraphEventType(str, Enum):
        """
        Enumeration of LangGraph streaming event types.
        This provides strong typing and avoids "magic strings" in the adapter logic.
        """
        ON_TOOL_START = "on_tool_start"
        ON_TOOL_END = "on_tool_end"
        ON_CHAT_MODEL_STREAM = "on_chat_model_stream"
        ON_CHAIN_START = "on_chain_start"
        ON_CHAIN_END = "on_chain_end"
        ON_NODE_START = "on_node_start"
        ON_NODE_END = "on_node_end"
        ON_CUSTOM_EVENT = "on_custom_event"
        # Add other relevant event types here as needed
    ```
3.  **在适配器中使用**:
    `AGUIAdapter` 将导入此枚举，并在事件处理逻辑中使用它，例如：
    ```python
    # In AGUIAdapter...
    from .langgraph_events import LangGraphEventType

    # ...
    kind_str = event["event"]
    try:
        kind = LangGraphEventType(kind_str)
    except ValueError:
        # Handle unknown event types gracefully
        continue

    if kind is LangGraphEventType.ON_TOOL_START:
        # ... process tool start
    ```

---

## 4. 核心映射方案：LangGraph -> AG-UI

为了弥补上述差距，我们需要建立 `langgraph` 事件与 `AG-UI` 事件之间更精细的映射关系。

| LangGraph Event (`kind`) | LangGraph Data (`event["data"]`) | 映射到的 AG-UI Event(s)                                    | 说明                                                              |
| ------------------------ | -------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------- |
| `on_tool_start`          | `name`, `input`                  | **`ToolCallStartEvent`**<br/>**`ToolCallArgsEvent`**        | 1. 用 `name` 填充 `tool_call_name`。<br/>2. 用 `input` 填充 `delta`。  |
| `on_tool_end`            | `name`, `output`                 | **`ToolCallEndEvent`**<br/>**`ToolCallResultEvent`**        | 1. 用 `name` 填充 `tool_call_name`。<br/>2. 用 `output` 填充 `content`。 |
| `on_chain_start`         | `name`                           | `ThinkingStartEvent`                                       | 用 `name` 填充 `title`，展示思考步骤的标题。                      |
| `on_chain_end`           | `name`                           | `ThinkingEndEvent`                                         | 标志思考步骤结束。                                                |
| `on_node_start`          | `name`                           | `StepStartedEvent`                                         | (可选) 展示更细粒度的节点执行。                                   |
| `on_node_end`            | `name`                           | `StepFinishedEvent`                                        | (可选)                                                            |
| `on_chat_model_stream`   | `chunk.content`                  | `TextMessageChunkEvent`                                    | (保持不变) 流式传输 LLM 的输出。                                  |

**注意**: `langgraph` 的事件中不直接提供 `tool_call_id`。我们需要在 `AGUIAdapter` 内部生成一个唯一的 ID (`uuid.uuid4().hex`)，并在 `start`/`args`/`end`/`result` 事件之间共享它，以将它们关联到同一次工具调用。

---

## 5. 实施步骤

1.  **创建 `langgraph_events.py`**: 根据章节 3.3 的描述，创建并定义 `LangGraphEventType` 枚举。
2.  **修改 `AGUIAdapter.event_stream_adapter`**:
    -   导入 `LangGraphEventType`。
    -   在循环的开始，将事件字符串转换为 `LangGraphEventType` 枚举成员，并处理未知事件。
    -   将所有 `if/elif` 判断条件从 `kind == "..."` 修改为 `kind is LangGraphEventType.MEMBER`。
3.  **引入 `tool_call_id` 管理**: 在 `event_stream_adapter` 的作用域内创建一个字典或状态管理器，用于生成和追踪当前活动的 `tool_call_id`。

4.  **增强 `on_tool_start` 事件处理**:
    -   当 `kind is LangGraphEventType.ON_TOOL_START`:
    -   生成一个唯一的 `tool_call_id` 并保存。
    -   `yield` 一个 `ag_ui.core.events.ToolCallStartEvent`，填充 `tool_call_id` 和从 `event["data"]["name"]` 获取的 `tool_call_name`。
    -   `yield` 一个 `ag_ui.core.events.ToolCallArgsEvent`，将 `event["data"]["input"]` 序列化为 JSON 字符串后填充到 `delta` 字段。
    -   **移除** 原有的 `StateDeltaEvent`，因为它已被功能更丰富的事件替代。

5.  **增强 `on_tool_end` 事件处理**:
    -   当 `kind is LangGraphEventType.ON_TOOL_END`:
    -   使用之前保存的 `tool_call_id`。
    -   `yield` 一个 `ag_ui.core.events.ToolCallEndEvent`，填充 `tool_call_id`。
    -   `yield` 一个 `ag_ui.core.events.ToolCallResultEvent`，将 `event["data"]["output"]` 序列化为 JSON 字符串后填充到 `content` 字段。
    -   清除已完成的 `tool_call_id`。
    -   **移除** 原有的 `StateDeltaEvent`。

6.  **（可选/第二阶段）实现 `Thinking` 和 `Step` 事件**:
    -   添加对 `LangGraphEventType.ON_CHAIN_START` 等枚举成员的处理。
    -   根据映射表 `yield` 相应的 `AG-UI` 事件。

---

## 6. 错误处理策略

一个健壮的适配器必须能够优雅地处理预期之外的输入和内部错误。

### 6.1 自定义异常

为了让调用者能精确捕获源自本适配器的错误，我们将定义一个基础异常类。

```python
# src/yai_nexus_agentkit/adapter/errors.py (New File)
class AGUIAdapterError(Exception):
    """Base exception for AGUIAdapter specific errors."""
    pass

class EventTranslationError(AGUIAdapterError):
    """Raised when an event cannot be translated."""
    pass
```

### 6.2 未知事件类型的处理

当 `langgraph` 库更新，引入了我们的 `LangGraphEventType` 枚举还不认识的新事件类型时，适配器不应该崩溃。

**策略**: 采用宽容处理（Tolerant Handling）。
1.  在 `event_stream_adapter` 中，当 `LangGraphEventType(kind_str)` 转换失败并抛出 `ValueError` 时，予以捕获。
2.  使用 `logger.warning()` 记录下未知的事件类型 `kind_str` 及其内容，以便后续分析和跟进。
3.  忽略该事件，使用 `continue` 继续处理事件流中的下一个事件。

这能保证适配器在面对上游库的非破坏性更新时，依然能稳定运行核心功能。

---

## 7. 测试策略

为了保证适配器的正确性、健壮性和性能，需要建立一个多层次的测试策略。

### 7.1 单元测试 (Unit Tests)

-   **测试目标**: `_translate_event` 辅助方法（我们将在重构中创建）。
-   **测试方法**:
    -   为每一种关心的 `langgraph` 事件类型（`ON_TOOL_START`, `ON_TOOL_END` 等）创建 Mock 的输入字典。
    -   调用 `_translate_event(mock_event)` 并收集其 `yield` 的所有结果。
-   **断言**:
    -   验证返回的 `AG-UI` 事件对象的**类型**和**内容**是否完全符合预期。
    -   验证对于 `on_tool_start` 和 `on_tool_end`，相关的系列事件（Start, Args, End, Result）共享同一个 `tool_call_id`。
-   **边缘情况测试**:
    -   测试当输入一个未知事件类型时，该方法是否不产生任何输出。

### 7.2 集成测试 (Integration Tests)

-   **测试目标**: 完整的 `AGUIAdapter.event_stream_adapter` 方法。
-   **覆盖范围**:
    -   构建一个包含至少一个工具的、可运行的 `langgraph` `StateGraph` 实例。
    -   在测试中调用 `adapter.event_stream_adapter`，并完整消费其返回的异步生成器。
    -   收集所有产生的 `AG-UI` 事件。
-   **断言**:
    -   **事件序列**: 验证事件的总体顺序是否正确（`RunStarted` 在最前, `RunFinished`/`RunError` 在最后）。
    -   **工具调用流程**: 验证一次完整的工具调用是否能正确地生成 `ToolCallStart` -> `ToolCallArgs` -> `ToolCallEnd` -> `ToolCallResult` 的事件序列。
    -   **错误处理流程**: 故意在 langgraph 图中或工具中引发异常，验证适配器是否能正确捕获并产生一个 `RunErrorEvent`。

### 7.3 性能测试 (Performance Tests)

-   **测试目标**: 量化 `AGUIAdapter` 引入的事件处理延迟。
-   **测试方法**:
    1.  **基线 (Baseline)**: 编写脚本直接异步消费一个包含 N 个事件的 `langgraph` `astream_events` 流，记录总耗时 `T_base`。
    2.  **实验 (Experimental)**: 编写脚本将同一个事件流传入 `AGUIAdapter`，异步消费适配器处理后的 `AG-UI` 事件流，记录总耗时 `T_adapter`。
-   **基准指标**:
    -   **平均事件开销**: `(T_adapter - T_base) / N`
    -   **设定阈值**: 为此指标设定一个可接受的阈值（例如：< 5ms/事件）。
    -   此测试可纳入 CI/CD 流水线，以防止未来的代码变更引入性能衰退。

---

## 8. 高级功能：通过 `EventEmitter` 发射业务事件

`langgraph` 的原生事件流擅长描述框架的**结构性活动**（如工具调用、节点执行），但它无法理解应用的**业务层语义**。为了让节点能够发送应用专属的、希望驱动前端 UI 做出特殊响应的信号（例如，渲染一张图表），我们引入了一个干净、解耦的“第二轨道”：`EventEmitter`。

### 8.1 “双轨制”设计哲学

我们的事件处理遵循一个清晰的“双轨制”模型：

1.  **轨道一：自动化结构性事件**
    -   **来源**: `langgraph` 引擎的原生 `astream_events` 流。
    -   **内容**: 描述框架正在做什么 (`on_tool_start`, `on_chat_model_stream` 等)。
    -   **职责**: `AGUIAdapter` 的核心职责是**被动地监听并翻译**这些事件为标准的 `AG-UI` 事件。开发者无需关心。

2.  **轨道二：手动业务事件**
    -   **来源**: 开发者在节点代码中**主动调用** `EventEmitter`。
    -   **内容**: 描述业务逻辑希望 UI 做什么 (`display_chart`, `request_user_confirmation` 等)。
    -   **职责**: 节点开发者使用 `EventEmitter` 发射与协议无关的通用事件。`AGUIAdapter` 负责监听这些通用事件，并将其翻译为 `AG-UI` 的 `CustomEvent`。

这个模型将框架的自动化观测能力与应用的手动扩展能力完美地结合起来。

### 8.2 引入 `EventEmitter`

为了给开发者提供一个优雅、标准的 API，我们定义一个通用的 `EventEmitter` 类。

```python
# Proposed location: src/yai_nexus_agentkit/orchestration/events.py
from typing import Any
from langchain_core.runnables import RunnableConfig

_INTERNAL_EVENT_MARKER = "agent_custom_event"

class EventEmitter:
    """
    A standard, protocol-agnostic event emitter for use within Agent nodes.
    It provides a clean interface for nodes to signal events during their
    execution, decoupling them from any specific adapter or UI implementation.
    """
    def __init__(self, config: RunnableConfig):
        self._callbacks = config.get("callbacks")

    def emit(self, name: str, payload: Any) -> None:
        """
        Emits a named event with a payload.

        Args:
            name: The name of the event (e.g., "chart_generated").
            payload: The data payload for the event.
        """
        if not self._callbacks:
            return

        full_event_data = {"name": name, "payload": payload}
        self._callbacks.on_custom_event(name=_INTERNAL_EVENT_MARKER, data=full_event_data)
```

### 8.3 开发者体验

`EventEmitter` 提供了极致简洁和清晰的开发者体验，且完全不干扰节点作为状态更新单元的核心职责。

**使用示例**:
```python
# In a langgraph node
from yai_nexus_agentkit.orchestration.events import EventEmitter

def my_charting_node(state: AgentState, config: RunnableConfig):
    # 1. 执行业务逻辑
    chart_data = {"type": "line", "data": [1, 5, 3]}
    
    # 2. 初始化 emitter 并发射一个与业务相关的事件
    emitter = EventEmitter(config)
    emitter.emit(name="display_chart", payload=chart_data)
    
    # 3. 节点的 return 语句回归其纯粹的职责：更新状态
    return {"status_message": "Charting complete"}
```

### 8.4 `AGUIAdapter` 的翻译职责

`AGUIAdapter` 现在需要监听 `on_custom_event`，并检查它是否是由我们的 `EventEmitter` 发出的内部事件，然后将其翻译成 `AG-UI` 的 `CustomEvent`。

**适配器翻译逻辑**:
```python
# 在 AGUIAdapter 的处理逻辑中
# ...
elif kind is LangGraphEventType.ON_CUSTOM_EVENT:
    # 只处理我们约定的、由 EventEmitter 发出的内部标记事件
    # _INTERNAL_EVENT_MARKER 的值应从 yai_nexus_agentkit.orchestration.events 导入
    if event["name"] == _INTERNAL_EVENT_MARKER:
        # 从负载中解析出真正的事件名和数据
        event_data = event["data"]
        ui_event_name = event_data["name"]
        ui_event_payload = event_data["payload"]
        
        # 翻译成 AG-UI 的 CustomEvent
        yield CustomEvent(
            name=ui_event_name,
            value=ui_event_payload
        )
```

### 8.5 最终事件分类清单

| 事件轨道 | AG-UI 事件                                               | 触发方式                                                    |
| :------- | :------------------------------------------------------- | :---------------------------------------------------------- |
| **自动化** | `Run*`, `Thinking*`, `Step*`, `ToolCall*`, `TextMessage*` | **自动**: 由 `AGUIAdapter` 监听 `langgraph` 原生事件流并翻译。 |
| **手动**   | `CustomEvent`                                            | **手动**: 由开发者在节点中调用 `emitter.emit(...)` 来触发。   |


---

## 9. 预期收益

完成本次改造后，`AGUIAdapter` 将：
-   **高度兼容 `AG-UI`**: 能够驱动功能丰富的、高度透明的前端交互界面。
-   **代码更健壮**: 通过强类型枚举消除了魔术字符串，并通过明确的错误处理策略提升了容错性。
-   **质量可验证**: 拥有完整的多层测试策略，确保代码的正确性和性能。
-   **提升用户体验**: 用户可以清晰地看到 Agent 的每一步思考，包括完整的工具调用细节和丰富的自定义业务事件。
-   **架构更清晰**: 节点的核心业务逻辑与 UI 协议实现完全解耦，提升了代码的可维护性和可移植性。
-   **增强可调试性**: 开发人员可以通过观察详细的事件流，快速定位 Agent 行为异常的原因。
-   **成为名副其实的 "高级" 适配器**: 提供与 `langgraph` 能力相匹配的、一流的前端集成能力。 