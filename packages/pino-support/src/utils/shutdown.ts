/**
 * Graceful shutdown utilities for pino transports.
 */

import { BaseTransport } from '../base';
import { GracefulShutdownConfig } from '../types';

export class GracefulShutdown {
  private transports = new Set<BaseTransport>();
  private shutdownCallbacks: Array<() => Promise<void> | void> = [];
  private shutdownComplete = false;

  /**
   * Register a transport for graceful shutdown
   */
  registerTransport(transport: BaseTransport): void {
    this.transports.add(transport);
  }

  /**
   * Unregister a transport
   */
  unregisterTransport(transport: BaseTransport): void {
    this.transports.delete(transport);
  }

  /**
   * Register a custom shutdown callback
   */
  registerCallback(callback: () => Promise<void> | void): void {
    this.shutdownCallbacks.push(callback);
  }

  /**
   * Shutdown all registered transports and run callbacks
   */
  async shutdown(timeout = 30000): Promise<void> {
    if (this.shutdownComplete) return;

    this.shutdownComplete = true;
    console.log('Gracefully shutting down pino transports...');

    // Run custom callbacks first
    for (const callback of this.shutdownCallbacks) {
      try {
        await callback();
      } catch (error) {
        console.error('Error in shutdown callback:', error);
      }
    }

    // Shutdown all transports
    const shutdownPromises = Array.from(this.transports).map(async (transport) => {
      try {
        await transport.stop();
      } catch (error) {
        console.error('Error shutting down transport:', error);
      }
    });

    if (shutdownPromises.length > 0) {
      try {
        await Promise.race([
          Promise.allSettled(shutdownPromises),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Shutdown timeout')), timeout)
          )
        ]);
        console.log('All transports shut down successfully');
      } catch (error) {
        console.warn(`Shutdown timed out after ${timeout}ms`);
      }
    }
  }

  /**
   * Setup signal handlers
   */
  setupSignalHandlers(signals: NodeJS.Signals[] = ['SIGINT', 'SIGTERM']): void {
    const handleSignal = (signal: string) => {
      console.log(`Received ${signal}, initiating graceful shutdown...`);
      this.shutdown()
        .then(() => process.exit(0))
        .catch((error) => {
          console.error('Shutdown error:', error);
          process.exit(1);
        });
    };

    for (const signal of signals) {
      process.on(signal, () => handleSignal(signal));
    }
  }

  /**
   * Setup process exit handler
   */
  setupExitHandler(): void {
    process.on('beforeExit', () => {
      if (!this.shutdownComplete && this.transports.size > 0) {
        console.log('Process exiting, initiating graceful shutdown...');
        // Note: beforeExit allows async operations
        this.shutdown().catch(console.error);
      }
    });
  }

  /**
   * Setup for Next.js applications
   */
  setupNextJS(): void {
    // Next.js doesn't have built-in shutdown hooks for production,
    // so we rely on signal handlers and process events
    this.setupSignalHandlers();
    this.setupExitHandler();
  }

  /**
   * Setup for Express applications
   */
  setupExpress(server: unknown): void {
    // Express server shutdown integration
    this.setupSignalHandlers();
    this.setupExitHandler();

    // If server has a close method, register it as a callback
    if (server && typeof server === 'object' && 'close' in server) {
      this.registerCallback(async () => {
        return new Promise<void>((resolve, reject) => {
          const closeMethod = (server as any).close;
          if (typeof closeMethod === 'function') {
            closeMethod.call(server, (error: unknown) => {
              if (error) reject(error);
              else resolve();
            });
          } else {
            resolve();
          }
        });
      });
    }
  }

  /**
   * Setup for Fastify applications
   */
  setupFastify(fastify: unknown): void {
    // Fastify has built-in graceful shutdown support
    this.setupSignalHandlers();
    
    // Register with Fastify's shutdown hooks if available
    if (fastify && typeof fastify === 'object' && 'addHook' in fastify) {
      const addHook = (fastify as any).addHook;
      if (typeof addHook === 'function') {
        addHook.call(fastify, 'onClose', async () => {
          await this.shutdown();
        });
      }
    }
  }
}

// Global shutdown manager
const globalShutdown = new GracefulShutdown();

/**
 * Register a transport for global graceful shutdown
 */
export function registerTransportForShutdown(transport: BaseTransport): void {
  globalShutdown.registerTransport(transport);
}

/**
 * Setup graceful shutdown with configuration
 */
export function setupGracefulShutdown(
  transports: BaseTransport[],
  config: GracefulShutdownConfig = {}
): GracefulShutdown {
  const shutdown = new GracefulShutdown();

  // Register transports
  for (const transport of transports) {
    shutdown.registerTransport(transport);
  }

  // Setup signal handlers
  if (config.signals) {
    shutdown.setupSignalHandlers(config.signals);
  } else {
    shutdown.setupSignalHandlers();
  }

  // Setup exit handler
  if (config.enableAtexit !== false) {
    shutdown.setupExitHandler();
  }

  return shutdown;
}

/**
 * One-line production setup
 */
export function createProductionSetup(options: {
  transports: BaseTransport[];
  framework?: 'nextjs' | 'express' | 'fastify';
  app?: unknown;
  config?: GracefulShutdownConfig;
}): void {
  const shutdown = setupGracefulShutdown(options.transports, options.config);

  // Framework-specific setup
  switch (options.framework) {
    case 'nextjs':
      shutdown.setupNextJS();
      break;
    case 'express':
      shutdown.setupExpress(options.app);
      break;
    case 'fastify':
      shutdown.setupFastify(options.app);
      break;
    default:
      // Already setup with basic signal handlers
      break;
  }

  console.log(`Production setup complete with ${options.transports.length} transports`);
}