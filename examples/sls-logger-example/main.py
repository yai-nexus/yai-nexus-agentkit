#!/usr/bin/env python3
"""
SLS 日志集成简化示例

演示如何用最简单的方式将 Loguru 日志发送到阿里云 SLS。

这个示例展示了：
1. 从环境变量自动配置 SLS
2. 发送基本的日志消息  
3. 优雅停机确保日志完整发送

运行前需要设置环境变量：
export SLS_ENDPOINT=cn-hangzhou.log.aliyuncs.com
export SLS_AK_ID=your_access_key_id
export SLS_AK_KEY=your_access_key_secret
export SLS_PROJECT=your_project
export SLS_LOGSTORE=your_logstore
"""

import os
import asyncio
import time
from loguru import logger
from yai_loguru_support.sls import AliyunSlsSink
from yai_loguru_support.utils import create_production_setup


async def main():
    """主函数 - 演示 SLS 日志集成的核心流程"""
    
    # 1. 检查必要的环境变量
    required_vars = ["SLS_ENDPOINT", "SLS_AK_ID", "SLS_AK_KEY", "SLS_PROJECT", "SLS_LOGSTORE"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"错误: 缺少必要的环境变量: {missing_vars}")
        print("请参考 README.md 设置环境变量。")
        return
        
    try:
        # 2. 从环境变量创建 SLS Sink
        sls_sink = AliyunSlsSink.from_env()
        
        # 3. 添加到 loguru (发送 INFO 及以上级别日志到 SLS)
        logger.add(sls_sink, serialize=True, level="INFO")
        
        # 4. 设置优雅停机 (确保程序退出前日志完整发送)
        create_production_setup([sls_sink])
        
        logger.info("SLS 日志集成已启用", 
                   project=os.getenv("SLS_PROJECT"), 
                   logstore=os.getenv("SLS_LOGSTORE"))
        
        # 5. 发送示例日志
        logger.info("这是一个简单的 INFO 日志")
        logger.warning("这是一个 WARNING 日志", user_id="demo_user")
        
        # 带上下文的日志
        logger.bind(request_id="req_123", action="demo").info("带上下文的日志")
        
        # 异常日志演示
        try:
            result = 1 / 0
        except ZeroDivisionError:
            logger.exception("这是一个自动捕获的异常日志")
            
        # 结构化日志演示
        start_time = time.time()
        await asyncio.sleep(0.1)  # 模拟一些工作
        duration = time.time() - start_time
        
        logger.info("操作完成", 
                   operation="demo_task",
                   duration_ms=round(duration * 1000, 2),
                   success=True)
        
        logger.info("示例运行结束，等待日志发送...")
        
        # 6. 等待批处理发送 (SLS 使用批量发送优化性能)
        await asyncio.sleep(5)
        
        logger.info("SLS 日志示例完成")
        
    except Exception as e:
        print(f"SLS 集成失败: {e}")
        print("请检查环境变量配置和网络连接。")


if __name__ == "__main__":
    print("启动 SLS 日志集成示例...")
    asyncio.run(main())