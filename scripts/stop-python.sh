#!/bin/bash

# Stop Python Backend Service Script
# 单独停止 Python 后端

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}🛑 停止 Python 后端...${NC}"

# 停止 Python 相关进程
echo -e "${YELLOW}📋 查找并停止 Python 服务...${NC}"

# 停止 Python 相关的进程
pkill -f "dev:example:python" 2>/dev/null && echo "  ✅ 停止 Python 后端" || echo "  ℹ️  Python 后端未运行"

# 停止可能的端口占用进程
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 释放端口 8000" || echo "  ℹ️  端口 8000 未占用"

# 等待进程完全停止
sleep 2

echo -e "${GREEN}✨ Python 后端已停止！${NC}"

# 显示清理后的服务状态
echo -e "\n${YELLOW}📊 当前 Python 进程:${NC}"
PYTHON_PROCESSES=$(ps aux | grep -E "dev:example:python" | grep -v grep)
if [ -z "$PYTHON_PROCESSES" ]; then
    echo "  ✅ 无 Python 进程运行"
else
    echo "  ⚠️  仍有 Python 进程运行:"
    echo "$PYTHON_PROCESSES"
fi

# 显示端口占用情况
echo -e "\n${YELLOW}📊 端口 8000 占用情况:${NC}"
PORT_8000=$(lsof -ti:8000 2>/dev/null)

if [ -z "$PORT_8000" ]; then
    echo "  ✅ 端口 8000 已释放"
else
    echo "  ⚠️  端口 8000 仍被占用 (PID: $PORT_8000)"
fi
