"""
LLM 设置模块 - 使用 agentkit 的 LLM 工厂创建 LLM 实例
"""
import os
from loguru import logger
from yai_nexus_agentkit.llm import LLMFactory, LLMConfig, LLMProvider


def create_llm():
    """使用 agentkit 的 LLM 工厂创建合适的 LLM 实例"""
    factory = LLMFactory()
    
    # 优先使用 Doubao
    if os.getenv("DOUBAO_API_KEY"):
        logger.info("Using Doubao LLM")
        config = LLMConfig(
            provider=LLMProvider.DOUBAO,
            model="doubao-seed-1-6-250615",
            api_key=os.getenv("DOUBAO_API_KEY"),
            base_url="https://ark.cn-beijing.volces.com/api/v3"
        )
        factory.register_config("doubao", config)
        return factory.get_llm_client("doubao")
    
    # 回退到 OpenAI
    elif os.getenv("OPENAI_API_KEY"):
        logger.info("Using OpenAI GPT-4o")
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        factory.register_config("openai", config)
        return factory.get_llm_client("openai")
    
    else:
        raise ValueError("No suitable LLM configuration found")