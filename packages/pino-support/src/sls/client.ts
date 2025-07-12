/**
 * SLS HTTP client implementation.
 * 
 * Handles authentication, request signing, compression, and HTTP communication
 * with Alibaba Cloud SLS service.
 */

import { createHash, createHmac } from 'crypto';
import { gzip } from 'zlib';
import { promisify } from 'util';
import { SlsConfig } from './config';
import { SlsLogGroup, SlsResponse } from './types';

const gzipAsync = promisify(gzip);

export class SlsClient {
  private config: SlsConfig;
  private baseUrl: string;

  constructor(config: SlsConfig) {
    this.config = config;
    this.baseUrl = config.getBaseUrl();
  }

  /**
   * Initialize the client
   */
  async initialize(): Promise<void> {
    // Perform initial health check
    const healthy = await this.healthCheck();
    if (!healthy) {
      throw new Error('SLS service is not accessible');
    }
  }

  /**
   * Cleanup resources
   */
  async cleanup(): Promise<void> {
    // No cleanup needed for HTTP client
  }

  /**
   * Send logs to SLS
   */
  async putLogs(logGroup: SlsLogGroup): Promise<SlsResponse> {
    const body = JSON.stringify(logGroup);
    let compressedBody: Buffer;
    let contentEncoding = '';

    // Compress if enabled
    if (this.config.compression === 'gzip') {
      compressedBody = await gzipAsync(body);
      contentEncoding = 'gzip';
    } else {
      compressedBody = Buffer.from(body, 'utf-8');
    }

    const contentMd5 = createHash('md5').update(compressedBody).digest('hex').toUpperCase();
    const contentLength = compressedBody.length;
    const date = new Date().toUTCString();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Content-Length': contentLength.toString(),
      'Content-MD5': contentMd5,
      'Date': date,
      'Host': `${this.config.project}.${this.config.endpoint}`,
      'x-log-apiversion': '0.6.0',
      'x-log-compresstype': this.config.compression === 'gzip' ? 'gzip' : '',
      ...this.config.headers
    };

    if (contentEncoding) {
      headers['Content-Encoding'] = contentEncoding;
    }

    if (this.config.securityToken) {
      headers['x-acs-security-token'] = this.config.securityToken;
    }

    // Generate authorization header
    const authorization = this.generateAuthorization(
      'POST',
      `/logstores/${this.config.logstore}/shards/lb`,
      headers
    );
    headers['Authorization'] = authorization;

    // Make HTTP request
    const url = `${this.baseUrl}/logstores/${this.config.logstore}/shards/lb`;
    
    try {
      const response = await this.makeRequest(url, {
        method: 'POST',
        headers,
        body: compressedBody
      });

      return {
        requestId: response.headers['x-log-requestid'] || '',
        statusCode: response.status
      };
    } catch (error) {
      throw new Error(`SLS request failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Perform health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const date = new Date().toUTCString();
      const headers: Record<string, string> = {
        'Date': date,
        'Host': `${this.config.project}.${this.config.endpoint}`,
        'x-log-apiversion': '0.6.0'
      };

      if (this.config.securityToken) {
        headers['x-acs-security-token'] = this.config.securityToken;
      }

      const authorization = this.generateAuthorization(
        'GET',
        `/logstores/${this.config.logstore}`,
        headers
      );
      headers['Authorization'] = authorization;

      const url = `${this.baseUrl}/logstores/${this.config.logstore}`;
      const response = await this.makeRequest(url, {
        method: 'GET',
        headers
      });

      return response.status >= 200 && response.status < 300;
    } catch {
      return false;
    }
  }

  /**
   * Generate SLS authorization header
   */
  private generateAuthorization(
    method: string,
    path: string,
    headers: Record<string, string>
  ): string {
    // Collect headers for signing
    const slsHeaders: string[] = [];
    const sortedKeys = Object.keys(headers)
      .filter(key => key.toLowerCase().startsWith('x-log-') || key.toLowerCase().startsWith('x-acs-'))
      .sort();

    for (const key of sortedKeys) {
      slsHeaders.push(`${key.toLowerCase()}:${headers[key]}`);
    }

    // Build string to sign
    const stringToSign = [
      method,
      headers['Content-MD5'] || '',
      headers['Content-Type'] || '',
      headers['Date'] || '',
      ...slsHeaders,
      path
    ].join('\\n');

    // Generate signature
    const signature = createHmac('sha1', this.config.accessKeySecret)
      .update(stringToSign)
      .digest('base64');

    return `LOG ${this.config.accessKeyId}:${signature}`;
  }

  /**
   * Make HTTP request (using fetch or fallback)
   */
  private async makeRequest(
    url: string,
    options: {
      method: string;
      headers: Record<string, string>;
      body?: Buffer;
    }
  ): Promise<{ status: number; headers: Record<string, string> }> {
    // Try to use native fetch (Node.js 18+)
    if (typeof fetch !== 'undefined') {
      const response = await fetch(url, {
        method: options.method,
        headers: options.headers,
        body: options.body
      });

      const headers: Record<string, string> = {};
      response.headers.forEach((value, key) => {
        headers[key] = value;
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      return {
        status: response.status,
        headers
      };
    }

    // Fallback to axios if available
    try {
      const axios = await import('axios');
      const response = await axios.default({
        url,
        method: options.method,
        headers: options.headers,
        data: options.body,
        validateStatus: () => true
      });

      if (response.status >= 400) {
        throw new Error(`HTTP ${response.status}: ${response.data}`);
      }

      return {
        status: response.status,
        headers: response.headers
      };
    } catch (importError) {
      throw new Error('No HTTP client available. Please ensure Node.js 18+ or install axios.');
    }
  }
}