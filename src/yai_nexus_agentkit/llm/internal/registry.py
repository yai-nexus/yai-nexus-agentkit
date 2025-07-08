# -*- coding: utf-8 -*-
"""提供商注册表实现。"""

from typing import Any, Dict, Callable

from langchain_core.language_models import BaseChatModel

from ..providers import LLMProvider
from .creators import (
    create_openai_client,
    create_zhipu_client,
    create_anthropic_client,
    create_openrouter_client,
    create_tongyi_client,
)


# 提供商注册表：将 LLMProvider 映射到对应的创建函数
PROVIDER_REGISTRY: Dict[LLMProvider, Callable[[Dict[str, Any]], BaseChatModel]] = {
    LLMProvider.OPENAI: create_openai_client,
    LLMProvider.ZHIPU: create_zhipu_client,
    LLMProvider.ANTHROPIC: create_anthropic_client,
    LLMProvider.OPENROUTER: create_openrouter_client,
    LLMProvider.TONGYI: create_tongyi_client,
}