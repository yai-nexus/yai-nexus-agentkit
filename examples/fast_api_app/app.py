# -*- coding: utf-8 -*-
from dependency_injector import containers, providers
from fastapi import FastAPI
from yai_nexus_agentkit.llm import LLMFactory
from yai_nexus_agentkit.persistence import (
    DatabaseConfig,
    PostgresCheckpoint,
    ConversationRepository,
)
from .core.services import ChatService, ConversationService


class Container(containers.DeclarativeContainer):
    """
    依赖注入容器
    """

    config = providers.Configuration()
    llm_factory = providers.Singleton(LLMFactory)
    db_config = providers.Singleton(DatabaseConfig, db_url=config.db.url)
    checkpoint_repository = providers.Singleton(PostgresCheckpoint, config=db_config)
    conversation_repository = providers.Singleton(
        ConversationRepository, db_config=db_config
    )
    chat_service = providers.Factory(
        ChatService,
        llm_factory=llm_factory,
        checkpoint_repo=checkpoint_repository,
    )
    conversation_service = providers.Factory(
        ConversationService, repo=conversation_repository
    )


container = Container()
app = FastAPI(
    title="AgentKit FastAPI Demo",
    description="一个使用 AgentKit 构建的 FastAPI 示例应用",
    summary="AgentKit FastAPI Demo",
    version="1.0.0",
)
