#!/bin/bash

# Stop All Examples Script
# 一键停止所有示例应用

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}🛑 停止所有示例应用...${NC}"

# 停止相关进程
echo -e "${YELLOW}📋 查找并停止进程...${NC}"

# 停止 pnpm 相关的开发进程
pkill -f "dev:example:next" 2>/dev/null && echo "  ✅ 停止 Next.js 应用" || echo "  ℹ️  Next.js 应用未运行"
pkill -f "dev:example:python" 2>/dev/null && echo "  ✅ 停止 Python 后端" || echo "  ℹ️  Python 后端未运行"
pkill -f "dev:example:sls-loguru" 2>/dev/null && echo "  ✅ 停止 SLS Loguru" || echo "  ℹ️  SLS Loguru 未运行"
pkill -f "dev:example:sls-pino" 2>/dev/null && echo "  ✅ 停止 SLS Pino" || echo "  ℹ️  SLS Pino 未运行"

# 停止 nx serve 进程
pkill -f "nx serve" 2>/dev/null && echo "  ✅ 停止 Nx 服务" || echo "  ℹ️  Nx 服务未运行"

# 停止可能的端口占用进程
lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 释放端口 3000" || echo "  ℹ️  端口 3000 未占用"

# 等待进程完全停止
sleep 2

echo -e "${GREEN}✨ 所有示例应用已停止！${NC}"

# 显示清理后的进程状态
echo -e "\n${YELLOW}📊 当前相关进程:${NC}"
ps aux | grep -E "(dev:example|nx serve)" | grep -v grep || echo "  ✅ 无相关进程运行"