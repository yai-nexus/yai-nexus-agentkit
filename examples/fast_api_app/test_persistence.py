#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试持久化层集成的简单脚本。
用于验证 ConversationService 的 CRUD 功能。
"""

import asyncio
from dotenv import load_dotenv
from tortoise import Tortoise

from yai_nexus_agentkit.persistence import (
    DatabaseConfig,
    TORTOISE_ORM_CONFIG_TEMPLATE,
    TortoiseRepository,
    AgentConversation,
)
from core.services import ConversationService


async def test_conversation_service():
    """测试 ConversationService 的基本功能"""
    # 加载环境变量
    load_dotenv()

    # 初始化数据库配置
    db_config = DatabaseConfig.from_env()
    print(f"数据库配置: {db_config.db_url[:20]}...")

    # 初始化数据库连接
    tortoise_config = TORTOISE_ORM_CONFIG_TEMPLATE.copy()
    tortoise_config["connections"]["default"] = db_config.db_url

    try:
        await Tortoise.init(config=tortoise_config)
        if db_config.generate_schemas:
            await Tortoise.generate_schemas()
        print("数据库连接已初始化")

        # 创建服务实例
        conversation_repository = TortoiseRepository(model_cls=AgentConversation)
        conversation_service = ConversationService(repo=conversation_repository)

        # 测试创建对话
        print("\n--- 测试创建对话 ---")
        conversation = await conversation_service.create_conversation(
            title="测试对话", metadata={"test": True, "created_by": "test_script"}
        )
        print(f"创建对话成功: {conversation.id}")
        print(f"对话标题: {conversation.title}")
        print(f"对话元数据: {conversation.metadata_}")

        # 测试获取对话
        print("\n--- 测试获取对话 ---")
        retrieved = await conversation_service.get_conversation(str(conversation.id))
        if retrieved:
            print(f"获取对话成功: {retrieved.id}")
            print(f"对话标题: {retrieved.title}")
        else:
            print("获取对话失败")

        # 测试更新对话
        print("\n--- 测试更新对话 ---")
        updated = await conversation_service.update_conversation(
            str(conversation.id),
            title="更新后的标题",
            metadata={"test": True, "updated": True},
        )
        if updated:
            print(f"更新对话成功: {updated.title}")
            print(f"更新后元数据: {updated.metadata_}")
        else:
            print("更新对话失败")

        # 测试列出对话
        print("\n--- 测试列出对话 ---")
        conversations = await conversation_service.list_conversations(limit=5)
        print(f"找到 {len(conversations)} 个对话")
        for conv in conversations:
            print(f"  - {conv.id}: {conv.title}")

        # 测试统计数量
        print("\n--- 测试统计数量 ---")
        count = await conversation_service.count_conversations()
        print(f"对话总数: {count}")

        # 测试删除对话
        print("\n--- 测试删除对话 ---")
        success = await conversation_service.delete_conversation(str(conversation.id))
        if success:
            print("删除对话成功")
        else:
            print("删除对话失败")

        # 验证删除
        deleted = await conversation_service.get_conversation(str(conversation.id))
        if deleted is None:
            print("删除验证成功：对话已不存在")
        else:
            print("删除验证失败：对话仍然存在")

        print("\n--- 测试完成 ---")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # 关闭数据库连接
        await Tortoise.close_connections()
        print("数据库连接已关闭")


if __name__ == "__main__":
    print("开始测试持久化层集成...")
    asyncio.run(test_conversation_service())
