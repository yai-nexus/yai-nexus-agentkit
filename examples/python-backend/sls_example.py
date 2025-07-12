#!/usr/bin/env python3
"""
SLS 集成示例

演示如何在生产环境中使用 yai-loguru-support 包集成阿里云 SLS。

这个示例展示了：
1. 如何配置和使用 AliyunSlsSink
2. 自动化的优雅停机
3. 监控和告警设置
4. 与 FastAPI 的集成

运行前需要设置环境变量：
export SLS_ENDPOINT=cn-hangzhou.log.aliyuncs.com
export SLS_AK_ID=your_access_key_id
export SLS_AK_KEY=your_access_key_secret
export SLS_PROJECT=your_project
export SLS_LOGSTORE=your_logstore
export ENV=production
"""

import os
import asyncio
from yai_nexus_agentkit.core.logging import logger, get_logger

# 检查是否可以导入 SLS 支持
try:
    from yai_loguru_support.sls import AliyunSlsSink, SlsConfig
    from yai_loguru_support.utils import setup_graceful_shutdown, create_production_setup
    from yai_loguru_support.monitoring import setup_monitoring, ConsoleAlertChannel, LogAlertChannel
    SLS_AVAILABLE = True
except ImportError as e:
    print(f"SLS support not available: {e}")
    print("Install with: pip install ../../packages/loguru-support[sls]")
    SLS_AVAILABLE = False


def setup_sls_logging():
    """设置 SLS 日志集成（仅在生产环境且有配置时）"""
    
    if not SLS_AVAILABLE:
        logger.warning("SLS support not available, using local logging only")
        return None
        
    # 只在生产环境启用 SLS
    if os.getenv("ENV") != "production":
        logger.info("Non-production environment, SLS disabled")
        return None
        
    # 检查必要的环境变量
    required_vars = ["SLS_ENDPOINT", "SLS_AK_ID", "SLS_AK_KEY", "SLS_PROJECT", "SLS_LOGSTORE"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"SLS configuration incomplete, missing: {missing_vars}")
        return None
        
    try:
        # 创建 SLS sink
        sls_config = SlsConfig(
            endpoint=os.environ["SLS_ENDPOINT"],
            access_key_id=os.environ["SLS_AK_ID"],
            access_key=os.environ["SLS_AK_KEY"],
            project=os.environ["SLS_PROJECT"],
            logstore=os.environ["SLS_LOGSTORE"],
            topic=os.getenv("SLS_TOPIC", "python-backend"),
            source=os.getenv("SLS_SOURCE", "yai-nexus-agentkit"),
            
            # 优化配置
            batch_size=100,
            flush_interval=5.0,
            max_retries=3,
            enable_metrics=True
        )
        
        sls_sink = AliyunSlsSink(sls_config)
        
        # 添加到 loguru（只发送 INFO 及以上级别的日志到 SLS）
        logger.add(sls_sink, serialize=True, level="INFO")
        
        logger.info("SLS logging enabled", 
                   endpoint=sls_config.endpoint,
                   project=sls_config.project,
                   logstore=sls_config.logstore)
        
        return sls_sink
        
    except Exception as e:
        logger.error(f"Failed to setup SLS logging: {e}")
        return None


def setup_monitoring_example(sls_sink=None):
    """设置监控和告警示例"""
    
    if not SLS_AVAILABLE or not sls_sink:
        logger.info("Monitoring setup skipped (no SLS sink)")
        return None
        
    try:
        # 设置监控
        sinks = {"sls": sls_sink}
        
        # 配置告警通道
        alert_channels = [
            ConsoleAlertChannel(),  # 控制台告警
            LogAlertChannel("sls_alerts")  # 日志告警
        ]
        
        # 如果有 webhook 配置，也可以添加
        webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        if webhook_url:
            from yai_loguru_support.monitoring import WebhookAlertChannel
            alert_channels.append(WebhookAlertChannel(webhook_url))
            
        # 启动监控
        monitor = setup_monitoring(
            sinks=sinks,
            alert_channels=alert_channels,
            check_interval=60.0,  # 1分钟检查一次
            start_immediately=True
        )
        
        logger.info("Monitoring system started", 
                   sinks=list(sinks.keys()),
                   alert_channels=len(alert_channels))
        
        return monitor
        
    except Exception as e:
        logger.error(f"Failed to setup monitoring: {e}")
        return None


async def demo_logging():
    """演示各种日志记录功能"""
    
    # 获取模块级别的 logger
    demo_logger = get_logger("sls_example")
    
    logger.info("Starting SLS logging demonstration")
    
    # 基本日志
    demo_logger.info("Basic log message")
    
    # 带上下文的日志
    demo_logger.bind(user_id="demo_user", action="login").info("User action logged")
    
    # 使用上下文管理器
    with demo_logger.contextualize(request_id="req_123", trace_id="trace_456"):
        demo_logger.info("Processing request")
        demo_logger.warning("This is a warning message")
        
        # 模拟错误
        try:
            raise ValueError("This is a demo error")
        except Exception:
            demo_logger.exception("Error occurred during processing")
            
    # 性能日志
    import time
    start_time = time.time()
    await asyncio.sleep(0.1)  # 模拟一些工作
    duration = time.time() - start_time
    
    demo_logger.info("Operation completed", 
                    operation="demo_task",
                    duration_ms=round(duration * 1000, 2),
                    success=True)
    
    logger.info("SLS logging demonstration completed")


async def main():
    """主函数"""
    
    logger.info("SLS Integration Example Starting...")
    
    # 设置 SLS 日志
    sls_sink = setup_sls_logging()
    
    # 设置监控
    monitor = setup_monitoring_example(sls_sink)
    
    # 设置优雅停机
    if sls_sink:
        create_production_setup([sls_sink])
        
    # 演示日志功能
    await demo_logging()
    
    # 如果有监控，显示一些统计信息
    if monitor:
        await asyncio.sleep(2)  # 等待一些指标收集
        dashboard_data = monitor.get_dashboard_data()
        logger.info("Monitoring dashboard data", dashboard=dashboard_data)
        
    logger.info("Example completed. Press Ctrl+C to exit gracefully.")
    
    # 保持运行以演示监控功能
    try:
        while True:
            await asyncio.sleep(10)
            logger.info("Heartbeat message", timestamp=time.time())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")


if __name__ == "__main__":
    asyncio.run(main())