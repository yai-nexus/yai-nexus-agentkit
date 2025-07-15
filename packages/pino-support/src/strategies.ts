/**
 * 日志目录策略实现
 *
 * 提供与 loguru-support 语义一致的目录策略，包括：
 * - HourlyDirectoryStrategy: 按小时分目录存储日志
 * - DailyDirectoryStrategy: 按天分目录存储日志
 * - SimpleFileStrategy: 简单文件存储策略
 */

// 动态导入 Node.js 模块以避免浏览器打包错误
async function getNodeModules() {
  try {
    const [fs, path] = await Promise.all([import("fs"), import("path")]);
    return { fs, path };
  } catch (error) {
    console.warn("Failed to import Node.js modules:", error);
    return null;
  }
}

/**
 * 日志路径策略接口
 */
export interface DirectoryStrategy {
  /**
   * 生成日志文件路径
   * @param serviceName 服务名称
   * @returns 日志文件的完整路径
   */
  getLogPath(serviceName: string): Promise<string>;

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
async function getBaseDirectory(baseDir: string): Promise<string> {
  const nodeModules = await getNodeModules();
  if (!nodeModules) {
    throw new Error("Path operations require Node.js environment");
  }
  return nodeModules.path.resolve(process.cwd(), baseDir);
}

/**
 * 确保目录存在
 */
async function ensureDirectory(dirPath: string): Promise<boolean> {
  const nodeModules = await getNodeModules();
  if (!nodeModules) {
    console.error("Directory operations require Node.js environment");
    return false;
  }

  try {
    nodeModules.fs.mkdirSync(dirPath, { recursive: true });
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
  private currentHour: string | null = null;
  private currentDir: string | null = null;

  constructor(
    options: {
      baseDir?: string;
      timezone?: string;
      createSymlink?: boolean;
    } = {}
  ) {
    this.baseDir = options.baseDir || "logs";
    this.timezone =
      options.timezone || process.env.LOG_TIMEZONE || "Asia/Shanghai";
    this.createSymlink = options.createSymlink !== false; // 默认为 true
  }

  async getLogPath(serviceName: string): Promise<string> {
    const nodeModules = await getNodeModules();
    if (!nodeModules) {
      throw new Error("Path operations require Node.js environment");
    }

    const now = new Date();
    const hourDir = this.formatHourDirectory(now);

    // 缓存优化：如果还是同一小时，直接返回缓存的路径
    if (this.currentHour === hourDir && this.currentDir) {
      return nodeModules.path.join(this.currentDir, `${serviceName}.log`);
    }

    const logDir = await getBaseDirectory(
      nodeModules.path.join(this.baseDir, hourDir)
    );

    // 确保目录存在
    if (await ensureDirectory(logDir)) {
      this.currentHour = hourDir;
      this.currentDir = logDir;

      // 创建/更新软链接
      if (this.createSymlink) {
        const baseDirectory = await getBaseDirectory(this.baseDir);
        await this.createCurrentSymlink(baseDirectory, hourDir);
      }
    }

    return nodeModules.path.join(logDir, `${serviceName}.log`);
  }

  getMetadata(): Record<string, any> {
    return {
      strategyName: "hourly_directory",
      baseDir: this.baseDir,
      timezone: this.timezone,
      createSymlink: this.createSymlink,
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

  private async createCurrentSymlink(
    rootDir: string,
    hourDir: string
  ): Promise<void> {
    const nodeModules = await getNodeModules();
    if (!nodeModules) return;

    try {
      const symlinkPath = nodeModules.path.join(
        rootDir,
        this.baseDir,
        "current"
      );

      // 删除现有的软链接（如果存在）
      if (nodeModules.fs.existsSync(symlinkPath)) {
        nodeModules.fs.unlinkSync(symlinkPath);
      }

      // 创建新的软链接
      nodeModules.fs.symlinkSync(hourDir, symlinkPath, "dir");
    } catch (error) {
      // 软链接创建失败不应该影响日志功能
      console.warn(`Failed to create symlink:`, error);
    }
  }
}

/**
 * 按天分目录的日志策略
 */
export class DailyDirectoryStrategy implements DirectoryStrategy {
  private baseDir: string;
  private createSymlink: boolean;

  constructor(
    options: {
      baseDir?: string;
      createSymlink?: boolean;
    } = {}
  ) {
    this.baseDir = options.baseDir || "logs";
    this.createSymlink = options.createSymlink !== false;
  }

  async getLogPath(serviceName: string): Promise<string> {
    const nodeModules = await getNodeModules();
    if (!nodeModules) {
      throw new Error("Path operations require Node.js environment");
    }

    const now = new Date();
    const dayDir = this.formatDayDirectory(now);

    const logDir = await getBaseDirectory(
      nodeModules.path.join(this.baseDir, dayDir)
    );

    await ensureDirectory(logDir);

    return nodeModules.path.join(logDir, `${serviceName}.log`);
  }

  getMetadata(): Record<string, any> {
    return {
      strategyName: "daily_directory",
      baseDir: this.baseDir,
      createSymlink: this.createSymlink,
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

  async getLogPath(serviceName: string): Promise<string> {
    const nodeModules = await getNodeModules();
    if (!nodeModules) {
      throw new Error("Path operations require Node.js environment");
    }

    const logDir = await getBaseDirectory(this.baseDir);

    await ensureDirectory(logDir);

    const filename = this.filename.replace("{serviceName}", serviceName);
    return nodeModules.path.join(logDir, filename);
  }

  getMetadata(): Record<string, any> {
    return {
      strategyName: "simple_file",
      baseDir: this.baseDir,
      filename: this.filename,
    };
  }
}
