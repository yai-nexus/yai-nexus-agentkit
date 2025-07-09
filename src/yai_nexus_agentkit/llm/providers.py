# -*- coding: utf-8 -*-
"""LLM 提供商枚举定义。"""

from enum import Enum


class LLMProvider(str, Enum):
    """支持的 LLM 提供商枚举。"""

    OPENAI = "openai"
    ZHIPU = "zhipu"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    TONGYI = "tongyi"
    DOUBAO = "doubao"
