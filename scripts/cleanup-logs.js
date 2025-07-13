#!/usr/bin/env node
/**
 * 日志清理脚本
 * 
 * 自动清理按小时分目录的日志文件，支持：
 * - 按时间清理（默认保留7天）
 * - 按大小清理（可选）
 * - 干运行模式（预览清理操作）
 * - 详细输出模式
 * - 灵活配置选项
 * 
 * Usage:
 *   node scripts/cleanup-logs.js
 *   node scripts/cleanup-logs.js --retention-days 14
 *   node scripts/cleanup-logs.js --dry-run --verbose
 *   node scripts/cleanup-logs.js --max-size 1GB
 */

const fs = require('fs');
const path = require('path');

class LogCleaner {
  constructor(options = {}) {
    this.logsDir = options.logsDir || path.join(process.cwd(), 'logs');
    this.retentionDays = options.retentionDays !== undefined ? options.retentionDays : 7;
    this.maxSize = options.maxSize || null; // 如 "1GB", "500MB"
    this.dryRun = options.dryRun || false;
    this.verbose = options.verbose || false;
    this.excludePatterns = options.excludePatterns || ['current', 'README.md'];
  }

  /**
   * 执行日志清理
   */
  cleanupOldLogs() {
    if (!fs.existsSync(this.logsDir)) {
      this.log('Logs directory does not exist');
      return { removed: 0, errors: 0, freedSpace: 0 };
    }

    this.log(`Starting cleanup in: ${this.logsDir}`);
    this.log(`Retention days: ${this.retentionDays}`);
    if (this.maxSize) {
      this.log(`Max total size: ${this.maxSize}`);
    }
    this.log(`Dry run: ${this.dryRun}`);

    const cutoffTime = Date.now() - (this.retentionDays * 24 * 60 * 60 * 1000);
    const entries = fs.readdirSync(this.logsDir, { withFileTypes: true });
    
    let removed = 0;
    let errors = 0;
    let freedSpace = 0;

    // 收集需要清理的目录
    const candidatesForRemoval = [];

    for (const entry of entries) {
      if (this.shouldSkipEntry(entry.name)) {
        continue;
      }

      if (entry.isDirectory() && this.isHourlyDirectory(entry.name)) {
        const dirTime = this.parseHourlyDirectory(entry.name);
        
        if (dirTime && dirTime < cutoffTime) {
          const dirPath = path.join(this.logsDir, entry.name);
          const dirSize = this.getDirectorySize(dirPath);
          
          candidatesForRemoval.push({
            name: entry.name,
            path: dirPath,
            time: dirTime,
            size: dirSize
          });
        }
      }
    }

    // 按时间排序（最旧的先删除）
    candidatesForRemoval.sort((a, b) => a.time - b.time);

    this.log(`Found ${candidatesForRemoval.length} directories to clean up`);

    // 执行清理
    for (const candidate of candidatesForRemoval) {
      try {
        const sizeStr = this.formatSize(candidate.size);
        
        if (this.dryRun) {
          this.log(`[DRY RUN] Would remove: ${candidate.name} (${sizeStr})`);
        } else {
          this.log(`Removing old log directory: ${candidate.name} (${sizeStr})`);
          fs.rmSync(candidate.path, { recursive: true, force: true });
        }
        
        removed++;
        freedSpace += candidate.size;
      } catch (error) {
        this.log(`Error removing ${candidate.name}: ${error.message}`);
        errors++;
      }
    }

    // 如果设置了最大大小限制，检查是否需要进一步清理
    if (this.maxSize && !this.dryRun) {
      const maxBytes = this.parseSizeString(this.maxSize);
      const currentSize = this.getTotalLogsSize();
      
      if (currentSize > maxBytes) {
        this.log(`Current size (${this.formatSize(currentSize)}) exceeds limit (${this.maxSize})`);
        const { removed: sizeRemoved, freedSpace: sizeFeedSpace } = this.cleanupBySize(maxBytes);
        removed += sizeRemoved;
        freedSpace += sizeFeedSpace;
      }
    }

    return { removed, errors, freedSpace };
  }

  /**
   * 按大小清理（从最旧的开始删除直到满足大小限制）
   */
  cleanupBySize(maxBytes) {
    const entries = fs.readdirSync(this.logsDir, { withFileTypes: true });
    const directories = [];

    for (const entry of entries) {
      if (this.shouldSkipEntry(entry.name) || !entry.isDirectory() || !this.isHourlyDirectory(entry.name)) {
        continue;
      }

      const dirPath = path.join(this.logsDir, entry.name);
      const dirTime = this.parseHourlyDirectory(entry.name);
      const dirSize = this.getDirectorySize(dirPath);

      directories.push({
        name: entry.name,
        path: dirPath,
        time: dirTime,
        size: dirSize
      });
    }

    // 按时间排序（最旧的先删除）
    directories.sort((a, b) => a.time - b.time);

    let currentSize = this.getTotalLogsSize();
    let removed = 0;
    let freedSpace = 0;

    for (const dir of directories) {
      if (currentSize <= maxBytes) {
        break;
      }

      try {
        this.log(`Removing for size limit: ${dir.name} (${this.formatSize(dir.size)})`);
        fs.rmSync(dir.path, { recursive: true, force: true });
        currentSize -= dir.size;
        freedSpace += dir.size;
        removed++;
      } catch (error) {
        this.log(`Error removing ${dir.name}: ${error.message}`);
      }
    }

    return { removed, freedSpace };
  }

  /**
   * 检查是否应该跳过某个条目
   */
  shouldSkipEntry(name) {
    return this.excludePatterns.some(pattern => {
      if (typeof pattern === 'string') {
        return name === pattern;
      }
      if (pattern instanceof RegExp) {
        return pattern.test(name);
      }
      return false;
    });
  }

  /**
   * 检查是否为小时目录格式
   */
  isHourlyDirectory(name) {
    return /^\d{8}-\d{2}$/.test(name);
  }

  /**
   * 解析小时目录名为时间戳
   */
  parseHourlyDirectory(name) {
    const match = name.match(/^(\d{4})(\d{2})(\d{2})-(\d{2})$/);
    if (!match) return null;
    
    const [, year, month, day, hour] = match;
    return new Date(
      parseInt(year), 
      parseInt(month) - 1, 
      parseInt(day), 
      parseInt(hour)
    ).getTime();
  }

  /**
   * 获取目录大小
   */
  getDirectorySize(dirPath) {
    let size = 0;
    try {
      const files = fs.readdirSync(dirPath);
      
      for (const file of files) {
        const filePath = path.join(dirPath, file);
        const stats = fs.statSync(filePath);
        
        if (stats.isFile()) {
          size += stats.size;
        } else if (stats.isDirectory()) {
          size += this.getDirectorySize(filePath);
        }
      }
    } catch (error) {
      // 忽略访问错误
    }
    
    return size;
  }

  /**
   * 获取整个 logs 目录的总大小
   */
  getTotalLogsSize() {
    return this.getDirectorySize(this.logsDir);
  }

  /**
   * 格式化大小为人类可读格式
   */
  formatSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  }

  /**
   * 解析大小字符串为字节数
   */
  parseSizeString(sizeStr) {
    const match = sizeStr.match(/^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB)$/i);
    if (!match) {
      throw new Error(`Invalid size format: ${sizeStr}`);
    }
    
    const [, num, unit] = match;
    const multipliers = {
      'B': 1,
      'KB': 1024,
      'MB': 1024 * 1024,
      'GB': 1024 * 1024 * 1024,
      'TB': 1024 * 1024 * 1024 * 1024
    };
    
    return parseFloat(num) * multipliers[unit.toUpperCase()];
  }

  /**
   * 获取统计信息
   */
  getStats() {
    if (!fs.existsSync(this.logsDir)) {
      return { totalDirs: 0, totalSize: 0, oldestDir: null, newestDir: null };
    }

    const entries = fs.readdirSync(this.logsDir, { withFileTypes: true });
    let totalDirs = 0;
    let totalSize = 0;
    let oldestTime = Infinity;
    let newestTime = 0;
    let oldestDir = null;
    let newestDir = null;

    for (const entry of entries) {
      if (this.shouldSkipEntry(entry.name) || !entry.isDirectory() || !this.isHourlyDirectory(entry.name)) {
        continue;
      }

      totalDirs++;
      const dirPath = path.join(this.logsDir, entry.name);
      const dirSize = this.getDirectorySize(dirPath);
      const dirTime = this.parseHourlyDirectory(entry.name);
      
      totalSize += dirSize;
      
      if (dirTime < oldestTime) {
        oldestTime = dirTime;
        oldestDir = entry.name;
      }
      
      if (dirTime > newestTime) {
        newestTime = dirTime;
        newestDir = entry.name;
      }
    }

    return { 
      totalDirs, 
      totalSize, 
      oldestDir: oldestDir ? { name: oldestDir, time: new Date(oldestTime) } : null,
      newestDir: newestDir ? { name: newestDir, time: new Date(newestTime) } : null
    };
  }

  /**
   * 日志输出
   */
  log(message) {
    if (this.verbose || this.dryRun) {
      const timestamp = new Date().toISOString();
      console.log(`[${timestamp}] ${message}`);
    }
  }
}

/**
 * 解析命令行参数
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {};
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    switch (arg) {
      case '--retention-days':
        options.retentionDays = parseInt(args[++i]);
        break;
      case '--logs-dir':
        options.logsDir = args[++i];
        break;
      case '--max-size':
        options.maxSize = args[++i];
        break;
      case '--dry-run':
        options.dryRun = true;
        break;
      case '--verbose':
        options.verbose = true;
        break;
      case '--stats':
        options.showStats = true;
        break;
      case '--help':
      case '-h':
        showHelp();
        process.exit(0);
        break;
      default:
        console.error(`Unknown option: ${arg}`);
        process.exit(1);
    }
  }
  
  return options;
}

/**
 * 显示帮助信息
 */
function showHelp() {
  console.log(`
Log Cleanup Utility

Usage: node cleanup-logs.js [options]

Options:
  --retention-days N    Days to retain logs (default: 7)
  --logs-dir PATH      Path to logs directory (default: ./logs)
  --max-size SIZE      Maximum total size (e.g., "1GB", "500MB")
  --dry-run           Preview operations without making changes
  --verbose           Enable detailed output
  --stats             Show current statistics only
  --help, -h          Show this help message

Examples:
  node cleanup-logs.js --retention-days 14 --verbose
  node cleanup-logs.js --dry-run --max-size 500MB
  node cleanup-logs.js --stats
`);
}

/**
 * 主执行函数
 */
function main() {
  try {
    const options = parseArgs();
    const cleaner = new LogCleaner(options);
    
    if (options.showStats) {
      const stats = cleaner.getStats();
      console.log('\n=== Log Directory Statistics ===');
      console.log(`Total directories: ${stats.totalDirs}`);
      console.log(`Total size: ${cleaner.formatSize(stats.totalSize)}`);
      if (stats.oldestDir) {
        console.log(`Oldest directory: ${stats.oldestDir.name} (${stats.oldestDir.time.toLocaleString()})`);
      }
      if (stats.newestDir) {
        console.log(`Newest directory: ${stats.newestDir.name} (${stats.newestDir.time.toLocaleString()})`);
      }
      console.log('===============================\n');
      return;
    }
    
    const startTime = Date.now();
    const result = cleaner.cleanupOldLogs();
    const duration = Date.now() - startTime;
    
    console.log('\n=== Cleanup Results ===');
    console.log(`Removed: ${result.removed} directories`);
    console.log(`Errors: ${result.errors}`);
    console.log(`Space freed: ${cleaner.formatSize(result.freedSpace)}`);
    console.log(`Duration: ${duration}ms`);
    console.log('=======================\n');
    
    if (result.errors > 0) {
      process.exit(1);
    }
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

// 仅在直接运行时执行
if (require.main === module) {
  main();
}

module.exports = { LogCleaner };