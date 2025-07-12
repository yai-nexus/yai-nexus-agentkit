/**
 * Alibaba Cloud SLS transport implementation for pino.
 */

import { BaseTransport } from '../base';
import { LogMessage } from '../types';
import { SlsConfig } from './config';
import { SlsTransportOptions, SlsLogGroup, SlsLog, SlsLogContent } from './types';
import { SlsClient } from './client';

export class SlsTransport extends BaseTransport {
  private slsConfig: SlsConfig;
  private slsClient: SlsClient;

  constructor(options: SlsTransportOptions) {
    super(options);
    this.slsConfig = new SlsConfig(options);
    this.slsClient = new SlsClient(this.slsConfig);
  }

  /**
   * Initialize the SLS transport
   */
  protected async initialize(): Promise<void> {
    await this.slsClient.initialize();
  }

  /**
   * Cleanup resources
   */
  protected async cleanup(): Promise<void> {
    await this.slsClient.cleanup();
  }

  /**
   * Send a batch of log messages to SLS
   */
  protected async sendBatch(messages: LogMessage[]): Promise<number> {
    if (messages.length === 0) return 0;

    return this.retryOperation(async () => {
      const logGroup = this.convertToSlsLogGroup(messages);
      const response = await this.slsClient.putLogs(logGroup);
      
      // Calculate bytes sent (approximate)
      const bytesSent = JSON.stringify(logGroup).length;
      this.recordSuccess(bytesSent);
      
      return bytesSent;
    });
  }

  /**
   * Perform health check
   */
  protected async performHealthCheck(): Promise<boolean> {
    try {
      return await this.slsClient.healthCheck();
    } catch (error) {
      console.warn('SLS health check failed:', error);
      return false;
    }
  }

  /**
   * Convert pino log messages to SLS log group format
   */
  private convertToSlsLogGroup(messages: LogMessage[]): SlsLogGroup {
    const logs: SlsLog[] = messages.map(msg => ({
      time: Math.floor(msg.time / 1000), // SLS expects seconds
      contents: this.convertToSlsContents(msg)
    }));

    return {
      topic: this.slsConfig.topic,
      source: this.slsConfig.source,
      logs
    };
  }

  /**
   * Convert pino log message to SLS contents format
   */
  private convertToSlsContents(msg: LogMessage): SlsLogContent[] {
    const contents: SlsLogContent[] = [];

    // Add standard fields
    contents.push(
      { key: 'level', value: this.getLevelName(msg.level) },
      { key: 'time', value: new Date(msg.time).toISOString() },
      { key: 'pid', value: msg.pid.toString() },
      { key: 'hostname', value: msg.hostname },
      { key: 'msg', value: msg.msg || '' }
    );

    // Add custom fields
    for (const [key, value] of Object.entries(msg)) {
      if (['level', 'time', 'pid', 'hostname', 'msg'].includes(key)) {
        continue; // Skip standard fields
      }

      let stringValue: string;
      if (typeof value === 'string') {
        stringValue = value;
      } else if (value === null || value === undefined) {
        stringValue = '';
      } else {
        try {
          stringValue = JSON.stringify(value);
        } catch {
          stringValue = String(value);
        }
      }

      contents.push({ key, value: stringValue });
    }

    return contents;
  }

  /**
   * Convert pino level number to level name
   */
  private getLevelName(level: number): string {
    const levels: Record<number, string> = {
      10: 'trace',
      20: 'debug',
      30: 'info',
      40: 'warn',
      50: 'error',
      60: 'fatal'
    };
    return levels[level] || 'info';
  }

  /**
   * Get current configuration
   */
  getConfig(): SlsConfig {
    return this.slsConfig;
  }
}

/**
 * Factory function to create SLS transport
 */
export function createSlsTransport(options: SlsTransportOptions): SlsTransport {
  return new SlsTransport(options);
}