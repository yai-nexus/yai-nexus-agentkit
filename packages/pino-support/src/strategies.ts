/**
 * 日志目录策略实现
 *
 * 提供与 loguru-support 语义一致的目录策略，包括：
 * - HourlyDirectoryStrategy: 按小时分目录存储日志
 * - DailyDirectoryStrategy: 按天分目录存储日志
 * - SimpleFileStrategy: 简单文件存储策略
 */

import * as fs from "fs";
import * as path from "path";

/**
 * 日志路径策略接口
 */
export interface DirectoryStrategy {
  /**
   * 生成日志文件路径
   * @param serviceName 服务名称
   * @returns 日志文件的完整路径
   */
  getLogPath(serviceName: string): string;

  /**
   * 获取策略元数据
   * @returns 策略相关的元数据信息
   */
  getMetadata(): Record<string, any>;
}

/**
 * 简化的根目录获取 - 直接使用当前工作目录
 * 用户需要通过 baseDir 参数指定正确的相对路径
 */
function getBaseDirectory(baseDir: string): string {
  return path.resolve(process.cwd(), baseDir);
}

/**
 * 确保目录存在
 */
function ensureDirectory(dirPath: string): boolean {
  try {
    fs.mkdirSync(dirPath, { recursive: true });
    return true;
  } catch (error) {
    console.error(`Failed to create directory ${dirPath}:`, error);
    return false;
  }
}

/**
 * 按小时分目录的日志策略
 *
 * 生成格式：logs/YYYYMMDD-HH/service-name.log
 * 与 Python loguru-support 的 HourlyDirectoryStrategy 保持一致
 */
export class HourlyDirectoryStrategy implements DirectoryStrategy {
  private baseDir: string;
  private timezone: string;
  private createSymlink: boolean;
  private createReadme: boolean;
  private currentHour: string | null = null;
  private currentDir: string | null = null;

  constructor(
    options: {
      baseDir?: string;
      timezone?: string;
      createSymlink?: boolean;
      createReadme?: boolean;
    } = {}
  ) {
    this.baseDir = options.baseDir || "logs";
    this.timezone =
      options.timezone || process.env.LOG_TIMEZONE || "Asia/Shanghai";
    this.createSymlink = options.createSymlink !== false; // 默认为 true
    this.createReadme = options.createReadme !== false; // 默认为 true
  }

  getLogPath(serviceName: string): string {
    const now = new Date();
    const hourDir = this.formatHourDirectory(now);

    // 缓存优化：如果还是同一小时，直接返回缓存的路径
    if (this.currentHour === hourDir && this.currentDir) {
      return path.join(this.currentDir, `${serviceName}.log`);
    }

    const logDir = getBaseDirectory(path.join(this.baseDir, hourDir));

    // 确保目录存在
    if (ensureDirectory(logDir)) {
      this.currentHour = hourDir;
      this.currentDir = logDir;

      // 创建/更新软链接
      if (this.createSymlink) {
        const baseDirectory = getBaseDirectory(this.baseDir);
        this.createCurrentSymlink(baseDirectory, hourDir);
      }

      // 创建 README
      if (this.createReadme) {
        this.createHourReadme(logDir, hourDir);
      }
    }

    return path.join(logDir, `${serviceName}.log`);
  }

  getMetadata(): Record<string, any> {
    return {
      strategyName: "hourly_directory",
      baseDir: this.baseDir,
      timezone: this.timezone,
      createSymlink: this.createSymlink,
      createReadme: this.createReadme,
      currentHour: this.currentHour,
      currentDir: this.currentDir,
    };
  }

  private formatHourDirectory(date: Date): string {
    // 格式：YYYYMMDD-HH
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hour = String(date.getHours()).padStart(2, "0");

    return `${year}${month}${day}-${hour}`;
  }

  private createCurrentSymlink(rootDir: string, hourDir: string): void {
    try {
      const symlinkPath = path.join(rootDir, this.baseDir, "current");

      // 删除现有的软链接（如果存在）
      if (fs.existsSync(symlinkPath)) {
        fs.unlinkSync(symlinkPath);
      }

      // 创建新的软链接
      fs.symlinkSync(hourDir, symlinkPath, "dir");
    } catch (error) {
      // 软链接创建失败不应该影响日志功能
      console.warn(`Failed to create symlink:`, error);
    }
  }

  private createHourReadme(logDir: string, hourDir: string): void {
    try {
      const readmePath = path.join(logDir, "README.md");

      // 如果 README 已存在，不覆盖
      if (fs.existsSync(readmePath)) {
        return;
      }

      const readmeContent = `# 日志目录：${hourDir}

此目录包含 ${hourDir
        .replace("-", " 年 ")
        .replace(/(\d{2})$/, "$1 时")} 的所有服务日志。

## 目录结构

\`\`\`
${hourDir}/
├── README.md           # 本文件
├── nextjs-app.log      # Next.js 应用日志
├── python-backend.log  # Python 后端日志
└── *.log              # 其他服务日志
\`\`\`

## 日志格式

- **Next.js 应用**: JSON 格式，包含请求追踪、性能指标等
- **Python 后端**: 结构化日志，包含上下文信息和错误追踪

## 相关目录

- \`../current/\` - 指向当前小时目录的软链接
- \`../${this.getPreviousHour(hourDir)}/\` - 上一小时的日志
- \`../${this.getNextHour(hourDir)}/\` - 下一小时的日志（如果存在）

---
生成时间: ${new Date().toISOString()}
`;

      fs.writeFileSync(readmePath, readmeContent, "utf8");
    } catch (error) {
      console.warn(`Failed to create README:`, error);
    }
  }

  private getPreviousHour(hourDir: string): string {
    const match = hourDir.match(/^(\d{4})(\d{2})(\d{2})-(\d{2})$/);
    if (!match) return hourDir;

    const [, year, month, day, hour] = match;
    const date = new Date(
      parseInt(year),
      parseInt(month) - 1,
      parseInt(day),
      parseInt(hour)
    );
    date.setHours(date.getHours() - 1);

    return this.formatHourDirectory(date);
  }

  private getNextHour(hourDir: string): string {
    const match = hourDir.match(/^(\d{4})(\d{2})(\d{2})-(\d{2})$/);
    if (!match) return hourDir;

    const [, year, month, day, hour] = match;
    const date = new Date(
      parseInt(year),
      parseInt(month) - 1,
      parseInt(day),
      parseInt(hour)
    );
    date.setHours(date.getHours() + 1);

    return this.formatHourDirectory(date);
  }
}

/**
 * 按天分目录的日志策略
 */
export class DailyDirectoryStrategy implements DirectoryStrategy {
  private baseDir: string;
  private createSymlink: boolean;
  private createReadme: boolean;

  constructor(
    options: {
      baseDir?: string;
      createSymlink?: boolean;
      createReadme?: boolean;
    } = {}
  ) {
    this.baseDir = options.baseDir || "logs";
    this.createSymlink = options.createSymlink !== false;
    this.createReadme = options.createReadme !== false;
  }

  getLogPath(serviceName: string): string {
    const now = new Date();
    const dayDir = this.formatDayDirectory(now);

    const logDir = getBaseDirectory(path.join(this.baseDir, dayDir));

    ensureDirectory(logDir);

    return path.join(logDir, `${serviceName}.log`);
  }

  getMetadata(): Record<string, any> {
    return {
      strategyName: "daily_directory",
      baseDir: this.baseDir,
      createSymlink: this.createSymlink,
      createReadme: this.createReadme,
    };
  }

  private formatDayDirectory(date: Date): string {
    // 格式：YYYYMMDD
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");

    return `${year}${month}${day}`;
  }
}

/**
 * 简单文件策略
 */
export class SimpleFileStrategy implements DirectoryStrategy {
  private baseDir: string;
  private filename: string;

  constructor(
    options: {
      baseDir?: string;
      filename?: string;
    } = {}
  ) {
    this.baseDir = options.baseDir || "logs";
    this.filename = options.filename || "{serviceName}.log";
  }

  getLogPath(serviceName: string): string {
    const logDir = getBaseDirectory(this.baseDir);

    ensureDirectory(logDir);

    const filename = this.filename.replace("{serviceName}", serviceName);
    return path.join(logDir, filename);
  }

  getMetadata(): Record<string, any> {
    return {
      strategyName: "simple_file",
      baseDir: this.baseDir,
      filename: this.filename,
    };
  }
}
