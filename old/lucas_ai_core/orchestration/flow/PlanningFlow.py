from typing import List, Optional, Dict


class StepStatus:
    """步骤状态常量（整数类型）"""

    INITIALIZED = 0  # 初始化
    PROCESSING = 1  # 处理中
    COMPLETED = 2  # 已完成
    FAILED = 3  # 失败


class Step:
    """步骤类，支持状态和输入输出数据，以及转换规则"""

    def __init__(
        self,
        step_id: str,
        status: int = StepStatus.INITIALIZED,
        input: dict = None,
        output: dict = None,
    ):
        self.step_id = step_id
        self.status = status
        self.input = input or {}
        self.output = output or {}
        self.transitions: Dict[str, str] = {}  # 事件到下一步骤ID的映射

    def add_transition(self, event: str, next_step_id: str):
        """添加一个事件转换规则"""
        self.transitions[event] = next_step_id

    def get_next_step_id(self, event: str) -> Optional[str]:
        """根据事件确定下一步骤ID"""
        return self.transitions.get(event)


class PlanningFlow:
    """步骤流程管理类，支持线性推进和事件驱动转换"""

    def __init__(self, steps: List[Step]):
        self.steps = steps
        self.current_index = 0

    @property
    def current(self) -> Optional[Step]:
        """返回当前步骤（不存在则返回 None）"""
        if self.current_index < len(self.steps):
            return self.steps[self.current_index]
        return None

    @property
    def next(self) -> Optional[Step]:
        """返回下一步骤（不存在则返回 None）"""
        idx = self.current_index + 1
        if idx < len(self.steps):
            return self.steps[idx]
        return None

    def is_end(self) -> bool:
        """判断是否所有步骤都已完成"""
        return all(step.status == StepStatus.COMPLETED for step in self.steps)

    def goNext(self) -> Optional[Step]:
        """过滤状态为 INITIALIZED 或 PROCESSING 的步骤，将第一个匹配项标记为 PROCESSING 并返回"""
        for step in self.steps:
            if step.status in (StepStatus.INITIALIZED, StepStatus.PROCESSING):
                step.status = StepStatus.PROCESSING
                return step
        return None

    def route(self, event: str) -> Optional[Step]:
        """处理事件，根据当前步骤的转换规则确定下一步"""
        current = self.current
        if not current:
            return None

        next_step_id = current.get_next_step_id(event)

        # 特殊处理："self"表示重新执行当前步骤
        if next_step_id == "self":
            return current

        # 找不到转换规则，默认进入下一步（线性推进）
        if next_step_id is None:
            self.advance()
            return self.current

        # 查找目标步骤
        for idx, step in enumerate(self.steps):
            if step.step_id == next_step_id:
                # 将当前步骤标记为完成
                if current.status == StepStatus.PROCESSING:
                    current.status = StepStatus.COMPLETED
                # 更新当前索引并标记新步骤为处理中
                self.current_index = idx
                step.status = StepStatus.PROCESSING
                return step

        # 没找到目标步骤，返回None或抛出异常
        return None

    def advance(self):
        """完成当前步骤并推进指针"""
        current = self.current
        if current:
            current.status = StepStatus.COMPLETED
        self.current_index += 1

    def insertStep(self, step: Step, index: int = None):
        """在指定位置插入步骤，并更新 current_index"""
        if index is None or index > len(self.steps):
            index = len(self.steps)
        else:
            index = max(0, index)
        self.steps.insert(index, step)
        if index <= self.current_index:
            self.current_index += 1

    def appendStep(self, step: Step):
        """在末尾追加步骤"""
        self.steps.append(step)
