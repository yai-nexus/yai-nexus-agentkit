"""
Monitoring and alerting utilities for loguru sinks.

This module provides comprehensive monitoring capabilities for sink health,
performance metrics, and automated alerting based on configurable thresholds.
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from .base import BaseSink


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    """Configuration for monitoring alerts."""
    
    name: str
    description: str
    level: AlertLevel
    condition: Callable[[Dict[str, Any]], bool]
    cooldown: float = 300.0  # 5 minutes default cooldown
    enabled: bool = True
    
    # Internal state
    last_triggered: float = field(default=0.0, init=False)
    trigger_count: int = field(default=0, init=False)


class AlertChannel(ABC):
    """Abstract base class for alert notification channels."""
    
    @abstractmethod
    async def send_alert(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """Send an alert notification."""
        pass


class ConsoleAlertChannel(AlertChannel):
    """Simple console-based alert channel for development."""
    
    async def send_alert(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """Print alert to console."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n🚨 ALERT [{rule.level.value.upper()}] {timestamp}")
        print(f"Rule: {rule.name}")
        print(f"Description: {rule.description}")
        print(f"Metrics: {json.dumps(metrics, indent=2)}")
        print("=" * 50)
        return True


class LogAlertChannel(AlertChannel):
    """Log-based alert channel that writes alerts to a separate logger."""
    
    def __init__(self, logger_name: str = "yai_loguru_support.alerts"):
        import logging
        self.logger = logging.getLogger(logger_name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def send_alert(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """Log alert using standard logging."""
        alert_data = {
            "rule_name": rule.name,
            "level": rule.level.value,
            "description": rule.description,
            "metrics": metrics,
            "trigger_count": rule.trigger_count
        }
        
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }[rule.level]
        
        self.logger.log(log_level, f"Alert: {rule.name}", extra=alert_data)
        return True


class WebhookAlertChannel(AlertChannel):
    """Webhook-based alert channel for external integrations."""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {"Content-Type": "application/json"}
    
    async def send_alert(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """Send alert via HTTP webhook."""
        try:
            import aiohttp
            
            payload = {
                "timestamp": time.time(),
                "rule": {
                    "name": rule.name,
                    "level": rule.level.value,
                    "description": rule.description,
                    "trigger_count": rule.trigger_count
                },
                "metrics": metrics
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status < 400
                    
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")
            return False


class SinkMonitor:
    """
    Comprehensive monitoring system for loguru sinks.
    
    Features:
    - Real-time performance metrics collection
    - Configurable alert rules and thresholds
    - Multiple notification channels
    - Health dashboard data
    - Automated anomaly detection
    """
    
    def __init__(self, check_interval: float = 60.0):
        self.check_interval = check_interval
        self.sinks: Dict[str, BaseSink] = {}
        self.alert_rules: List[AlertRule] = []
        self.alert_channels: List[AlertChannel] = []
        self.historical_metrics: List[Dict[str, Any]] = []
        self.max_history = 1440  # 24 hours at 1-minute intervals
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Setup default alert rules
        self._setup_default_alerts()
        
    def add_sink(self, name: str, sink: BaseSink) -> None:
        """Add a sink to monitor."""
        self.sinks[name] = sink
        
    def remove_sink(self, name: str) -> None:
        """Remove a sink from monitoring."""
        self.sinks.pop(name, None)
        
    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add a custom alert rule."""
        self.alert_rules.append(rule)
        
    def add_alert_channel(self, channel: AlertChannel) -> None:
        """Add an alert notification channel."""
        self.alert_channels.append(channel)
        
    def _setup_default_alerts(self) -> None:
        """Setup commonly useful alert rules."""
        
        # High error rate alert
        self.alert_rules.append(AlertRule(
            name="high_error_rate",
            description="Sink error rate above 10%",
            level=AlertLevel.WARNING,
            condition=lambda m: any(
                sink_m.get("success_rate", 100) < 90
                for sink_m in m.get("sinks", {}).values()
            ),
            cooldown=600.0  # 10 minutes
        ))
        
        # Very high error rate alert
        self.alert_rules.append(AlertRule(
            name="critical_error_rate",
            description="Sink error rate above 50%",
            level=AlertLevel.CRITICAL,
            condition=lambda m: any(
                sink_m.get("success_rate", 100) < 50
                for sink_m in m.get("sinks", {}).values()
            ),
            cooldown=300.0  # 5 minutes
        ))
        
        # Sink down alert
        self.alert_rules.append(AlertRule(
            name="sink_unhealthy",
            description="One or more sinks are unhealthy",
            level=AlertLevel.ERROR,
            condition=lambda m: any(
                not sink_m.get("healthy", True)
                for sink_m in m.get("sinks", {}).values()
            ),
            cooldown=300.0
        ))
        
        # Large queue size alert
        self.alert_rules.append(AlertRule(
            name="large_queue_size",
            description="Sink queue size is very large",
            level=AlertLevel.WARNING,
            condition=lambda m: any(
                sink_m.get("queue_size", 0) > 1000
                for sink_m in m.get("sinks", {}).values()
            ),
            cooldown=300.0
        ))
        
        # Connection errors alert
        self.alert_rules.append(AlertRule(
            name="connection_errors",
            description="Multiple connection errors detected",
            level=AlertLevel.ERROR,
            condition=lambda m: any(
                sink_m.get("connection_errors", 0) > 5
                for sink_m in m.get("sinks", {}).values()
            ),
            cooldown=600.0
        ))
        
    async def start_monitoring(self) -> None:
        """Start the monitoring loop."""
        if self._running:
            return
            
        self._running = True
        
        # Add default console channel if none configured
        if not self.alert_channels:
            self.alert_channels.append(ConsoleAlertChannel())
            
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        print(f"Sink monitoring started (interval: {self.check_interval}s)")
        
    async def stop_monitoring(self) -> None:
        """Stop the monitoring loop."""
        self._running = False
        
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
                
        print("Sink monitoring stopped")
        
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check_metrics()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
                
    async def _check_metrics(self) -> None:
        """Collect metrics and check alert conditions."""
        # Collect metrics from all sinks
        current_metrics = {
            "timestamp": time.time(),
            "sinks": {}
        }
        
        for name, sink in self.sinks.items():
            try:
                sink_metrics = sink.get_metrics()
                current_metrics["sinks"][name] = sink_metrics
            except Exception as e:
                current_metrics["sinks"][name] = {
                    "error": str(e),
                    "healthy": False
                }
                
        # Store historical data
        self.historical_metrics.append(current_metrics)
        if len(self.historical_metrics) > self.max_history:
            self.historical_metrics.pop(0)
            
        # Check alert rules
        await self._check_alerts(current_metrics)
        
    async def _check_alerts(self, metrics: Dict[str, Any]) -> None:
        """Check all alert rules against current metrics."""
        current_time = time.time()
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
                
            # Check cooldown period
            if current_time - rule.last_triggered < rule.cooldown:
                continue
                
            try:
                # Evaluate alert condition
                if rule.condition(metrics):
                    rule.last_triggered = current_time
                    rule.trigger_count += 1
                    
                    # Send alerts through all channels
                    for channel in self.alert_channels:
                        try:
                            await channel.send_alert(rule, metrics)
                        except Exception as e:
                            print(f"Failed to send alert via {channel}: {e}")
                            
            except Exception as e:
                print(f"Error evaluating alert rule '{rule.name}': {e}")
                
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data."""
        if not self.historical_metrics:
            return {"error": "No metrics available"}
            
        latest = self.historical_metrics[-1]
        
        # Calculate aggregated statistics
        total_logs_sent = sum(
            sink_m.get("logs_sent", 0)
            for sink_m in latest.get("sinks", {}).values()
            if isinstance(sink_m, dict)
        )
        
        total_logs_failed = sum(
            sink_m.get("logs_failed", 0)
            for sink_m in latest.get("sinks", {}).values()
            if isinstance(sink_m, dict)
        )
        
        overall_success_rate = 100.0
        if total_logs_sent + total_logs_failed > 0:
            overall_success_rate = (total_logs_sent / (total_logs_sent + total_logs_failed)) * 100
            
        # Alert summary
        active_alerts = [
            rule for rule in self.alert_rules
            if rule.enabled and time.time() - rule.last_triggered < rule.cooldown
        ]
        
        return {
            "timestamp": latest["timestamp"],
            "summary": {
                "total_sinks": len(self.sinks),
                "healthy_sinks": sum(
                    1 for sink_m in latest.get("sinks", {}).values()
                    if isinstance(sink_m, dict) and sink_m.get("healthy", False)
                ),
                "total_logs_sent": total_logs_sent,
                "total_logs_failed": total_logs_failed,
                "overall_success_rate": overall_success_rate,
                "active_alerts": len(active_alerts)
            },
            "sinks": latest.get("sinks", {}),
            "alerts": {
                "active": [
                    {
                        "name": rule.name,
                        "level": rule.level.value,
                        "description": rule.description,
                        "trigger_count": rule.trigger_count,
                        "last_triggered": rule.last_triggered
                    }
                    for rule in active_alerts
                ],
                "rules": [
                    {
                        "name": rule.name,
                        "level": rule.level.value,
                        "description": rule.description,
                        "enabled": rule.enabled,
                        "trigger_count": rule.trigger_count,
                        "cooldown": rule.cooldown
                    }
                    for rule in self.alert_rules
                ]
            },
            "history_size": len(self.historical_metrics)
        }
        
    def export_metrics(self, format: str = "json") -> Union[str, Dict[str, Any]]:
        """Export metrics in various formats."""
        data = self.get_dashboard_data()
        
        if format.lower() == "json":
            return json.dumps(data, indent=2)
        elif format.lower() == "prometheus":
            # Basic Prometheus format export
            lines = []
            for sink_name, sink_metrics in data.get("sinks", {}).items():
                if isinstance(sink_metrics, dict):
                    lines.extend([
                        f'sink_logs_sent{{sink="{sink_name}"}} {sink_metrics.get("logs_sent", 0)}',
                        f'sink_logs_failed{{sink="{sink_name}"}} {sink_metrics.get("logs_failed", 0)}',
                        f'sink_success_rate{{sink="{sink_name}"}} {sink_metrics.get("success_rate", 0)}',
                        f'sink_healthy{{sink="{sink_name}"}} {1 if sink_metrics.get("healthy") else 0}',
                        f'sink_queue_size{{sink="{sink_name}"}} {sink_metrics.get("queue_size", 0)}'
                    ])
            return "\n".join(lines)
        else:
            return data


# Global monitor instance
_global_monitor = SinkMonitor()


def get_global_monitor() -> SinkMonitor:
    """Get the global sink monitor instance."""
    return _global_monitor


def setup_monitoring(
    sinks: Dict[str, BaseSink],
    alert_channels: Optional[List[AlertChannel]] = None,
    check_interval: float = 60.0,
    start_immediately: bool = True
) -> SinkMonitor:
    """
    Setup comprehensive monitoring for multiple sinks.
    
    Args:
        sinks: Dictionary of sink name -> sink instance
        alert_channels: List of alert notification channels
        check_interval: Monitoring check interval in seconds
        start_immediately: Whether to start monitoring immediately
        
    Returns:
        SinkMonitor instance
    """
    monitor = SinkMonitor(check_interval=check_interval)
    
    # Add sinks
    for name, sink in sinks.items():
        monitor.add_sink(name, sink)
        
    # Add alert channels
    if alert_channels:
        for channel in alert_channels:
            monitor.add_alert_channel(channel)
            
    # Start monitoring
    if start_immediately:
        asyncio.create_task(monitor.start_monitoring())
        
    return monitor