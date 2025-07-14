# -*- coding: utf-8 -*-
"""
工具调用状态跟踪器
管理当前活跃的工具调用ID，用于在start、args、end、result事件之间建立关联
"""

import uuid
from typing import Dict, Optional


class ToolCallTracker:
    """
    工具调用状态跟踪器
    管理当前活跃的工具调用ID，用于在start、args、end、result事件之间建立关联
    """

    def __init__(self):
        self.active_calls: Dict[str, str] = {}  # tool_name -> call_id

    def start_call(self, tool_name: str) -> str:
        """开始一次工具调用，返回生成的call_id"""
        call_id = uuid.uuid4().hex
        self.active_calls[tool_name] = call_id
        return call_id

    def end_call(self, tool_name: str) -> Optional[str]:
        """结束一次工具调用，返回并清理call_id"""
        return self.active_calls.pop(tool_name, None)

    def get_call_id(self, tool_name: str) -> Optional[str]:
        """获取当前工具的call_id"""
        return self.active_calls.get(tool_name)