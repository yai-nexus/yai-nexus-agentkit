/**
 * @fileoverview
 * Server-side entry point for yai-nexus-fekit SDK.
 * This module only exports functions that are safe to use on the server.
 */

// Core server-side functionality
export { createYaiNexusHandler } from './handler';
export type { CreateYaiNexusHandlerOptions, YaiNexusHandler } from './handler'; 