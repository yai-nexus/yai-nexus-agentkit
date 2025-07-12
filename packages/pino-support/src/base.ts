/**
 * Base transport implementation for pino cloud logging.
 * 
 * Provides common functionality for batch processing, retry logic,
 * metrics collection, and health monitoring.
 */

import { Transform } from 'stream';
import {
  TransportConfig,
  TransportMetrics,
  LogMessage,
  BatchProcessor,
  HealthChecker,
  RetryPolicy
} from './types';

export abstract class BaseTransport extends Transform {
  protected config: Required<TransportConfig>;
  protected metrics: TransportMetrics;
  protected batchProcessor: BatchProcessor<LogMessage>;
  protected healthChecker: HealthChecker;
  protected retryPolicy: RetryPolicy;
  protected running = false;
  protected startTime = Date.now();
  private flushTimer?: NodeJS.Timeout;
  private connectionErrors = 0;

  constructor(config: TransportConfig = {}) {
    super({
      objectMode: true,
      transform: (chunk, encoding, callback) => {
        this.handleLog(chunk);
        callback();
      }
    });

    this.config = {
      level: 'info',
      maxWorkers: 4,
      batchSize: 100,
      flushInterval: 5000,
      maxRetries: 3,
      retryDelay: 1000,
      enableMetrics: true,
      ...config
    };

    this.metrics = {
      logsSent: 0,
      logsFailed: 0,
      bytesSent: 0,
      successRate: 100,
      queueSize: 0,
      healthy: true,
      running: false,
      connectionErrors: 0,
      uptime: 0
    };

    this.retryPolicy = {
      maxAttempts: this.config.maxRetries,
      baseDelay: this.config.retryDelay,
      maxDelay: 30000,
      backoffMultiplier: 2,
      jitter: 0.1
    };

    this.batchProcessor = new SimpleBatchProcessor(
      this.config.batchSize,
      async (messages: LogMessage[]) => {
        await this.sendBatch(messages);
      }
    );

    this.healthChecker = new SimpleHealthChecker(
      this.performHealthCheck.bind(this)
    );

    this.setupFlushTimer();
  }

  /**
   * Start the transport
   */
  async start(): Promise<void> {
    if (this.running) return;

    try {
      await this.initialize();
      this.running = true;
      this.metrics.running = true;
      this.metrics.healthy = true;
      console.log(`Transport started: ${this.constructor.name}`);
    } catch (error) {
      this.metrics.healthy = false;
      this.metrics.lastError = error as Error;
      throw error;
    }
  }

  /**
   * Stop the transport
   */
  async stop(): Promise<void> {
    if (!this.running) return;

    this.running = false;
    this.metrics.running = false;

    // Clear flush timer
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    // Flush remaining logs
    try {
      await this.batchProcessor.flush();
      await this.cleanup();
      console.log(`Transport stopped: ${this.constructor.name}`);
    } catch (error) {
      console.error('Error during transport shutdown:', error);
    }
  }

  /**
   * Get current metrics
   */
  getMetrics(): TransportMetrics {
    return {
      ...this.metrics,
      queueSize: this.batchProcessor.size(),
      uptime: Math.floor((Date.now() - this.startTime) / 1000),
      connectionErrors: this.connectionErrors
    };
  }

  /**
   * Abstract methods to be implemented by subclasses
   */
  protected abstract initialize(): Promise<void>;
  protected abstract cleanup(): Promise<void>;
  protected abstract sendBatch(messages: LogMessage[]): Promise<number>;
  protected abstract performHealthCheck(): Promise<boolean>;

  /**
   * Handle incoming log message
   */
  private handleLog(log: LogMessage): void {
    if (!this.running) return;

    try {
      this.batchProcessor.add(log);
      
      if (this.batchProcessor.isReady()) {
        this.batchProcessor.flush().catch(error => {
          console.error('Batch flush error:', error);
        });
      }
    } catch (error) {
      this.recordFailure(error as Error);
    }
  }

  /**
   * Setup periodic flush timer
   */
  private setupFlushTimer(): void {
    this.flushTimer = setInterval(async () => {
      if (this.batchProcessor.size() > 0) {
        try {
          await this.batchProcessor.flush();
        } catch (error) {
          console.error('Periodic flush error:', error);
        }
      }
    }, this.config.flushInterval);
  }

  /**
   * Record successful operation
   */
  protected recordSuccess(bytesSent: number = 0): void {
    this.metrics.logsSent++;
    this.metrics.bytesSent += bytesSent;
    this.updateSuccessRate();
  }

  /**
   * Record failed operation
   */
  protected recordFailure(error: Error): void {
    this.metrics.logsFailed++;
    this.metrics.lastError = error;
    
    // Track connection errors specifically
    if (this.isConnectionError(error)) {
      this.connectionErrors++;
      this.metrics.healthy = false;
    }
    
    this.updateSuccessRate();
  }

  /**
   * Update success rate calculation
   */
  private updateSuccessRate(): void {
    const total = this.metrics.logsSent + this.metrics.logsFailed;
    if (total > 0) {
      this.metrics.successRate = (this.metrics.logsSent / total) * 100;
    }
  }

  /**
   * Check if error is connection-related
   */
  private isConnectionError(error: Error): boolean {
    const connectionKeywords = [
      'ECONNREFUSED',
      'ENOTFOUND',
      'ETIMEDOUT',
      'ECONNRESET',
      'network',
      'connection'
    ];
    
    return connectionKeywords.some(keyword => 
      error.message.toLowerCase().includes(keyword.toLowerCase())
    );
  }

  /**
   * Retry an operation with exponential backoff
   */
  protected async retryOperation<T>(
    operation: () => Promise<T>,
    attempt: number = 1
  ): Promise<T> {
    try {
      return await operation();
    } catch (error) {
      if (attempt >= this.retryPolicy.maxAttempts) {
        throw error;
      }

      const delay = Math.min(
        this.retryPolicy.baseDelay * Math.pow(this.retryPolicy.backoffMultiplier, attempt - 1),
        this.retryPolicy.maxDelay
      );

      // Add jitter
      const jitteredDelay = delay * (1 + (Math.random() - 0.5) * this.retryPolicy.jitter);

      await new Promise(resolve => setTimeout(resolve, jitteredDelay));
      return this.retryOperation(operation, attempt + 1);
    }
  }
}

/**
 * Simple batch processor implementation
 */
class SimpleBatchProcessor<T> implements BatchProcessor<T> {
  private batch: T[] = [];

  constructor(
    private batchSize: number,
    private flushFn: (items: T[]) => Promise<void>
  ) {}

  add(item: T): void {
    this.batch.push(item);
  }

  async flush(): Promise<void> {
    if (this.batch.length === 0) return;

    const items = this.batch.splice(0);
    await this.flushFn(items);
  }

  size(): number {
    return this.batch.length;
  }

  isReady(): boolean {
    return this.batch.length >= this.batchSize;
  }
}

/**
 * Simple health checker implementation
 */
class SimpleHealthChecker implements HealthChecker {
  private healthy = true;
  private lastCheckTime = new Date();

  constructor(private checkFn: () => Promise<boolean>) {}

  async check(): Promise<boolean> {
    try {
      this.healthy = await this.checkFn();
      this.lastCheckTime = new Date();
      return this.healthy;
    } catch {
      this.healthy = false;
      this.lastCheckTime = new Date();
      return false;
    }
  }

  isHealthy(): boolean {
    return this.healthy;
  }

  lastCheck(): Date {
    return this.lastCheckTime;
  }
}