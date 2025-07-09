# -*- coding: utf-8 -*-
"""
FastAPI 应用主入口文件。
负责应用的启动、依赖注入容器的创建和路由的组装。
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from tortoise import Tortoise

# --- 依赖项导入 ---
from yai_nexus_configuration import NexusConfigManager

from .api import chat, conversations
from .configs import AllLLMConfigs
from .core.services import ChatService, ConversationService
from yai_nexus_agentkit.llm import create_llm
from yai_nexus_agentkit.persistence import (
    DatabaseConfig,
    TORTOISE_ORM_CONFIG_TEMPLATE,
    TortoiseRepository,
    PostgresCheckpoint,
    AgentConversation,
)


# --- 依赖注入容器 ---
class AppContainer:
    """
    一个简单的手动依赖注入 (DI) 容器。
    在应用启动时，这个类的实例将被创建，并负责实例化所有的服务和客户端。
    """

    chat_service: ChatService
    conversation_service: ConversationService
    db_config: DatabaseConfig
    checkpoint: PostgresCheckpoint


# --- FastAPI 应用生命周期管理 ---
# 这个变量将在 lifespan 中被赋值，以便路由模块可以访问
container: "AppContainer"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 的生命周期管理器。
    在应用启动时执行 yield之前的部分，在关闭时执行 yield 之后的部分。
    """
    # 在应用启动时执行
    # 0. 加载 .env 文件中的环境变量
    load_dotenv()

    # 1. 配置日志
    logging.basicConfig(level="INFO", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.info("应用开始启动...")

    # 2. 初始化配置管理器并加载配置
    logging.info("初始化配置管理器...")
    manager = NexusConfigManager.with_file(base_path="configs")
    manager.register(AllLLMConfigs)
    all_llm_configs = manager.get_config(AllLLMConfigs)
    logging.info("LLM 配置已加载。")

    if not all_llm_configs.llms:
        raise ValueError("在 'configs/DEFAULT_GROUP/llms.json' 中未找到或加载 'llms' 失败。")

    # 3. 根据环境变量选择 LLM 配置
    model_to_use = os.getenv("MODEL_TO_USE")
    selected_llm_config = None

    if model_to_use:
        logging.info(f"环境变量 MODEL_TO_USE 设置为: {model_to_use}")
        for llm_config in all_llm_configs.llms:
            if llm_config.model == model_to_use:
                selected_llm_config = llm_config
                break
        if not selected_llm_config:
            raise ValueError(f"在配置中未找到模型: {model_to_use}")
    else:
        logging.info("未设置环境变量 MODEL_TO_USE，使用第一个可用的 LLM 配置。")
        selected_llm_config = all_llm_configs.llms[0]

    logging.info(f"正在使用模型: {selected_llm_config.provider}/{selected_llm_config.model}")

    # 4. 初始化数据库配置
    logging.info("初始化数据库配置...")
    db_config = DatabaseConfig.from_env()
    logging.info(f"数据库配置已加载，URL: {db_config.db_url[:20]}...")

    # 5. 初始化数据库连接
    logging.info("初始化数据库连接...")
    tortoise_config = TORTOISE_ORM_CONFIG_TEMPLATE.copy()
    tortoise_config["connections"]["default"] = db_config.db_url
    
    await Tortoise.init(config=tortoise_config)
    if db_config.generate_schemas:
        await Tortoise.generate_schemas()
    logging.info("数据库连接已初始化。")

    # 6. 初始化 Checkpoint
    logging.info("初始化 Checkpoint...")
    checkpoint = PostgresCheckpoint(db_config)
    await checkpoint.setup()
    logging.info("Checkpoint 已初始化。")

    # 7. 创建核心服务
    logging.info("创建核心服务...")
    llm_client = create_llm(selected_llm_config.model_dump())
    chat_service = ChatService(llm=llm_client)
    
    # 创建对话服务
    conversation_repository = TortoiseRepository(model_cls=AgentConversation)
    conversation_service = ConversationService(repo=conversation_repository)
    logging.info("核心服务已创建。")

    # 8. 创建并赋值全局的依赖注入容器
    global container
    container = AppContainer()
    container.chat_service = chat_service
    container.conversation_service = conversation_service
    container.db_config = db_config
    container.checkpoint = checkpoint
    logging.info("依赖注入容器已创建并填充。")

    # 9. 加载 API 路由
    logging.info("API 路由已加载。")
    app.include_router(chat.router)
    app.include_router(conversations.router)

    logging.info("应用启动完成。")
    yield
    # 在应用关闭时执行
    logging.info("应用开始关闭...")
    
    # 清理 Checkpoint 资源
    logging.info("清理 Checkpoint 资源...")
    await checkpoint.cleanup()
    
    # 关闭数据库连接
    logging.info("关闭数据库连接...")
    await Tortoise.close_connections()
    
    # 关闭配置管理器，释放资源（如 watcher 线程）
    manager.close()
    logging.info("应用关闭完成。")


# --- FastAPI 应用创建 ---
app = FastAPI(
    title="YAI Nexus AgentKit Example",
    description="一个展示 YAI Nexus AgentKit 功能的示例应用",
    version="0.1.0",
    lifespan=lifespan,
    debug=True,
)


# --- 应用运行说明 ---
# 要运行此应用:
# 1. 确保已安装所有依赖:
#    pip install -e ".[all,fastapi]"
# 2. 在项目根目录下创建一个 .env 文件，并填入您的 OPENAI_API_KEY 和 OPENROUTER_API_KEY。
#    示例:
#    OPENAI_API_KEY="sk-..."
#    OPENROUTER_API_KEY="sk-or-..."
# 3. 在项目根目录下运行:
#    python -m examples.fast_api_app.main
# 4. (可选) 设置 MODEL_TO_USE 环境变量来选择不同的模型
#    export MODEL_TO_USE="google/gemini-2.5-pro"

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "examples.fast_api_app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
