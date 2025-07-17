"""
配置管理模块 - 环境变量检查和应用配置
"""
import os
from loguru import logger
from dotenv import load_dotenv
from yai_loguru_support import setup_dev_logging


def load_environment():
    """加载环境变量和初始化日志系统"""
    load_dotenv()
    setup_dev_logging("python-backend")


def check_environment_variables():
    """检查必要的环境变量是否已设置"""
    # 优先检查 Doubao API Key
    doubao_key = os.getenv("DOUBAO_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not any([doubao_key, openai_key]):
        logger.error(
            "FATAL: No API key found. Please set DOUBAO_API_KEY or OPENAI_API_KEY"
        )
        raise ValueError("At least one LLM API key is required to run the application.")

    if doubao_key:
        logger.info("DOUBAO_API_KEY is configured.")
    elif openai_key:
        logger.info("OPENAI_API_KEY is configured.")


def get_server_config():
    """获取服务器配置"""
    return {
        "host": os.getenv("HOST", "127.0.0.1"),
        "port": int(os.getenv("PORT", "8000")),
        "environment": os.getenv("ENVIRONMENT", "development")
    }