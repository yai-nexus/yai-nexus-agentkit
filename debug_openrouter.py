#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenRouter 测试脚本"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 加载环境变量
load_dotenv()

# 检查 API 密钥
api_key = os.getenv("OPENROUTER_API_KEY")
print(f"API 密钥: {api_key[:10]}...{api_key[-5:]}" if api_key else "未找到 API 密钥")

# 直接测试 OpenRouter API (添加必要的请求头)
try:
    llm = ChatOpenAI(
        model="google/gemini-2.5-pro",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
        default_headers={
            "HTTP-Referer": "https://localhost:8000",  # OpenRouter 需要此头
            "X-Title": "yai-nexus-agentkit",  # 可选，用于 OpenRouter 的使用统计
        },
    )

    print("正在测试 OpenRouter (带必要请求头)...")

    message = HumanMessage(content="你好，请简短地介绍一下你自己。")
    response = llm.invoke([message])

    print(f"成功！回复: {response.content}")

except Exception as e:
    print(f"错误: {e}")
    print(f"错误类型: {type(e).__name__}")

    # 如果仍然失败，尝试不同的请求头组合
    if "401" in str(e):
        print("\n尝试其他请求头配置...")
        try:
            llm2 = ChatOpenAI(
                model="google/gemini-2.5-pro",
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.7,
                default_headers={
                    "HTTP-Referer": "https://github.com/harrytang/yai-nexus-agentkit",
                },
            )
            response2 = llm2.invoke([message])
            print(f"成功（第二次尝试）！回复: {response2.content}")
        except Exception as e2:
            print(f"第二次尝试也失败: {e2}")
