/**
 * Transport monitoring system.
 */

import { BaseTransport } from '../base';
import { TransportMetrics, MonitoringConfig, AlertRule, AlertChannel } from '../types';
import { ConsoleAlertChannel } from './alerts';

export class TransportMonitor {
  private transports = new Map<string, BaseTransport>();
  private alertRules: AlertRule[] = [];
  private alertChannels: AlertChannel[] = [];
  private config: Required<MonitoringConfig>;
  private monitoringInterval?: NodeJS.Timeout;
  private running = false;
  private metricsHistory: Array<{ timestamp: number; metrics: Record<string, TransportMetrics> }> = [];
  private readonly maxHistorySize = 1440; // 24 hours at 1-minute intervals

  constructor(config: MonitoringConfig = {}) {
    this.config = {
      checkInterval: config.checkInterval || 60,
      errorRateThreshold: config.errorRateThreshold || 0.1,
      queueSizeThreshold: config.queueSizeThreshold || 1000,
      enableConsoleAlerts: config.enableConsoleAlerts !== false,
      webhookUrl: config.webhookUrl || ''
    };

    this.setupDefaultAlerts();
    this.setupDefaultChannels();
  }

  /**
   * Add a transport to monitor
   */
  addTransport(name: string, transport: BaseTransport): void {
    this.transports.set(name, transport);
  }

  /**
   * Remove a transport from monitoring
   */
  removeTransport(name: string): void {
    this.transports.delete(name);
  }

  /**
   * Add an alert rule
   */
  addAlertRule(rule: AlertRule): void {
    this.alertRules.push(rule);
  }

  /**
   * Add an alert channel
   */
  addAlertChannel(channel: AlertChannel): void {
    this.alertChannels.push(channel);
  }

  /**
   * Start monitoring
   */
  async startMonitoring(): Promise<void> {
    if (this.running) return;

    this.running = true;
    this.monitoringInterval = setInterval(async () => {
      await this.checkMetrics();
    }, this.config.checkInterval * 1000);

    console.log(`Transport monitoring started (interval: ${this.config.checkInterval}s)`);
  }

  /**
   * Stop monitoring
   */
  async stopMonitoring(): Promise<void> {
    if (!this.running) return;

    this.running = false;
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }

    console.log('Transport monitoring stopped');
  }

  /**
   * Get current metrics for all transports
   */
  getCurrentMetrics(): Record<string, TransportMetrics> {
    const metrics: Record<string, TransportMetrics> = {};
    
    for (const [name, transport] of this.transports) {
      try {
        metrics[name] = transport.getMetrics();
      } catch (error) {
        metrics[name] = {
          logsSent: 0,
          logsFailed: 0,
          bytesSent: 0,
          successRate: 0,
          queueSize: 0,
          healthy: false,
          running: false,
          connectionErrors: 0,
          uptime: 0,
          lastError: error as Error
        };
      }
    }

    return metrics;
  }

  /**
   * Get monitoring dashboard data
   */
  getDashboardData(): {
    summary: {
      totalTransports: number;
      healthyTransports: number;
      totalLogsSent: number;
      totalLogsFailed: number;
      overallSuccessRate: number;
      activeAlerts: number;
    };
    transports: Record<string, TransportMetrics>;
    alertSummary: Array<{
      name: string;
      level: string;
      description: string;
      enabled: boolean;
    }>;
    historySize: number;
  } {
    const currentMetrics = this.getCurrentMetrics();
    
    const summary = {
      totalTransports: this.transports.size,
      healthyTransports: Object.values(currentMetrics).filter(m => m.healthy).length,
      totalLogsSent: Object.values(currentMetrics).reduce((sum, m) => sum + m.logsSent, 0),
      totalLogsFailed: Object.values(currentMetrics).reduce((sum, m) => sum + m.logsFailed, 0),
      overallSuccessRate: 0,
      activeAlerts: this.alertRules.filter(r => r.enabled).length
    };

    const totalLogs = summary.totalLogsSent + summary.totalLogsFailed;
    if (totalLogs > 0) {
      summary.overallSuccessRate = (summary.totalLogsSent / totalLogs) * 100;
    }

    return {
      summary,
      transports: currentMetrics,
      alertSummary: this.alertRules.map(rule => ({
        name: rule.name,
        level: rule.level,
        description: rule.description,
        enabled: rule.enabled
      })),
      historySize: this.metricsHistory.length
    };
  }

  /**
   * Export metrics in various formats
   */
  exportMetrics(format: 'json' | 'prometheus' = 'json'): string {
    const data = this.getDashboardData();

    if (format === 'prometheus') {
      const lines: string[] = [];
      
      for (const [name, metrics] of Object.entries(data.transports)) {
        lines.push(
          `pino_transport_logs_sent{transport="${name}"} ${metrics.logsSent}`,
          `pino_transport_logs_failed{transport="${name}"} ${metrics.logsFailed}`,
          `pino_transport_success_rate{transport="${name}"} ${metrics.successRate}`,
          `pino_transport_healthy{transport="${name}"} ${metrics.healthy ? 1 : 0}`,
          `pino_transport_queue_size{transport="${name}"} ${metrics.queueSize}`,
          `pino_transport_uptime{transport="${name}"} ${metrics.uptime}`
        );
      }
      
      return lines.join('\\n');
    }

    return JSON.stringify(data, null, 2);
  }

  /**
   * Check metrics and trigger alerts
   */
  private async checkMetrics(): Promise<void> {
    const currentMetrics = this.getCurrentMetrics();
    
    // Store metrics history
    this.metricsHistory.push({
      timestamp: Date.now(),
      metrics: currentMetrics
    });

    // Keep history size manageable
    if (this.metricsHistory.length > this.maxHistorySize) {
      this.metricsHistory.shift();
    }

    // Check alert rules
    for (const rule of this.alertRules) {
      if (!rule.enabled) continue;

      const shouldAlert = Object.values(currentMetrics).some(metrics => 
        rule.condition(metrics)
      );

      if (shouldAlert) {
        // Find which transport triggered the alert
        const triggeringTransports = Object.entries(currentMetrics)
          .filter(([, metrics]) => rule.condition(metrics))
          .map(([name]) => name);

        for (const channel of this.alertChannels) {
          try {
            await channel.sendAlert(rule, currentMetrics[triggeringTransports[0]]);
          } catch (error) {
            console.error('Failed to send alert:', error);
          }
        }
      }
    }
  }

  /**
   * Setup default alert rules
   */
  private setupDefaultAlerts(): void {
    this.alertRules = [
      {
        name: 'high_error_rate',
        description: 'Transport error rate above threshold',
        level: 'warning',
        condition: (metrics) => metrics.successRate < (100 - this.config.errorRateThreshold * 100),
        cooldown: 300, // 5 minutes
        enabled: true
      },
      {
        name: 'transport_unhealthy',
        description: 'Transport is unhealthy',
        level: 'error',
        condition: (metrics) => !metrics.healthy,
        cooldown: 300,
        enabled: true
      },
      {
        name: 'large_queue_size',
        description: 'Transport queue size is large',
        level: 'warning',
        condition: (metrics) => metrics.queueSize > this.config.queueSizeThreshold,
        cooldown: 300,
        enabled: true
      },
      {
        name: 'connection_errors',
        description: 'Multiple connection errors detected',
        level: 'error',
        condition: (metrics) => metrics.connectionErrors > 5,
        cooldown: 600, // 10 minutes
        enabled: true
      }
    ];
  }

  /**
   * Setup default alert channels
   */
  private setupDefaultChannels(): void {
    if (this.config.enableConsoleAlerts) {
      this.alertChannels.push(new ConsoleAlertChannel());
    }

    if (this.config.webhookUrl) {
      const { WebhookAlertChannel } = require('./alerts');
      this.alertChannels.push(new WebhookAlertChannel(this.config.webhookUrl));
    }
  }
}

/**
 * Setup monitoring for multiple transports
 */
export function setupMonitoring(options: {
  transports: Record<string, BaseTransport>;
  config?: MonitoringConfig;
  startImmediately?: boolean;
}): TransportMonitor {
  const monitor = new TransportMonitor(options.config);

  // Add transports
  for (const [name, transport] of Object.entries(options.transports)) {
    monitor.addTransport(name, transport);
  }

  // Start monitoring
  if (options.startImmediately !== false) {
    monitor.startMonitoring().catch(error => {
      console.error('Failed to start monitoring:', error);
    });
  }

  return monitor;
}