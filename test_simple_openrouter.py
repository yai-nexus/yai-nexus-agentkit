#!/usr/bin/env python3
import asyncio
import os
from yai_nexus_agentkit import create_llm, OpenRouterModel
from langchain_core.messages import HumanMessage


async def test_openrouter():
    """测试 OpenRouter 的基础功能。"""
    if not os.getenv("OPENROUTER_API_KEY"):
        print("未设置 OPENROUTER_API_KEY")
        return

    # 先尝试 Anthropic Claude 模型
    config = {
        "provider": "openrouter",
        "model": OpenRouterModel.ANTHROPIC_CLAUDE_3_5_SONNET.value,  # "anthropic/claude-3.5-sonnet"
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "base_url": "https://openrouter.ai/api/v1",
    }

    print(f"测试 OpenRouter 模型: {config['model']}")

    try:
        llm = create_llm(config)
        response = await llm.ainvoke([HumanMessage(content="Hello! Please respond with just 'Hi there!'")])
        print(f"✅ 成功调用: {response.content}")
    except Exception as e:
        print(f"❌ 调用失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_openrouter())
