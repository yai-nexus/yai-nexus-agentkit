#!/bin/bash

# Start All Examples Script
# 一键后台启动所有示例应用

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}🚀 启动所有示例应用...${NC}"
echo "项目根目录: $PROJECT_ROOT"

# 确保在项目根目录执行
cd "$PROJECT_ROOT"

# 创建日志目录
mkdir -p logs

# 停止可能已经运行的进程
echo -e "${YELLOW}📋 停止现有进程...${NC}"

# 停止 pnpm 相关的开发进程
pkill -f "dev:example:next" 2>/dev/null && echo "  ✅ 停止现有 Next.js 应用" || echo "  ℹ️  Next.js 应用未运行"
pkill -f "dev:example:python" 2>/dev/null && echo "  ✅ 停止现有 Python 后端" || echo "  ℹ️  Python 后端未运行"
pkill -f "dev:example:sls-loguru" 2>/dev/null && echo "  ✅ 停止现有 SLS Loguru" || echo "  ℹ️  SLS Loguru 未运行"
pkill -f "dev:example:sls-pino" 2>/dev/null && echo "  ✅ 停止现有 SLS Pino" || echo "  ℹ️  SLS Pino 未运行"

# 停止 nx serve 进程
pkill -f "nx serve" 2>/dev/null && echo "  ✅ 停止现有 Nx 服务" || echo "  ℹ️  Nx 服务未运行"

# 释放可能被占用的端口
lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 释放端口 3000" || echo "  ℹ️  端口 3000 未占用"
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 释放端口 8000" || echo "  ℹ️  端口 8000 未占用"

# 等待进程完全停止
sleep 3

# 启动所有示例
echo -e "${GREEN}🔥 启动示例应用...${NC}"

echo "  📱 启动 Next.js 应用..."
nohup pnpm dev:example:next > logs/nextjs-bg.log 2>&1 &
NEXTJS_PID=$!

echo "  🐍 启动 Python 后端..."
nohup pnpm dev:example:python > logs/python-bg.log 2>&1 &
PYTHON_PID=$!

echo "  📝 启动 SLS Loguru 示例..."
nohup pnpm dev:example:sls-loguru > logs/sls-loguru-bg.log 2>&1 &
LOGURU_PID=$!

echo "  📋 启动 SLS Pino 示例..."
nohup pnpm dev:example:sls-pino > logs/sls-pino-bg.log 2>&1 &
PINO_PID=$!

# 等待进程启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 5

# 检查进程状态
echo -e "${GREEN}📊 检查服务状态:${NC}"

check_process() {
    local pid=$1
    local name=$2
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "  ✅ $name (PID: $pid)"
    else
        echo -e "  ❌ $name 启动失败"
    fi
}

check_process $NEXTJS_PID "Next.js 应用"
check_process $PYTHON_PID "Python 后端"
check_process $LOGURU_PID "SLS Loguru"
check_process $PINO_PID "SLS Pino"

# 显示访问信息
echo -e "\n${GREEN}🌐 访问地址:${NC}"
echo "  📱 Next.js 应用: http://localhost:3000"
echo "  🐍 Python 后端: 已启动 (查看 logs/python-bg.log)"
echo "  📝 日志示例: 已运行 (查看 logs/ 目录)"

# 显示日志监控命令
echo -e "\n${YELLOW}📋 实用命令:${NC}"
echo "  查看所有日志: tail -f logs/*-bg.log"
echo "  查看 Next.js 日志: tail -f logs/nextjs-bg.log"
echo "  查看 Python 日志: tail -f logs/python-bg.log"
echo "  停止所有服务: ./scripts/stop-all-examples.sh"

echo -e "\n${GREEN}✨ 所有示例应用已启动完成！${NC}"