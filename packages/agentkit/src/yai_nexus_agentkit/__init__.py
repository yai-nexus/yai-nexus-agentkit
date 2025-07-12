# -*- coding: utf-8 -*-
"""
yai-nexus-agentkit: 一个灵活、可扩展的智能体开发套件。
"""

from .llm import (
    LLMFactory,
    llm_factory,
    BaseChatModel,
    LLMConfig,
    LLMProvider,
    OpenAIModel,
    AnthropicModel,
    ZhipuModel,
    TongyiModel,
    DoubaoModel,
    OpenRouterModel,
)

from .adapter import (
    BasicSSEAdapter,
    SSEEvent,
    AGUIAdapter,
    Task,
)

from .persistence import (
    DatabaseConfig,
    TORTOISE_ORM_CONFIG_TEMPLATE,
    TortoiseRepository,
    ConversationRepository,
    PostgresCheckpoint,
    AgentConversation,
    AgentMessage,
)

from .core.logger_config import (
    logger,
    get_logger,
    configure_logging,
    LoggerConfigurator,
    LogPathStrategy,
)

__all__ = [
    # LLM 核心功能
    "LLMFactory",
    "llm_factory",
    "BaseChatModel",
    # 配置和提供商
    "LLMConfig",
    "LLMProvider",
    # 模型枚举
    "OpenAIModel",
    "AnthropicModel",
    "ZhipuModel",
    "TongyiModel",
    "DoubaoModel",
    "OpenRouterModel",
    # 适配器
    "BasicSSEAdapter",
    "SSEEvent",
    "AGUIAdapter",
    "Task",
    # 持久化
    "DatabaseConfig",
    "TORTOISE_ORM_CONFIG_TEMPLATE",
    "TortoiseRepository",
    "ConversationRepository",
    "PostgresCheckpoint",
    "AgentConversation",
    "AgentMessage",
    # 日志系统
    "logger",
    "get_logger",
    "configure_logging",
    "LoggerConfigurator",
    "LogPathStrategy",
]
