"""
YAI Loguru Support

A collection of Loguru sinks for integrating with third-party cloud logging services.

This package provides production-ready sinks for popular cloud logging services,
built on top of their official SDKs for maximum reliability and performance.

Example usage:
    from yai_loguru_support.sls import AliyunSlsSink
    from loguru import logger
    
    # Create and configure sink
    sls_sink = AliyunSlsSink(
        endpoint="cn-hangzhou.log.aliyuncs.com",
        access_key_id="your_key_id",
        access_key="your_key",
        project="your_project",
        logstore="your_logstore"
    )
    
    # Add to loguru
    logger.add(sls_sink, serialize=True, level="INFO")
    
    # Use normally
    logger.info("Hello from cloud logging!")
"""

from .version import __version__
from .base import BaseSink, SinkError, SinkConfig

# Import specific sinks when their dependencies are available
try:
    from .sls import AliyunSlsSink
    __all__ = ["__version__", "BaseSink", "SinkError", "SinkConfig", "AliyunSlsSink"]
except ImportError:
    __all__ = ["__version__", "BaseSink", "SinkError", "SinkConfig"]

# Version info
__author__ = "YAI-Nexus Team"
__email__ = "contact@yai-nexus.com"