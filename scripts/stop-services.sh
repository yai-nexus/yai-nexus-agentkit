#!/bin/bash

# Stop Services Script
# 停止长期服务：Next.js 应用 + Python 后端

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}🛑 停止长期服务...${NC}"

# 停止服务相关进程
echo -e "${YELLOW}📋 查找并停止服务...${NC}"

# 停止服务相关的进程
pkill -f "dev:example:next" 2>/dev/null && echo "  ✅ 停止 Next.js 应用" || echo "  ℹ️  Next.js 应用未运行"
pkill -f "dev:example:python" 2>/dev/null && echo "  ✅ 停止 Python 后端" || echo "  ℹ️  Python 后端未运行"

# 停止 nx serve 进程
pkill -f "nx serve" 2>/dev/null && echo "  ✅ 停止 Nx 服务" || echo "  ℹ️  Nx 服务未运行"

# 停止可能的端口占用进程
lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 释放端口 3000" || echo "  ℹ️  端口 3000 未占用"
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 释放端口 8000" || echo "  ℹ️  端口 8000 未占用"

# 等待进程完全停止
sleep 2

echo -e "${GREEN}✨ 所有服务已停止！${NC}"

# 显示清理后的服务状态
echo -e "\n${YELLOW}📊 当前服务进程:${NC}"
SERVICE_PROCESSES=$(ps aux | grep -E "(dev:example:next|dev:example:python|nx serve)" | grep -v grep)
if [ -z "$SERVICE_PROCESSES" ]; then
    echo "  ✅ 无服务进程运行"
else
    echo "  ⚠️  仍有进程运行:"
    echo "$SERVICE_PROCESSES"
fi

# 显示端口占用情况
echo -e "\n${YELLOW}📊 端口占用情况:${NC}"
PORT_3000=$(lsof -ti:3000 2>/dev/null)
PORT_8000=$(lsof -ti:8000 2>/dev/null)

if [ -z "$PORT_3000" ]; then
    echo "  ✅ 端口 3000 已释放"
else
    echo "  ⚠️  端口 3000 仍被占用 (PID: $PORT_3000)"
fi

if [ -z "$PORT_8000" ]; then
    echo "  ✅ 端口 8000 已释放"
else
    echo "  ⚠️  端口 8000 仍被占用 (PID: $PORT_8000)"
fi