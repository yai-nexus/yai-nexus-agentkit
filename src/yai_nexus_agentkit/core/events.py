# -*- coding: utf-8 -*-
"""
通用事件发射器
为节点提供协议无关的事件发射能力，支持双轨制事件处理架构
"""

import uuid
from typing import Any, Optional
from langchain_core.runnables import RunnableConfig


# 内部事件标记，用于标识由EventEmitter发出的事件
_INTERNAL_EVENT_MARKER = "agent_custom_event"


class EventEmitter:
    """
    标准的、协议无关的事件发射器，供Agent节点使用

    它提供了一个清晰的接口，让节点在执行过程中能够发射事件信号，
    将节点与特定适配器或UI实现完全解耦
    """

    def __init__(self, config: RunnableConfig):
        """
        初始化事件发射器

        Args:
            config: LangChain的运行配置，包含回调管理器
        """
        self._callbacks = config.get("callbacks")
        self._event_id_prefix = uuid.uuid4().hex[:8]
        self._event_counter = 0

    def emit(self, name: str, payload: Any, event_id: Optional[str] = None) -> None:
        """
        发射一个命名事件及其负载

        Args:
            name: 事件名称（例如："chart_generated", "user_confirmation_needed"）
            payload: 事件数据负载
            event_id: 可选的事件ID，如果未提供将自动生成
        """
        if not self._callbacks:
            return

        if event_id is None:
            self._event_counter += 1
            event_id = f"{self._event_id_prefix}_{self._event_counter}"

        full_event_data = {"event_id": event_id, "name": name, "payload": payload}

        # 使用内部标记发射自定义事件
        self._callbacks.on_custom_event(
            name=_INTERNAL_EVENT_MARKER, data=full_event_data
        )

    def emit_progress(
        self, step: str, progress: float, details: Optional[str] = None
    ) -> None:
        """
        发射进度更新事件的便捷方法

        Args:
            step: 当前步骤描述
            progress: 进度百分比 (0.0 - 1.0)
            details: 可选的详细信息
        """
        payload = {"step": step, "progress": progress, "details": details}
        self.emit("progress_update", payload)

    def emit_chart(
        self, chart_type: str, data: Any, title: Optional[str] = None
    ) -> None:
        """
        发射图表显示事件的便捷方法

        Args:
            chart_type: 图表类型 ("line", "bar", "pie", etc.)
            data: 图表数据
            title: 可选的图表标题
        """
        payload = {"type": chart_type, "data": data, "title": title}
        self.emit("display_chart", payload)

    def emit_file_download(self, filename: str, content: bytes, mime_type: str) -> None:
        """
        发射文件下载事件的便捷方法

        Args:
            filename: 文件名
            content: 文件内容
            mime_type: MIME类型
        """
        payload = {
            "filename": filename,
            "content": content.hex(),  # 转换为十六进制字符串以便JSON序列化
            "mime_type": mime_type,
        }
        self.emit("file_download", payload)
