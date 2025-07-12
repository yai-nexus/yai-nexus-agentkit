/**
 * Alibaba Cloud SLS (Simple Log Service) transport for pino.
 * 
 * Provides high-performance, reliable log shipping to Alibaba Cloud SLS
 * with automatic batching, retry logic, and monitoring.
 */

export { SlsTransport, createSlsTransport } from './transport';
export { SlsConfig } from './config';
export type { SlsTransportOptions } from './types';