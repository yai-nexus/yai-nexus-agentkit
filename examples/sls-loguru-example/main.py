#!/usr/bin/env python3
"""
SLS 日志集成简化示例

演示如何用最简单的方式将 Loguru 日志发送到阿里云 SLS。

这个示例展示了：
1. 从环境变量自动配置 SLS
2. 使用新的生命周期管理 API (astart/astop)
3. 异步上下文管理器的优雅用法
4. 发送基本的日志消息
5. 优雅停机确保日志完整发送

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
from dotenv import load_dotenv
from loguru import logger
from yai_loguru_support import setup_logging
from yai_loguru_support.sls import AliyunSlsSink
# from yai_loguru_support.utils import create_production_setup  # 不再需要手动设置优雅停机


async def main():
    """主函数 - 演示 SLS 日志集成的核心流程"""
    
    # 1. 设置统一的基础日志配置 (控制台 + 文件)
    # 使用根目录的 logs 文件夹，与其他服务保持一致
    setup_logging("sls-loguru-example", {
        "level": "info",
        "console": {"enabled": True, "pretty": True},
        "file": {"enabled": True, "strategy": "hourly", "baseDir": "../../logs"}
    })
    
    logger.info("启动 SLS 日志集成示例", service="sls-loguru-example")
    
    # 2. 检查必要的环境变量
    required_vars = ["SLS_ENDPOINT", "SLS_AK_ID", "SLS_AK_KEY", "SLS_PROJECT", "SLS_LOGSTORE"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error("缺少必要的环境变量", missing_vars=missing_vars)
        logger.error("请参考 README.md 设置环境变量")
        return
    
    try:
        # 3. 使用异步上下文管理器创建和管理 SLS Sink (推荐方式)
        async with AliyunSlsSink.from_env() as sls_sink:
            # 4. 添加到 loguru (发送 INFO 及以上级别日志到 SLS)
            logger.add(sls_sink, serialize=True, level="INFO")
            
            await demo_logging_with_sls(sls_sink)
            
            # 异步上下文管理器会自动处理 astop()
            logger.info("异步上下文管理器示例完成")
        
        # 演示手动生命周期管理方式
        await demo_manual_lifecycle()
        
    except Exception as e:
        print(f"SLS 集成失败: {e}")
        print("请检查环境变量配置和网络连接。")


        
async def demo_logging_with_sls(sls_sink):
    """演示使用 SLS 进行各种日志记录的功能"""
    
    logger.info("SLS 日志集成已启用", 
               project=os.getenv("SLS_PROJECT"), 
               logstore=os.getenv("SLS_LOGSTORE"))
    
    # 7. 发送示例日志
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
    
    # 8. 等待批处理发送 (SLS 使用批量发送优化性能)
    await asyncio.sleep(5)


async def demo_manual_lifecycle():
    """演示手动生命周期管理的方式"""
    
    logger.info("=== 演示手动生命周期管理 ===")
    
    # 手动创建和管理 SLS Sink
    sls_sink = AliyunSlsSink.from_env()
    
    try:
        # 手动启动
        await sls_sink.astart()
        logger.add(sls_sink, serialize=True, level="INFO")
        
        logger.info("手动生命周期管理示例")
        
    finally:
        # 手动关闭
        await sls_sink.astop()
        logger.info("手动关闭完成")



if __name__ == "__main__":
    print("启动 SLS 日志集成示例...")
    load_dotenv()
    asyncio.run(main())