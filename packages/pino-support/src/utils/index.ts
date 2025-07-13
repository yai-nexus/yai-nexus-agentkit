/**
 * Utility functions for pino transport lifecycle management.
 * 
 * Provides graceful shutdown, signal handling, and framework
 * integration helpers.
 */

import { existsSync, readFileSync } from 'fs';
import { join, dirname } from 'path';

const ROOT_MARKERS = [
  'pnpm-workspace.yaml',
  'yarn.lock',
  'lerna.json',
];

/**
 * 查找 monorepo 根目录（优先环境变量、支持多种标志文件）
 */
export function findMonorepoRoot(): string {
  if (process.env.MONOREPO_ROOT && existsSync(process.env.MONOREPO_ROOT)) {
    return process.env.MONOREPO_ROOT;
  }
  let currentDir = process.cwd();
  while (currentDir !== dirname(currentDir)) {
    for (const marker of ROOT_MARKERS) {
      if (existsSync(join(currentDir, marker))) {
        return currentDir;
      }
    }
    const pkgPath = join(currentDir, 'package.json');
    if (existsSync(pkgPath)) {
      try {
        const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));
        if (pkg.workspaces) {
          return currentDir;
        }
      } catch {}
    }
    currentDir = dirname(currentDir);
  }
  return process.cwd();
}

export { GracefulShutdown, setupGracefulShutdown, createProductionSetup } from './shutdown';
export type { GracefulShutdownConfig } from '../types';