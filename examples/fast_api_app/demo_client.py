# -*- coding: utf-8 -*-
"""
演示客户端
展示如何使用不同层次的 API
"""

import asyncio
import aiohttp
import json


class ChatClient:
    """演示聊天客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def test_simple_mode(self):
        """测试简单模式"""
        print("=== 测试简单模式 ===")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/simple", json={"message": "Hello, world!"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"响应: {result['response']}")
                else:
                    print(f"错误: {response.status}")

    async def test_basic_sse(self):
        """测试基础 SSE 模式"""
        print("\n=== 测试基础 SSE 模式 ===")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/stream-basic",
                json={"message": "Tell me a story"},
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                            print(f"事件: {data}")
                else:
                    print(f"错误: {response.status}")

    async def test_advanced_mode(self):
        """测试高级 AG-UI 模式"""
        print("\n=== 测试高级 AG-UI 模式 ===")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/stream-advanced",
                json={"id": "task-123", "query": "Explain quantum computing"},
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            print(f"AG-UI 事件: {data}")
                else:
                    print(f"错误: {response.status}")

    async def check_capabilities(self):
        """检查 API 能力"""
        print("\n=== 检查 API 能力 ===")

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/chat/capabilities") as response:
                if response.status == 200:
                    capabilities = await response.json()
                    print(f"支持的功能: {json.dumps(capabilities, indent=2)}")
                else:
                    print(f"错误: {response.status}")

    async def run_all_tests(self):
        """运行所有测试"""
        await self.check_capabilities()
        await self.test_simple_mode()
        await self.test_basic_sse()
        await self.test_advanced_mode()


async def main():
    """主函数"""
    client = ChatClient()
    await client.run_all_tests()


if __name__ == "__main__":
    print("演示客户端启动...")
    print("确保 FastAPI 服务器正在运行: python -m examples.fast_api_app.main")
    asyncio.run(main())
