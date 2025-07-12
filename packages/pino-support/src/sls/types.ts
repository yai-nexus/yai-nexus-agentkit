/**
 * Type definitions for SLS transport.
 */

import { TransportConfig } from '../types';

export interface SlsTransportOptions extends TransportConfig {
  /** SLS endpoint (e.g., 'cn-hangzhou.log.aliyuncs.com') */
  endpoint: string;
  /** Access Key ID */
  accessKeyId: string;
  /** Access Key Secret */
  accessKeySecret: string;
  /** SLS project name */
  project: string;
  /** SLS logstore name */
  logstore: string;
  /** Log topic (optional) */
  topic?: string;
  /** Log source (optional) */
  source?: string;
  /** Security token for STS (optional) */
  securityToken?: string;
  /** Compression type */
  compression?: 'gzip' | 'lz4' | 'none';
  /** Custom headers */
  headers?: Record<string, string>;
}

export interface SlsLogGroup {
  topic: string;
  source: string;
  logs: SlsLog[];
}

export interface SlsLog {
  time: number;
  contents: SlsLogContent[];
}

export interface SlsLogContent {
  key: string;
  value: string;
}

export interface SlsResponse {
  requestId: string;
  statusCode: number;
}

export interface SlsAuthInfo {
  accessKeyId: string;
  accessKeySecret: string;
  securityToken?: string;
}

export interface SlsRequestConfig {
  endpoint: string;
  project: string;
  logstore: string;
  compression: string;
  headers: Record<string, string>;
}