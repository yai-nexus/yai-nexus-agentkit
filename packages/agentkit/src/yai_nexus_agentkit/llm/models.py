# -*- coding: utf-8 -*-
"""LLM 模型枚举定义。"""

from enum import Enum
from typing import Dict, Type, Optional


class OpenAIModel(str, Enum):
    """OpenAI 常用模型枚举。"""

    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"


class AnthropicModel(str, Enum):
    """Anthropic 常用模型枚举。"""

    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"


class ZhipuModel(str, Enum):
    """智谱 AI 常用模型枚举。"""

    GLM_4 = "glm-4"
    GLM_4_TURBO = "glm-4-turbo"
    GLM_3_TURBO = "glm-3-turbo"


class TongyiModel(str, Enum):
    """通义千问常用模型枚举。"""

    QWEN_PLUS = "qwen-plus"
    QWEN_TURBO = "qwen-turbo"
    QWEN_MAX = "qwen-max"


class DoubaoModel(str, Enum):
    """豆包（抖音）常用模型枚举。"""

    DOUBAO_SEED_1_6_MODEL = "doubao-seed-1-6-250615"
    DOUBAO_SEED_1_5_MODEL = "doubao-1.5-thinking-pro-250415"
    DOUBAO_PRO_4K = "doubao-pro-4k"
    DOUBAO_PRO_32K = "doubao-pro-32k"
    DOUBAO_PRO_128K = "doubao-pro-128k"
    DOUBAO_LITE_4K = "doubao-lite-4k"
    DOUBAO_LITE_32K = "doubao-lite-32k"
    DOUBAO_LITE_128K = "doubao-lite-128k"


class OpenRouterModel(str, Enum):
    """
    OpenRouter 常用模型枚举。

    OpenRouter 是一个聚合平台，支持多家提供商的模型。
    模型名称格式通常为 "provider/model-name"。
    """

    # OpenAI 模型 (通过 OpenRouter)
    OPENAI_GPT_4O = "openai/gpt-4o"
    OPENAI_GPT_4O_MINI = "openai/gpt-4o-mini"
    OPENAI_GPT_4_TURBO = "openai/gpt-4-turbo"

    # Anthropic 模型 (通过 OpenRouter)
    ANTHROPIC_CLAUDE_3_5_SONNET = "anthropic/claude-3.5-sonnet"
    ANTHROPIC_CLAUDE_3_OPUS = "anthropic/claude-3-opus"
    ANTHROPIC_CLAUDE_3_HAIKU = "anthropic/claude-3-haiku"

    # Google 模型 (通过 OpenRouter)
    GOOGLE_GEMINI_PRO = "google/gemini-pro"
    GOOGLE_GEMINI_PRO_1_5 = "google/gemini-pro-1.5"
    GOOGLE_GEMINI_2_FLASH_EXP = "google/gemini-2.0-flash-exp"

    # Meta 模型 (通过 OpenRouter)
    META_LLAMA_3_1_70B = "meta-llama/llama-3.1-70b-instruct"
    META_LLAMA_3_1_8B = "meta-llama/llama-3.1-8b-instruct"

    # Mistral 模型 (通过 OpenRouter)
    MISTRAL_LARGE = "mistralai/mistral-large"
    MISTRAL_MEDIUM = "mistralai/mistral-medium"

    # 其他热门模型
    PERPLEXITY_LLAMA_3_1_SONAR_LARGE = "perplexity/llama-3.1-sonar-large-128k-online"
    DEEPSEEK_CODER = "deepseek/deepseek-coder"


# 统一的模型枚举映射
MODEL_MAPPING: Dict[str, Type[Enum]] = {
    "openai": OpenAIModel,
    "anthropic": AnthropicModel,
    "zhipu": ZhipuModel,
    "tongyi": TongyiModel,
    "doubao": DoubaoModel,
    "openrouter": OpenRouterModel,
}


def get_model_enum(provider: str) -> Optional[Type[Enum]]:
    """
    根据提供商获取对应的模型枚举类。

    Args:
        provider: 提供商名称

    Returns:
        对应的模型枚举类，如果不存在则返回 None
    """
    return MODEL_MAPPING.get(provider.lower())


def get_default_model(provider: str) -> Optional[str]:
    """
    获取指定提供商的默认模型。

    Args:
        provider: 提供商名称

    Returns:
        默认模型名称，如果提供商不存在则返回 None
    """
    model_enum = get_model_enum(provider)
    if not model_enum:
        return None

    # 返回每个枚举的第一个模型作为默认模型
    models = list(model_enum)
    return models[0].value if models else None
