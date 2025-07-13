/**
 * Type definitions for pino-support package.
 */

export interface TransportConfig {
  /** Log level threshold */
  level?: string;
  /** Maximum number of worker threads */
  maxWorkers?: number;
  /** Batch size for bulk operations */
  batchSize?: number;
  /** Flush interval in milliseconds */
  flushInterval?: number;
  /** Maximum retry attempts */
  maxRetries?: number;
  /** Retry delay in milliseconds */
  retryDelay?: number;
  /** Enable metrics collection */
  enableMetrics?: boolean;
}

export interface TransportMetrics {
  /** Number of logs successfully sent */
  logsSent: number;
  /** Number of logs that failed to send */
  logsFailed: number;
  /** Total bytes sent */
  bytesSent: number;
  /** Success rate as percentage */
  successRate: number;
  /** Current queue size */
  queueSize: number;
  /** Transport health status */
  healthy: boolean;
  /** Transport running status */
  running: boolean;
  /** Last error if any */
  lastError?: Error;
  /** Connection errors count */
  connectionErrors: number;
  /** Uptime in seconds */
  uptime: number;
}

export interface CloudTransportConfig extends TransportConfig {
  /** Cloud service endpoint */
  endpoint: string;
  /** Access key ID */
  accessKeyId: string;
  /** Access key secret */
  accessKeySecret: string;
  /** Service region */
  region?: string;
}

export interface LogMessage {
  /** Log level */
  level: number;
  /** Timestamp */
  time: number;
  /** Process ID */
  pid: number;
  /** Hostname */
  hostname: string;
  /** Log message */
  msg: string;
  /** Additional fields */
  [key: string]: unknown;
}

export interface BatchProcessor<T> {
  /** Add item to batch */
  add(item: T): void;
  /** Flush current batch */
  flush(): Promise<void>;
  /** Get current batch size */
  size(): number;
  /** Check if batch is ready to flush */
  isReady(): boolean;
}

export interface HealthChecker {
  /** Perform health check */
  check(): Promise<boolean>;
  /** Get health status */
  isHealthy(): boolean;
  /** Get last check time */
  lastCheck(): Date;
}

export interface RetryPolicy {
  /** Maximum retry attempts */
  maxAttempts: number;
  /** Base delay in milliseconds */
  baseDelay: number;
  /** Maximum delay in milliseconds */
  maxDelay: number;
  /** Backoff multiplier */
  backoffMultiplier: number;
  /** Jitter factor (0-1) */
  jitter: number;
}

export interface MonitoringConfig {
  /** Monitoring check interval in seconds */
  checkInterval?: number;
  /** Error rate threshold for alerts (0-1) */
  errorRateThreshold?: number;
  /** Queue size threshold for alerts */
  queueSizeThreshold?: number;
  /** Enable console alerts */
  enableConsoleAlerts?: boolean;
  /** Webhook URL for alerts */
  webhookUrl?: string;
}

export interface AlertRule {
  /** Rule name */
  name: string;
  /** Rule description */
  description: string;
  /** Alert level */
  level: 'info' | 'warning' | 'error' | 'critical';
  /** Condition function */
  condition: (metrics: TransportMetrics) => boolean;
  /** Cooldown period in seconds */
  cooldown: number;
  /** Whether rule is enabled */
  enabled: boolean;
}

export interface AlertChannel {
  /** Send alert notification */
  sendAlert(rule: AlertRule, metrics: TransportMetrics): Promise<boolean>;
}

export interface GracefulShutdownConfig {
  /** Shutdown timeout in milliseconds */
  timeout?: number;
  /** Signals to handle */
  signals?: NodeJS.Signals[];
  /** Enable atexit handler */
  enableAtexit?: boolean;
}

/**
 * Unified logging configuration interface.
 * This serves as the "Single Source of Truth" for logging configuration
 * across both Python (loguru-support) and Node.js (pino-support) stacks.
 */
export interface LoggerConfig {
  /** Service name for log identification */
  serviceName: string;
  /** Log level (debug, info, warn, error) */
  level?: 'debug' | 'info' | 'warn' | 'error';
  /** Console output configuration */
  console?: {
    /** Enable console output */
    enabled?: boolean;
    /** Pretty print for development */
    pretty?: boolean;
  };
  /** File output configuration */
  file?: {
    /** Enable file output */
    enabled?: boolean;
    /** Base directory for log files */
    baseDir?: string;
    /** Directory strategy (hourly, daily) */
    strategy?: 'hourly' | 'daily';
    /** Maximum file size in bytes */
    maxSize?: number;
    /** Maximum number of files to keep */
    maxFiles?: number;
  };
  /** Cloud logging configuration */
  cloud?: {
    /** Enable cloud logging */
    enabled?: boolean;
    /** Cloud provider specific config */
    sls?: {
      endpoint: string;
      accessKeyId: string;
      accessKeySecret: string;
      project: string;
      logstore: string;
      region?: string;
    };
  };
}

/**
 * Environment detection result for isomorphic logger setup
 */
export interface EnvironmentInfo {
  /** Is running in browser environment */
  isBrowser: boolean;
  /** Is running in Node.js environment */
  isNode: boolean;
  /** Is running in Next.js environment */
  isNextJs: boolean;
  /** Environment type for logging purposes */
  environment: 'browser' | 'node' | 'unknown';
}