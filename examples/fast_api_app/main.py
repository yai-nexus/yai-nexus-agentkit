# -*- coding: utf-8 -*-
"""
FastAPI 应用主入口文件。
负责应用的启动、依赖注入容器的创建和路由的组装。
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from yai_nexus_configuration import config

# --- 依赖项导入 ---
# 显式地从我们的包和应用模块中导入所需的类
from .api import chat
from yai_nexus_agentkit.llm import create_llm
from .core.services import ChatService


# --- 依赖注入容器 ---
class AppContainer:
    """
    一个简单的手动依赖注入 (DI) 容器。
    在应用启动时，这个类的实例将被创建，并负责实例化所有的服务和客户端。
    """

    def __init__(self):
        # 1. 从 yai-nexus-configuration 加载 LLM 配置列表
        llm_configs = config.get("llms", [])
        if not llm_configs:
            raise ValueError("在配置中未找到 'llms' 部分，请检查 pyproject.toml。")

        # 2. 使用第一个配置，通过工厂函数创建具体的 LLM 客户端
        #    这里创建的是一个 LangChain 的 ChatOpenAI 实例。
        self.llm_client = create_llm(llm_configs[0])

        # 3. 将具体的客户端实例注入到服务中
        self.chat_service = ChatService(llm=self.llm_client)


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
    # 1. 配置日志
    logging.basicConfig(
        level="INFO", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.info("应用开始启动...")

    # 2. 创建并赋值全局的依赖注入容器
    global container
    container = AppContainer()
    logging.info("依赖注入容器已创建。")

    # 3. 在容器创建后，再将路由包含进来
    app.include_router(chat.create_router(container))
    logging.info("API 路由已加载。")

    logging.info("应用启动完成。")
    yield
    # 在应用关闭时执行
    logging.info("应用开始关闭...")
    logging.info("应用关闭完成。")


# --- 创建 FastAPI 应用实例 ---
app = FastAPI(
    lifespan=lifespan,
    title="YAI-Nexus AgentKit - FastAPI 示例",
    description="此示例展示了如何使用 yai-nexus-agentkit 构建一个简单的 AI 聊天应用。",
    version="1.0.0",
)


# --- 应用运行说明 ---
# 要运行此应用:
# 1. 确保已安装所有依赖:
#    pip install -e ".[all,fastapi]"
# 2. 在项目根目录下创建一个 .env 文件，并填入您的 OPENAI_API_KEY。
#    示例: OPENAI_API_KEY="sk-..."
# 3. 在项目根目录下运行:
#    python -m examples.fast_api_app.main

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "examples.fast_api_app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
