#!/bin/bash

# Stop Next.js Service Script
# 单独停止 Next.js 应用

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}🛑 停止 Next.js 应用...${NC}"

# 停止 Next.js 相关进程
echo -e "${YELLOW}📋 查找并停止 Next.js 服务...${NC}"

# 停止 Next.js 相关的进程
pkill -f "dev:example:next" 2>/dev/null && echo "  ✅ 停止 Next.js 应用" || echo "  ℹ️  Next.js 应用未运行"

# 停止可能的端口占用进程
lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 释放端口 3000" || echo "  ℹ️  端口 3000 未占用"

# 等待进程完全停止
sleep 2

echo -e "${GREEN}✨ Next.js 应用已停止！${NC}"

# 显示清理后的服务状态
echo -e "\n${YELLOW}📊 当前 Next.js 进程:${NC}"
NEXTJS_PROCESSES=$(ps aux | grep -E "dev:example:next" | grep -v grep)
if [ -z "$NEXTJS_PROCESSES" ]; then
    echo "  ✅ 无 Next.js 进程运行"
else
    echo "  ⚠️  仍有 Next.js 进程运行:"
    echo "$NEXTJS_PROCESSES"
fi

# 显示端口占用情况
echo -e "\n${YELLOW}📊 端口 3000 占用情况:${NC}"
PORT_3000=$(lsof -ti:3000 2>/dev/null)

if [ -z "$PORT_3000" ]; then
    echo "  ✅ 端口 3000 已释放"
else
    echo "  ⚠️  端口 3000 仍被占用 (PID: $PORT_3000)"
fi
