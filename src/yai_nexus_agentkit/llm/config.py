# -*- coding: utf-8 -*-
"""LLM 配置模型定义。"""

from pydantic import BaseModel, Field

from .providers import LLMProvider


class LLMConfig(BaseModel):
    """
    LLM 配置的基础模型。

    所有特定提供商的配置模型都应继承自此模型。
    """

    provider: LLMProvider = Field(..., description="LLM 提供商的名称。")
    model: str = Field(..., description="要使用的具体模型名称。")

    class Config:
        extra = "allow"  # 允许未在模型中定义的额外字段
