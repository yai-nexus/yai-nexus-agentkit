# -*- coding: utf-8 -*-
"""
AG-UI 适配器数据模型
"""

from typing import Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    """任务模型，用于定义Agent任务"""

    id: str = Field(
        ...,
        description="作为run_id，每次请求的唯一标识",
        min_length=1,
        max_length=100,
    )
    query: str = Field(
        ...,
        description="用户查询内容",
        min_length=1,
        max_length=10000,
    )
    thread_id: Optional[str] = Field(
        None,
        description="对话线程ID，用于多轮对话上下文追踪",
        min_length=1,
        max_length=100,
    )

    class Config:
        """Pydantic 配置"""
        
        json_schema_extra = {
            "example": {
                "id": "task_abc123",
                "query": "请帮我分析这个数据并生成报告",
                "thread_id": "thread_def456",
            }
        }