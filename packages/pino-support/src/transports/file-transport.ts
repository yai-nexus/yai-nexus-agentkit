/**
 * File transport implementation for pino
 * 
 * Provides directory-based file logging with hourly/daily rotation strategies
 * that match the Python loguru-support implementation.
 */

import { createWriteStream, WriteStream } from 'fs';
import { mkdir } from 'fs/promises';
import { dirname, join } from 'path';
import { Transform } from 'stream';
import { findMonorepoRoot } from '../utils';

export interface FileTransportOptions {
  /** Base directory for log files */
  baseDir?: string;
  /** Directory strategy (hourly, daily, simple) */
  strategy?: 'hourly' | 'daily' | 'simple';
  /** Service name for file naming */
  serviceName: string;
  /** Create symlink to current log directory */
  createSymlink?: boolean;
  /** Create README in log directories */
  createReadme?: boolean;
  /** Maximum file size before rotation */
  maxSize?: number;
  /** Maximum number of files to keep */
  maxFiles?: number;
  /** 项目根目录（可选，优先使用） */
  projectRoot?: string;
}

interface DirectoryStrategy {
  getLogPath(serviceName: string): string;
  getCurrentDirectory(): string;
  getMetadata(): Record<string, any>;
}

class HourlyDirectoryStrategy implements DirectoryStrategy {
  private currentHour: string | null = null;
  private currentDir: string | null = null;
  private projectRoot: string;

  constructor(
    private baseDir: string,
    private createSymlink: boolean = true,
    private createReadme: boolean = true,
    projectRoot?: string
  ) {
    this.projectRoot = projectRoot || findMonorepoRoot();
  }

  getLogPath(serviceName: string): string {
    const now = new Date();
    const hourDir = this.formatHourDirectory(now);
    
    // Cache optimization: if still same hour, return cached path
    if (this.currentHour === hourDir && this.currentDir) {
      return join(this.currentDir, `${serviceName}.log`);
    }
    
    // 使用项目根目录而不是当前工作目录
    const logDir = join(this.projectRoot, this.baseDir, hourDir);
    
    // Ensure directory exists
    this.ensureDirectory(logDir).then(() => {
      this.currentHour = hourDir;
      this.currentDir = logDir;
      
      if (this.createSymlink) {
        this.createCurrentSymlink(hourDir).catch(() => {
          // Ignore symlink failures
        });
      }
      
      if (this.createReadme) {
        this.createHourReadme(logDir, hourDir).catch(() => {
          // Ignore README failures
        });
      }
    }).catch(() => {
      // Fallback to simple directory structure if creation fails
    });
    
    return join(logDir, `${serviceName}.log`);
  }

  getCurrentDirectory(): string {
    return this.currentDir || join(this.projectRoot, this.baseDir);
  }

  getMetadata(): Record<string, any> {
    return {
      strategy_name: 'hourly_directory',
      base_dir: this.baseDir,
      create_symlink: this.createSymlink,
      create_readme: this.createReadme,
      current_hour: this.currentHour
    };
  }

  private formatHourDirectory(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    return `${year}${month}${day}-${hour}`;
  }

  private async ensureDirectory(path: string): Promise<void> {
    try {
      await mkdir(path, { recursive: true });
    } catch (error) {
      // Directory might already exist
    }
  }

  private async createCurrentSymlink(hourDir: string): Promise<void> {
    try {
      const { symlink, unlink } = await import('fs/promises');
      const currentLink = join(this.projectRoot, this.baseDir, 'current');
      
      try {
        await unlink(currentLink);
      } catch {
        // Link might not exist
      }
      
      await symlink(hourDir, currentLink);
    } catch {
      // Symlink creation failed, continue without it
    }
  }

  private async createHourReadme(logDir: string, hourDir: string): Promise<void> {
    try {
      const { writeFile, access } = await import('fs/promises');
      const readmePath = join(logDir, 'README.md');
      
      // Check if README already exists
      try {
        await access(readmePath);
        return; // README exists, don't overwrite
      } catch {
        // README doesn't exist, create it
      }
      
      const content = `# 日志目录: ${hourDir}

创建时间: ${new Date().toISOString()}

## 包含的日志文件

- \`python-backend.log\`: Python 后端服务日志
- \`nextjs-app.log\`: Next.js 前端应用日志 (如果存在)

## 日志格式

所有日志文件都采用结构化格式，便于程序化处理和分析。

## 保留策略

日志文件会保留 7 天，之后自动清理。

## 访问当前日志

可以通过 \`logs/current\` 软链接访问当前小时的日志目录。
`;
      
      await writeFile(readmePath, content, 'utf-8');
    } catch {
      // README creation failed, continue without it
    }
  }
}

class DailyDirectoryStrategy implements DirectoryStrategy {
  private currentDay: string | null = null;
  private currentDir: string | null = null;
  private projectRoot: string;

  constructor(
    private baseDir: string,
    private createSymlink: boolean = true,
    projectRoot?: string
  ) {
    this.projectRoot = projectRoot || findMonorepoRoot();
  }

  getLogPath(serviceName: string): string {
    const now = new Date();
    const dayDir = this.formatDayDirectory(now);
    
    if (this.currentDay === dayDir && this.currentDir) {
      return join(this.currentDir, `${serviceName}.log`);
    }
    
    // 使用项目根目录而不是当前工作目录
    const logDir = join(this.projectRoot, this.baseDir, dayDir);
    
    this.ensureDirectory(logDir).then(() => {
      this.currentDay = dayDir;
      this.currentDir = logDir;
      
      if (this.createSymlink) {
        this.createCurrentSymlink(dayDir).catch(() => {});
      }
    }).catch(() => {});
    
    return join(logDir, `${serviceName}.log`);
  }

  getCurrentDirectory(): string {
    return this.currentDir || join(this.projectRoot, this.baseDir);
  }

  getMetadata(): Record<string, any> {
    return {
      strategy_name: 'daily_directory',
      base_dir: this.baseDir,
      create_symlink: this.createSymlink,
      current_day: this.currentDay
    };
  }

  private formatDayDirectory(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}${month}${day}`;
  }

  private async ensureDirectory(path: string): Promise<void> {
    try {
      await mkdir(path, { recursive: true });
    } catch (error) {
      // Directory might already exist
    }
  }

  private async createCurrentSymlink(dayDir: string): Promise<void> {
    try {
      const { symlink, unlink } = await import('fs/promises');
      const currentLink = join(this.projectRoot, this.baseDir, 'current');
      
      try {
        await unlink(currentLink);
      } catch {
        // Link might not exist
      }
      
      await symlink(dayDir, currentLink);
    } catch {
      // Symlink creation failed, continue without it
    }
  }
}

class SimpleFileStrategy implements DirectoryStrategy {
  private projectRoot: string;
  constructor(
    private baseDir: string,
    private filenameTemplate: string = '{serviceName}.log',
    projectRoot?: string
  ) {
    this.projectRoot = projectRoot || findMonorepoRoot();
  }

  getLogPath(serviceName: string): string {
    // 使用项目根目录而不是当前工作目录
    const logDir = join(this.projectRoot, this.baseDir);
    
    this.ensureDirectory(logDir).catch(() => {});
    
    const filename = this.filenameTemplate.replace('{serviceName}', serviceName);
    return join(logDir, filename);
  }

  getCurrentDirectory(): string {
    return join(this.projectRoot, this.baseDir);
  }

  getMetadata(): Record<string, any> {
    return {
      strategy_name: 'simple_file',
      base_dir: this.baseDir,
      filename_template: this.filenameTemplate
    };
  }

  private async ensureDirectory(path: string): Promise<void> {
    try {
      await mkdir(path, { recursive: true });
    } catch (error) {
      // Directory might already exist
    }
  }
}

export class FileTransport extends Transform {
  private strategy: DirectoryStrategy;
  private writeStream: WriteStream | null = null;
  private currentLogPath: string | null = null;

  constructor(private options: FileTransportOptions) {
    super({ objectMode: true });
    
    const baseDir = options.baseDir || 'logs';
    const strategy = options.strategy || 'hourly';
    const projectRoot = options.projectRoot;
    
    // 调试输出
    const projectRootForTransport = projectRoot || findMonorepoRoot();
    console.log('[FileTransport] findMonorepoRoot() =', projectRootForTransport);
    
    switch (strategy) {
      case 'hourly':
        this.strategy = new HourlyDirectoryStrategy(
          baseDir,
          options.createSymlink,
          options.createReadme,
          projectRoot
        );
        break;
      case 'daily':
        this.strategy = new DailyDirectoryStrategy(
          baseDir,
          options.createSymlink,
          projectRoot
        );
        break;
      case 'simple':
      default:
        this.strategy = new SimpleFileStrategy(baseDir, undefined, projectRoot);
        break;
    }
  }

  _transform(chunk: any, encoding: BufferEncoding, callback: (error?: Error | null, data?: any) => void): void {
    try {
      const logPath = this.strategy.getLogPath(this.options.serviceName);
      
      // Check if we need to rotate to a new file
      if (logPath !== this.currentLogPath) {
        this.rotateLogFile(logPath);
      }
      
      if (this.writeStream) {
        // Format the log entry
        const logLine = typeof chunk === 'string' ? chunk : JSON.stringify(chunk);
        this.writeStream.write(logLine + '\n');
      }
      
      callback();
    } catch (error) {
      callback(error as Error);
    }
  }

  _flush(callback: (error?: Error | null) => void): void {
    if (this.writeStream) {
      this.writeStream.end(callback);
    } else {
      callback();
    }
  }

  private rotateLogFile(newLogPath: string): void {
    // Close current stream if it exists
    if (this.writeStream) {
      this.writeStream.end();
    }
    
    // Ensure directory exists
    const dir = dirname(newLogPath);
    mkdir(dir, { recursive: true }).catch(() => {});
    
    // Create new write stream
    this.writeStream = createWriteStream(newLogPath, { flags: 'a' });
    this.currentLogPath = newLogPath;
  }

  getMetadata(): Record<string, any> {
    return {
      ...this.strategy.getMetadata(),
      current_log_path: this.currentLogPath,
      service_name: this.options.serviceName
    };
  }
}

export function createFileTransport(options: FileTransportOptions): FileTransport {
  return new FileTransport(options);
}

// Default export for pino transport
export default function(options: FileTransportOptions): FileTransport {
  return new FileTransport(options);
}