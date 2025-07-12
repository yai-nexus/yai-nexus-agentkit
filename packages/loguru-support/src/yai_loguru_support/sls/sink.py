"""
Aliyun SLS Sink implementation.

Provides high-performance, production-ready integration with Aliyun SLS
using the official SDK with async batching and error handling.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

try:
    from aliyun.log import LogClient, PutLogsRequest, LogItem
    from aliyun.log.exceptions import LogException
except ImportError:
    raise ImportError(
        "aliyun-log-python-sdk is required for SLS support. "
        "Install with: pip install aliyun-log-python-sdk>=0.7.8"
    )

from ..base import BaseSink, SinkConfig, SinkError, SinkConnectionError


@dataclass
class SlsConfig(SinkConfig):
    """Configuration for Aliyun SLS sink."""
    
    # SLS 连接配置
    endpoint: str = ""
    access_key_id: str = ""
    access_key: str = ""
    project: str = ""
    logstore: str = ""
    
    # SLS 特定配置
    topic: str = ""
    source: str = ""
    compress: bool = True
    
    # 性能优化配置
    batch_size: int = 500  # SLS 支持最大 4096 条/批
    max_log_size: int = 1024 * 1024  # 1MB per log
    
    # 高级配置
    auto_retry: bool = True
    shard_hash_key: str = ""
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not all([self.endpoint, self.access_key_id, self.access_key, 
                   self.project, self.logstore]):
            raise ValueError(
                "SLS configuration incomplete. Required: endpoint, access_key_id, "
                "access_key, project, logstore"
            )


class AliyunSlsSink(BaseSink):
    """
    High-performance Aliyun SLS sink for loguru.
    
    Features:
    - Asynchronous batch processing
    - Automatic retries with exponential backoff
    - Connection health monitoring
    - Performance metrics collection
    - Graceful shutdown with log flushing
    
    Example:
        ```python
        from yai_loguru_support.sls import AliyunSlsSink, SlsConfig
        from loguru import logger
        
        config = SlsConfig(
            endpoint="cn-hangzhou.log.aliyuncs.com",
            access_key_id="your_key_id",
            access_key="your_key",
            project="your_project",
            logstore="your_logstore"
        )
        
        sls_sink = AliyunSlsSink(config)
        logger.add(sls_sink, serialize=True, level="INFO")
        
        # Use logger normally
        logger.info("Hello SLS!", user_id="123")
        
        # Graceful shutdown
        import atexit
        atexit.register(lambda: asyncio.run(sls_sink.stop()))
        ```
    """
    
    def __init__(self, config: SlsConfig):
        if not isinstance(config, SlsConfig):
            raise TypeError("config must be an instance of SlsConfig")
            
        super().__init__(config)
        self.sls_config = config
        self._client: Optional[LogClient] = None
        
        # Start the sink automatically
        asyncio.create_task(self.start())
        
    @classmethod
    def from_env(cls, **kwargs) -> "AliyunSlsSink":
        """
        Create SLS sink from environment variables.
        
        Expected environment variables:
        - SLS_ENDPOINT
        - SLS_AK_ID
        - SLS_AK_KEY
        - SLS_PROJECT
        - SLS_LOGSTORE
        - SLS_TOPIC (optional)
        - SLS_SOURCE (optional)
        """
        import os
        
        config = SlsConfig(
            endpoint=os.environ.get("SLS_ENDPOINT", ""),
            access_key_id=os.environ.get("SLS_AK_ID", ""),
            access_key=os.environ.get("SLS_AK_KEY", ""),
            project=os.environ.get("SLS_PROJECT", ""),
            logstore=os.environ.get("SLS_LOGSTORE", ""),
            topic=os.environ.get("SLS_TOPIC", ""),
            source=os.environ.get("SLS_SOURCE", ""),
            **kwargs
        )
        
        return cls(config)
        
    async def _initialize_connection(self) -> None:
        """Initialize SLS client connection."""
        try:
            self._client = LogClient(
                self.sls_config.endpoint,
                self.sls_config.access_key_id,
                self.sls_config.access_key
            )
            
            # Test connection by listing logstores
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._client.list_logstores,
                self.sls_config.project
            )
            
            self._internal_logger.info(
                f"SLS connection established to {self.sls_config.endpoint}"
            )
            
        except Exception as e:
            raise SinkConnectionError(f"Failed to connect to SLS: {e}") from e
            
    async def _cleanup_connection(self) -> None:
        """Cleanup SLS connection."""
        self._client = None
        self._internal_logger.info("SLS connection cleaned up")
        
    async def _send_batch(self, messages: List[str]) -> int:
        """Send a batch of log messages to SLS."""
        if not self._client:
            raise SinkError("SLS client not initialized")
            
        try:
            # Convert messages to SLS LogItems
            log_items = []
            total_size = 0
            
            for message in messages:
                try:
                    # Parse the serialized log record
                    log_data = json.loads(message.strip())
                    
                    # Extract timestamp
                    log_time = int(log_data.get("time", time.time()))
                    
                    # Convert loguru record to SLS format
                    log_item = LogItem(
                        timestamp=log_time,
                        contents=[
                            ("level", str(log_data.get("level", "INFO"))),
                            ("message", str(log_data.get("message", ""))),
                            ("logger", str(log_data.get("name", ""))),
                            ("module", str(log_data.get("module", ""))),
                            ("function", str(log_data.get("function", ""))),
                            ("line", str(log_data.get("line", ""))),
                            ("thread", str(log_data.get("thread", {}).get("name", ""))),
                            ("process", str(log_data.get("process", {}).get("name", ""))),
                        ]
                    )
                    
                    # Add extra fields from the log record
                    extra = log_data.get("extra", {})
                    for key, value in extra.items():
                        if isinstance(value, (str, int, float, bool)):
                            log_item.contents.append((key, str(value)))
                    
                    # Add exception info if present
                    if "exception" in log_data and log_data["exception"]:
                        exc_info = log_data["exception"]
                        log_item.contents.extend([
                            ("exception_type", str(exc_info.get("type", ""))),
                            ("exception_value", str(exc_info.get("value", ""))),
                            ("exception_traceback", str(exc_info.get("traceback", ""))),
                        ])
                    
                    log_items.append(log_item)
                    total_size += len(message.encode('utf-8'))
                    
                except (json.JSONDecodeError, KeyError) as e:
                    self._internal_logger.warning(f"Failed to parse log message: {e}")
                    continue
                    
            if not log_items:
                return 0
                
            # Create put logs request
            request = PutLogsRequest(
                project=self.sls_config.project,
                logstore=self.sls_config.logstore,
                topic=self.sls_config.topic,
                source=self.sls_config.source,
                logitems=log_items,
                compress=self.sls_config.compress,
                hashKey=self.sls_config.shard_hash_key or None
            )
            
            # Send logs asynchronously
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._client.put_logs,
                request
            )
            
            return total_size
            
        except LogException as e:
            # SLS specific errors
            error_msg = f"SLS error (code: {e.get_error_code()}): {e.get_error_message()}"
            raise SinkError(error_msg) from e
            
        except Exception as e:
            raise SinkError(f"Failed to send logs to SLS: {e}") from e
            
    async def _health_check(self) -> bool:
        """Perform health check by testing SLS connectivity."""
        if not self._client:
            return False
            
        try:
            # Simple health check: list logstores
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._client.list_logstores,
                self.sls_config.project
            )
            return True
            
        except Exception as e:
            self._internal_logger.warning(f"SLS health check failed: {e}")
            return False
            
    def stop(self) -> None:
        """
        Synchronous stop method for use in atexit handlers.
        
        This is a convenience method that runs the async stop() in a new event loop.
        Use the async version when possible.
        """
        try:
            # Try to use existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in a running loop, create a task
                asyncio.create_task(super().stop())
            else:
                # If no running loop, run directly
                loop.run_until_complete(super().stop())
        except RuntimeError:
            # No event loop, create a new one
            asyncio.run(super().stop())
            
    def get_sls_metrics(self) -> Dict[str, Any]:
        """Get SLS-specific metrics."""
        metrics = self.get_metrics()
        metrics.update({
            "sls_endpoint": self.sls_config.endpoint,
            "sls_project": self.sls_config.project,
            "sls_logstore": self.sls_config.logstore,
            "batch_size": self.sls_config.batch_size,
            "compress": self.sls_config.compress,
        })
        return metrics