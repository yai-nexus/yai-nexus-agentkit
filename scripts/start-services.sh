#!/bin/bash

# Start Services Script
# 启动长期服务：Next.js 应用 + Python 后端

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}🚀 启动长期服务...${NC}"
echo "项目根目录: $PROJECT_ROOT"

# 确保在项目根目录执行
cd "$PROJECT_ROOT"

# 创建日志目录
mkdir -p logs

# 停止可能已经运行的服务
echo -e "${YELLOW}📋 停止现有服务...${NC}"

# 停止服务相关的进程
pkill -f "dev:example:next" 2>/dev/null && echo "  ✅ 停止现有 Next.js 应用" || echo "  ℹ️  Next.js 应用未运行"
pkill -f "dev:example:python" 2>/dev/null && echo "  ✅ 停止现有 Python 后端" || echo "  ℹ️  Python 后端未运行"

# 停止 nx serve 进程
pkill -f "nx serve" 2>/dev/null && echo "  ✅ 停止现有 Nx 服务" || echo "  ℹ️  Nx 服务未运行"

# 释放可能被占用的端口
lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 释放端口 3000" || echo "  ℹ️  端口 3000 未占用"
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 释放端口 8000" || echo "  ℹ️  端口 8000 未占用"

# 等待进程完全停止
sleep 3

# 启动服务
echo -e "${GREEN}🔥 启动服务...${NC}"

echo "  📱 启动 Next.js 应用..."
nohup pnpm dev:example:next > logs/nextjs-service.log 2>&1 &
NEXTJS_PID=$!

echo "  🐍 启动 Python 后端..."
nohup pnpm dev:example:python > logs/python-service.log 2>&1 &
PYTHON_PID=$!

# 等待进程启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 5

# 检查进程状态
echo -e "${GREEN}📊 检查服务状态:${NC}"

check_service() {
    local pid=$1
    local name=$2
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "  ✅ $name (PID: $pid)"
        return 0
    else
        echo -e "  ❌ $name 启动失败"
        return 1
    fi
}

SERVICE_STATUS=0
check_service $NEXTJS_PID "Next.js 应用" || SERVICE_STATUS=1
check_service $PYTHON_PID "Python 后端" || SERVICE_STATUS=1

# 显示访问信息
echo -e "\n${GREEN}🌐 服务访问地址:${NC}"
echo "  📱 Next.js 应用: http://localhost:3000"
echo "  🐍 Python 后端: http://localhost:8000 (FastAPI)"

# 显示日志监控命令
echo -e "\n${YELLOW}📋 实用命令:${NC}"
echo "  查看 Next.js 日志: tail -f logs/nextjs-service.log"
echo "  查看 Python 日志: tail -f logs/python-service.log"
echo "  查看所有日志: tail -f logs/*-service.log"
echo "  停止所有服务: ./scripts/stop-services.sh"

if [ $SERVICE_STATUS -eq 0 ]; then
    echo -e "\n${GREEN}✨ 所有服务已成功启动！${NC}"
else
    echo -e "\n${RED}⚠️  部分服务启动失败，请检查日志${NC}"
    exit 1
fi