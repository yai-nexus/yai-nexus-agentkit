/**
 * Monitoring and alerting for pino transports.
 * 
 * Provides real-time metrics collection, health monitoring,
 * and configurable alerting for cloud logging transports.
 */

export { TransportMonitor, setupMonitoring } from './monitor';
export { ConsoleAlertChannel, WebhookAlertChannel } from './alerts';
export type { MonitoringConfig, AlertRule, AlertChannel } from '../types';