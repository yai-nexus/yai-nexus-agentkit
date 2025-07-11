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
    LLMFactory,
    LLMProvider,
    LLMConfig,
    OpenAIModel,
    OpenRouterModel,
    DoubaoModel,
)
from langchain_core.messages import HumanMessage


async def demo_basic_usage():
    """演示基础的 LLMFactory 使用。"""
    print("=== 1. 基础 LLMFactory 使用 ===")

    factory = LLMFactory()

    # 使用 OpenAI (需要设置 OPENAI_API_KEY 环境变量)
    if os.getenv("OPENAI_API_KEY"):
        try:
            config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model=OpenAIModel.GPT_3_5_TURBO.value,
                api_key=os.getenv("OPENAI_API_KEY"),
            )

            factory.register_config("openai-basic", config)
            llm = factory.get_llm_client("openai-basic")
            response = await llm.ainvoke([HumanMessage(content="Hello, what's 2+2?")])
            print(f"OpenAI 回复: {response.content}")
        except Exception as e:
            print(f"OpenAI 示例失败: {e}")
    else:
        print("跳过 OpenAI 示例 (未设置 OPENAI_API_KEY)")


async def demo_doubao_usage():
    """演示豆包模型 DOUBAO_SEED_1_6_MODEL 的使用。"""
    print("\n=== 2. 豆包模型 DOUBAO_SEED_1_6_MODEL 测试 ===")

    factory = LLMFactory()

    # 使用豆包模型枚举 (测试 DOUBAO_SEED_1_6_MODEL)
    if os.getenv("DOUBAO_API_KEY"):
        try:
            config = LLMConfig(
                provider=LLMProvider.DOUBAO,
                model=DoubaoModel.DOUBAO_SEED_1_6_MODEL.value,
                api_key=os.getenv("DOUBAO_API_KEY"),
            )

            factory.register_config("doubao-seed", config)
            llm = factory.get_llm_client("doubao-seed")
            response = await llm.ainvoke(
                [HumanMessage(content="你好！请用中文回答，什么是人工智能？")]
            )
            print(
                f"豆包模型 {DoubaoModel.DOUBAO_SEED_1_6_MODEL.value} 回复: {response.content}"
            )
        except Exception as e:
            print(f"豆包模型 {DoubaoModel.DOUBAO_SEED_1_6_MODEL.value} 失败: {e}")
    else:
        print("跳过豆包示例 (未设置 DOUBAO_API_KEY)")


async def demo_model_enums():
    """演示如何结合使用 LLMProvider 和模型枚举来创建 LLM 实例。"""
    print("\n=== 2. 模型枚举使用 ===")
    factory = LLMFactory()

    # 使用 OpenAI 模型枚举
    if os.getenv("OPENAI_API_KEY"):
        try:
            config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model=OpenAIModel.GPT_3_5_TURBO.value,
                api_key=os.getenv("OPENAI_API_KEY"),
            )
            model_id = "openai-enum-demo"
            factory.register_config(model_id, config)
            llm = factory.get_llm_client(model_id)

            response = await llm.ainvoke(
                [HumanMessage(content="用中文回答：什么是人工智能？")]
            )
            print(f"使用模型枚举的回复: {response.content[:100]}...")
        except Exception as e:
            print(f"OpenAI 模型枚举示例失败: {e}")
    else:
        print("跳过 OpenAI 示例 (未设置 OPENAI_API_KEY)")

    # 使用豆包模型枚举 (测试 DOUBAO_SEED_1_6_MODEL)
    if os.getenv("DOUBAO_API_KEY"):
        try:
            config = LLMConfig(
                provider=LLMProvider.DOUBAO,
                model=DoubaoModel.DOUBAO_SEED_1_6_MODEL.value,
                api_key=os.getenv("DOUBAO_API_KEY"),
            )
            model_id = "doubao-enum-demo"
            factory.register_config(model_id, config)
            llm = factory.get_llm_client(model_id)

            response = await llm.ainvoke(
                [HumanMessage(content="你好！请用中文回答，什么是人工智能？")]
            )
            print(
                f"豆包模型 {DoubaoModel.DOUBAO_SEED_1_6_MODEL.value} 回复: {response.content}"
            )
        except Exception as e:
            print(f"豆包模型枚举示例失败: {e}")
    else:
        print("跳过豆包示例 (未设置 DOUBAO_API_KEY)")

    # 使用 OpenRouter 模型枚举
    if os.getenv("OPENROUTER_API_KEY"):
        try:
            config = LLMConfig(
                provider=LLMProvider.OPENROUTER,
                model=OpenRouterModel.GOOGLE_GEMINI_PRO.value,
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
            )
            model_id = "openrouter-enum-demo"
            factory.register_config(model_id, config)
            llm = factory.get_llm_client(model_id)

            response = await llm.ainvoke([HumanMessage(content="Hello from Gemini!")])
            print(f"OpenRouter + Gemini 回复: {response.content}")
        except Exception as e:
            print(f"OpenRouter 模型枚举示例失败: {e}")
    else:
        print("跳过 OpenRouter 示例 (未设置 OPENROUTER_API_KEY)")


async def demo_llm_factory():
    """演示如何使用 LLMFactory 同时管理多个 LLM 配置。"""
    print("\n=== 3. LLMFactory 多 LLM 管理 ===")

    # 1. 定义多个模型配置
    # 注意: provider 的值必须是 LLMProvider 枚举成员，而不是字符串
    configs = {
        "chat_model": LLMConfig(
            provider=LLMProvider.OPENAI,
            model=OpenAIModel.GPT_3_5_TURBO.value,
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
        "backup_model": LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model=OpenRouterModel.GOOGLE_GEMINI_PRO.value,
            api_key=os.getenv("OPENROUTER_API_KEY"),
        ),
    }

    # 2. 注册配置到工厂
    factory = LLMFactory()
    for model_id, config_obj in configs.items():
        # 只有在提供了 api_key 时才注册
        if config_obj.api_key:
            factory.register_config(model_id, config_obj)
        else:
            print(f"跳过注册模型 '{model_id}' (未提供 API Key)")

    # 3. 从工厂获取并使用不同的 LLM 客户端
    # 仅当 OPENAI_API_KEY 可用时才尝试获取
    if "chat_model" in factory._configs:
        try:
            chat_llm = factory.get_llm_client("chat_model")
            response = await chat_llm.ainvoke("Say 'Hello'")
            print(f"Chat Model (OpenAI) response: {response.content}")
        except Exception as e:
            print(f"使用 'chat_model' 失败: {e}")

    # 仅当 OPENROUTER_API_KEY 可用时才尝试获取
    if "backup_model" in factory._configs:
        try:
            backup_llm = factory.get_llm_client("backup_model")
            response = await backup_llm.ainvoke("Say 'Hi' in German")
            print(f"Backup Model (OpenRouter) response: {response.content}")
        except Exception as e:
            print(f"使用 'backup_model' 失败: {e}")


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
        await demo_doubao_usage()
        await demo_model_enums()
        await demo_llm_factory()

        print("\n✅ 所有示例执行完成！")

    except Exception as e:
        print(f"❌ 示例执行出错: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
