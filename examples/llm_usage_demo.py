#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 功能使用示例。

这个示例展示了如何使用 yai-nexus-agentkit 的各种 LLM 功能：
1. 基础的 create_llm() 工厂函数
2. 工厂类 LLMFactory 管理多个 LLM
3. 模型枚举的类型安全使用
4. 业务抽象层的便捷接口
"""

import asyncio
import os

from yai_nexus_agentkit import (
    create_llm,
    LLMFactory,
    LLMProvider,
    OpenAIModel,
    OpenRouterModel,
    DoubaoModel,
)
from langchain_core.messages import HumanMessage


async def demo_basic_usage():
    """演示基础的 create_llm() 使用。"""
    print("=== 1. 基础 create_llm() 使用 ===")

    # 使用 OpenAI (需要设置 OPENAI_API_KEY 环境变量)
    if os.getenv("OPENAI_API_KEY"):
        config = {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": os.getenv("OPENAI_API_KEY"),
        }

        llm = create_llm(config)
        response = await llm.ainvoke([HumanMessage(content="Hello, what's 2+2?")])
        print(f"OpenAI 回复: {response.content}")
    else:
        print("跳过 OpenAI 示例 (未设置 OPENAI_API_KEY)")


async def demo_model_enums():
    """演示模型枚举的类型安全使用。"""
    print("\n=== 2. 模型枚举使用 ===")

    # 使用 OpenAI 模型枚举
    if os.getenv("OPENAI_API_KEY"):
        config = {
            "provider": LLMProvider.OPENAI.value,
            "model": OpenAIModel.GPT_3_5_TURBO.value,  # 类型安全的模型选择
            "api_key": os.getenv("OPENAI_API_KEY"),
        }

        llm = create_llm(config)
        response = await llm.ainvoke([HumanMessage(content="用中文回答：什么是人工智能？")])
        print(f"使用模型枚举的回复: {response.content[:100]}...")

    # 使用豆包模型枚举 (测试 DOUBAO_SEED_1_6_MODEL)
    if os.getenv("DOUBAO_API_KEY"):
        config = {
            "provider": LLMProvider.DOUBAO.value,
            "model": DoubaoModel.DOUBAO_SEED_1_6_MODEL.value,  # "doubao-seed-1-6-250615"
            "api_key": os.getenv("DOUBAO_API_KEY"),
        }

        llm = create_llm(config)
        response = await llm.ainvoke([HumanMessage(content="你好！请用中文回答，什么是人工智能？")])
        print(f"豆包模型 {DoubaoModel.DOUBAO_SEED_1_6_MODEL.value} 回复: {response.content}")
    else:
        print("跳过豆包示例 (未设置 DOUBAO_API_KEY)")

    # 使用 OpenRouter 模型枚举
    if os.getenv("OPENROUTER_API_KEY"):
        config = {
            "provider": LLMProvider.OPENROUTER.value,
            "model": OpenRouterModel.GOOGLE_GEMINI_PRO.value,  # "google/gemini-pro"
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "base_url": "https://openrouter.ai/api/v1",
        }

        llm = create_llm(config)
        response = await llm.ainvoke([HumanMessage(content="Hello from Gemini!")])
        print(f"OpenRouter + Gemini 回复: {response.content}")
    else:
        print("跳过 OpenRouter 示例 (未设置 OPENROUTER_API_KEY)")


async def demo_llm_factory():
    """演示 LLMFactory 管理多个 LLM。"""
    print("\n=== 3. LLMFactory 多 LLM 管理 ===")

    configs = []

    # 添加可用的 LLM 配置
    if os.getenv("OPENAI_API_KEY"):
        configs.append(
            {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "api_key": os.getenv("OPENAI_API_KEY"),
            }
        )

    if os.getenv("OPENROUTER_API_KEY"):
        configs.append(
            {
                "provider": "openrouter",
                "model": "google/gemini-pro",
                "api_key": os.getenv("OPENROUTER_API_KEY"),
                "base_url": "https://openrouter.ai/api/v1",
            }
        )

    if not configs:
        print("跳过 LLMFactory 示例 (未设置任何 API 密钥)")
        return

    # 创建工厂
    factory = LLMFactory(configs)
    print(f"可用的提供商: {factory.list_providers()}")

    # 使用不同的 LLM
    for provider_name in factory.list_providers():
        try:
            client = factory.get_client_by_name(provider_name)
            response = await client.ainvoke([HumanMessage(content=f"Hi from {provider_name}!")])
            print(f"{provider_name} 回复: {response.content}")
        except Exception as e:
            print(f"{provider_name} 调用失败: {e}")


async def main():
    """主函数，运行所有示例。"""
    print("🚀 yai-nexus-agentkit LLM 功能演示")
    print("请确保设置了相应的 API 密钥环境变量:")
    print("- OPENAI_API_KEY (用于 OpenAI 示例)")
    print("- DOUBAO_API_KEY (用于豆包示例)")
    print("- OPENROUTER_API_KEY (用于 OpenRouter 示例)")
    print()

    try:
        await demo_basic_usage()
        await demo_model_enums()
        await demo_llm_factory()

        print("\n✅ 所有示例执行完成！")

    except Exception as e:
        print(f"❌ 示例执行出错: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
