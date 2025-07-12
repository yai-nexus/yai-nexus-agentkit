/**
 * Configuration management for SLS transport.
 */

import { SlsTransportOptions } from './types';

export class SlsConfig {
  readonly endpoint: string;
  readonly accessKeyId: string;
  readonly accessKeySecret: string;
  readonly project: string;
  readonly logstore: string;
  readonly topic: string;
  readonly source: string;
  readonly securityToken?: string;
  readonly compression: 'gzip' | 'lz4' | 'none';
  readonly headers: Record<string, string>;
  
  // Transport configuration
  readonly level: string;
  readonly maxWorkers: number;
  readonly batchSize: number;
  readonly flushInterval: number;
  readonly maxRetries: number;
  readonly retryDelay: number;
  readonly enableMetrics: boolean;

  constructor(options: SlsTransportOptions) {
    // Validate required fields
    if (!options.endpoint) {
      throw new Error('SLS endpoint is required');
    }
    if (!options.accessKeyId) {
      throw new Error('SLS accessKeyId is required');
    }
    if (!options.accessKeySecret) {
      throw new Error('SLS accessKeySecret is required');
    }
    if (!options.project) {
      throw new Error('SLS project is required');
    }
    if (!options.logstore) {
      throw new Error('SLS logstore is required');
    }

    // SLS-specific configuration
    this.endpoint = options.endpoint;
    this.accessKeyId = options.accessKeyId;
    this.accessKeySecret = options.accessKeySecret;
    this.project = options.project;
    this.logstore = options.logstore;
    this.topic = options.topic || 'pino-logs';
    this.source = options.source || 'nodejs-app';
    this.securityToken = options.securityToken;
    this.compression = options.compression || 'gzip';
    this.headers = options.headers || {};

    // Transport configuration with defaults
    this.level = options.level || 'info';
    this.maxWorkers = options.maxWorkers || 4;
    this.batchSize = options.batchSize || 100;
    this.flushInterval = options.flushInterval || 5000;
    this.maxRetries = options.maxRetries || 3;
    this.retryDelay = options.retryDelay || 1000;
    this.enableMetrics = options.enableMetrics !== false;
  }

  /**
   * Create SlsConfig from environment variables
   */
  static fromEnv(): SlsConfig {
    return new SlsConfig({
      endpoint: process.env.SLS_ENDPOINT!,
      accessKeyId: process.env.SLS_AK_ID!,
      accessKeySecret: process.env.SLS_AK_KEY!,
      project: process.env.SLS_PROJECT!,
      logstore: process.env.SLS_LOGSTORE!,
      topic: process.env.SLS_TOPIC,
      source: process.env.SLS_SOURCE,
      securityToken: process.env.SLS_SECURITY_TOKEN,
      
      // Optional performance tuning
      batchSize: process.env.SLS_BATCH_SIZE ? parseInt(process.env.SLS_BATCH_SIZE) : undefined,
      flushInterval: process.env.SLS_FLUSH_INTERVAL ? parseInt(process.env.SLS_FLUSH_INTERVAL) : undefined,
      maxRetries: process.env.SLS_MAX_RETRIES ? parseInt(process.env.SLS_MAX_RETRIES) : undefined
    });
  }

  /**
   * Validate environment variables are set
   */
  static validateEnv(): string[] {
    const required = ['SLS_ENDPOINT', 'SLS_AK_ID', 'SLS_AK_KEY', 'SLS_PROJECT', 'SLS_LOGSTORE'];
    const missing: string[] = [];

    for (const key of required) {
      if (!process.env[key]) {
        missing.push(key);
      }
    }

    return missing;
  }

  /**
   * Get base URL for SLS API
   */
  getBaseUrl(): string {
    return `https://${this.project}.${this.endpoint}`;
  }

  /**
   * Get logstore URL
   */
  getLogstoreUrl(): string {
    return `${this.getBaseUrl()}/logstores/${this.logstore}/shards/lb`;
  }

  /**
   * Convert to plain object for serialization
   */
  toJSON(): Record<string, unknown> {
    return {
      endpoint: this.endpoint,
      project: this.project,
      logstore: this.logstore,
      topic: this.topic,
      source: this.source,
      compression: this.compression,
      level: this.level,
      batchSize: this.batchSize,
      flushInterval: this.flushInterval,
      maxRetries: this.maxRetries,
      // Note: credentials are intentionally excluded
    };
  }
}