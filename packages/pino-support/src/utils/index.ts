/**
 * Utility functions for pino transport lifecycle management.
 * 
 * Provides graceful shutdown, signal handling, and framework
 * integration helpers.
 */

export { GracefulShutdown, setupGracefulShutdown, createProductionSetup } from './shutdown';
export type { GracefulShutdownConfig } from '../types';