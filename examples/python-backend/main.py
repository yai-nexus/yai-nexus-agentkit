#!/usr/bin/env python3
"""
Python backend example for yai-nexus-fekit, using AGUIAdapter.
"""
from fastapi import FastAPI, Request
from loguru import logger
from ag_ui.core import RunAgentInput

from config import load_environment, check_environment_variables, get_server_config
from middleware import setup_middleware
from agent import create_agui_adapter
from handlers import root, health_check, agui_agent

# 初始化配置
load_environment()
check_environment_variables()

# 创建 FastAPI 应用
app = FastAPI(
    title="YAI Nexus FeKit Python Backend",
    description="Example backend for demonstrating yai-nexus-agentkit integration",
    version="0.1.0",
)

# 设置中间件
setup_middleware(app)

# 创建 AGUIAdapter
agui_adapter = create_agui_adapter()

# 注册路由
@app.get("/")
async def root_handler():
    return await root()

@app.get("/health")
async def health_handler():
    return await health_check()

@app.post("/agui")
async def agui_handler(request_data: RunAgentInput, request: Request):
    return await agui_agent(request_data, request, agui_adapter)

if __name__ == "__main__":
    import uvicorn
    
    # 获取服务器配置
    config = get_server_config()
    
    logger.info("Starting YAI Nexus FeKit Python Backend...", **config)
    logger.info("Backend will be available at: http://{}:{}".format(config["host"], config["port"]))
    logger.info("API documentation at: http://{}:{}/docs".format(config["host"], config["port"]))
    logger.info("Log files will be stored in hourly directories under logs/")

    uvicorn.run(
        "main:app", 
        host=config["host"], 
        port=config["port"], 
        reload=True, 
        log_level="info"
    )