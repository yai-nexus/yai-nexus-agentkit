#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时调试脚本，用于测试与阿里云 DashScope API 的连接。
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取 API 密钥
api_key = os.getenv("DASHSCOPE_API_KEY")
print(f"API Key: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")

if not api_key:
    print("错误：DASHSCOPE_API_KEY 环境变量未设置")
    exit(1)

try:
    import dashscope
    from dashscope import Generation

    # 设置API密钥
    dashscope.api_key = api_key

    # 尝试不同的模型
    models_to_test = ["qwen-turbo", "qwen-plus", "qwen-max", "qwen2-7b-instruct", "qwen2-72b-instruct"]

    for model_name in models_to_test:
        print(f"\n正在测试模型: {model_name}")

        try:
            response = Generation.call(model=model_name, prompt="你好", max_tokens=50)

            print(f"状态码: {response.status_code}")

            if response.status_code == 200:
                print(f"✅ 成功！回复内容: {response.output.text}")
                break  # 找到可用模型，停止测试
            else:
                print(f"❌ 失败 - 错误代码: {response.code}, 消息: {response.message}")

        except Exception as e:
            print(f"❌ 异常: {type(e).__name__}: {e}")

except ImportError as e:
    print(f"导入错误: {e}")
except Exception as e:
    print(f"发生异常: {type(e).__name__}: {e}")
