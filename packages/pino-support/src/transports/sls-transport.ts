/**
 * SLS transport for pino using pino.transport() API
 * 
 * This creates a pino-compatible transport that can be used with
 * the unified logging configuration system.
 */

import { Transform } from 'stream';
import { SlsTransport } from '../sls/transport';
import { SlsTransportOptions } from '../sls/types';

/**
 * Create an SLS transport that works with pino.transport()
 */
export function createSlsPinoTransport(options: SlsTransportOptions) {
  return async function slsTransportFactory() {
    const slsTransport = new SlsTransport(options);
    await slsTransport.start();
    
    const transform = new Transform({
      objectMode: true,
      transform(chunk, encoding, callback) {
        try {
          // Parse the log message
          const logMessage = typeof chunk === 'string' ? JSON.parse(chunk) : chunk;
          
          // Send to SLS transport
          slsTransport.write(logMessage);
          
          callback();
        } catch (error) {
          callback(error instanceof Error ? error : new Error(String(error)));
        }
      }
    });
    
    // Handle cleanup on process exit
    process.on('exit', () => {
      slsTransport.stop();
    });
    
    process.on('SIGINT', () => {
      slsTransport.stop();
    });
    
    process.on('SIGTERM', () => {
      slsTransport.stop();
    });
    
    return transform;
  };
}

/**
 * SLS transport options for pino.transport()
 */
export interface SlsTransportConfig {
  target: string;
  options: SlsTransportOptions;
}

/**
 * Create SLS transport configuration for pino.transport()
 */
export function createSlsTransportConfig(options: SlsTransportOptions): SlsTransportConfig {
  return {
    target: require.resolve('./sls-transport-worker'),
    options
  };
}