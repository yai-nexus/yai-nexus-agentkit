/**
 * Alert channel implementations.
 */

import { AlertChannel, AlertRule, TransportMetrics } from '../types';

export class ConsoleAlertChannel implements AlertChannel {
  async sendAlert(rule: AlertRule, metrics: TransportMetrics): Promise<boolean> {
    const timestamp = new Date().toISOString();
    
    console.log(`\\n🚨 ALERT [${rule.level.toUpperCase()}] ${timestamp}`);
    console.log(`Rule: ${rule.name}`);
    console.log(`Description: ${rule.description}`);
    console.log(`Metrics:`, {
      logsSent: metrics.logsSent,
      logsFailed: metrics.logsFailed,
      successRate: `${metrics.successRate.toFixed(2)}%`,
      queueSize: metrics.queueSize,
      healthy: metrics.healthy,
      running: metrics.running,
      uptime: `${metrics.uptime}s`
    });
    console.log('='.repeat(50));
    
    return true;
  }
}

export class WebhookAlertChannel implements AlertChannel {
  constructor(
    private webhookUrl: string,
    private headers: Record<string, string> = { 'Content-Type': 'application/json' }
  ) {}

  async sendAlert(rule: AlertRule, metrics: TransportMetrics): Promise<boolean> {
    try {
      const payload = {
        timestamp: new Date().toISOString(),
        rule: {
          name: rule.name,
          level: rule.level,
          description: rule.description
        },
        metrics: {
          logsSent: metrics.logsSent,
          logsFailed: metrics.logsFailed,
          successRate: metrics.successRate,
          queueSize: metrics.queueSize,
          healthy: metrics.healthy,
          running: metrics.running,
          uptime: metrics.uptime,
          connectionErrors: metrics.connectionErrors
        }
      };

      // Try native fetch first (Node.js 18+)
      if (typeof fetch !== 'undefined') {
        const response = await fetch(this.webhookUrl, {
          method: 'POST',
          headers: this.headers,
          body: JSON.stringify(payload)
        });
        return response.ok;
      }

      // Fallback to axios
      try {
        const axios = await import('axios');
        const response = await axios.default.post(this.webhookUrl, payload, {
          headers: this.headers,
          timeout: 10000
        });
        return response.status >= 200 && response.status < 300;
      } catch (importError) {
        console.error('No HTTP client available for webhook alerts');
        return false;
      }
    } catch (error) {
      console.error('Failed to send webhook alert:', error);
      return false;
    }
  }
}