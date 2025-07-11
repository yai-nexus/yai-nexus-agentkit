# -*- coding: utf-8 -*-
"""
AGUIAdapter异常类定义
提供特定的异常类型，便于调用者精确捕获和处理适配器错误
"""


class AGUIAdapterError(Exception):
    """AGUIAdapter基础异常类"""

    pass


class EventTranslationError(AGUIAdapterError):
    """事件翻译错误，当事件无法被正确翻译时抛出"""

    pass


class ToolCallTrackingError(AGUIAdapterError):
    """工具调用跟踪错误，当工具调用状态管理出现问题时抛出"""

    pass


class UnknownEventTypeError(AGUIAdapterError):
    """未知事件类型错误，当遇到无法识别的事件类型时抛出"""

    pass
